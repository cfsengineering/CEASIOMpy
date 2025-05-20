#  Copyright 2019-2025, FADO Contributors (cf. AUTHORS.md)
#
#  This file is part of FADO.
#
#  FADO is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  FADO is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with FADO.  If not, see <https://www.gnu.org/licenses/>.

import os
import shutil
import numpy as np


class DriverBase:
    """Base class for optimization drivers, implements the basic setup interface."""

    # "structs" to store objective and constraint information
    class _Objective:
        def __init__(self,type,function,scale,weight):
            if scale <= 0.0 or weight <= 0.0:
                raise ValueError("Scale and weight must be positive.")

            if type == "min":
                self.scale = scale*weight
            elif type == "max":
                self.scale = -1.0*scale*weight
            else:
                raise ValueError("Type must be 'min' or 'max'.")

            self.function = function
    #end

    class _Constraint:
        def __init__(self,function,scale,bound=-1E20):
            self.scale = scale
            self.bound = bound
            self.function = function
    #end

    class _Monitor:
        def __init__(self,function):
            self.function = function
    #end

    def __init__(self):
        self._variables = []
        self._varScales = None
        self._parameters = []

        # lazy evaluation flags, and current value of the variables
        self._funReady = False
        self._jacReady = False
        self._nVar = 0
        self._x = None

        # functions by role
        self._objectives = []
        self._constraintsEQ = []
        self._constraintsGT = []
        self._monitors = []

        # function values
        self._ofval = None
        self._eqval = None
        self._gtval = None
        self._monval = None

        # map the start index of each variable in the design vector
        self._variableStartMask = None

        self._userDir = ""
        self._workDir = "__WORKDIR__"
        self._dirPrefix = "DSN_"
        self._keepDesigns = True
        self._failureMode = "HARD"
        self._logObj = None
        self._logColWidth = 13
        self._hisObj = None
        self._hisDelim = ",  "

        self._userPreProcessFun = None
        self._userPreProcessGrad = None
        self._userPostProcessFun = None
        self._userPostProcessGrad = None
    #end

    def addObjective(self,type,function,scale=1.0,weight=1.0):
        """
        Add an objective function to the optimization problem.

        Parameters
        ----------
        type      : "min" or "max" for minimization or maximization.
        function  : A function object.
        scale     : Scale applied to the function, optimizer will see function*scale.
        weight    : Weight given to the objective, only relevant for multiple objectives.
        """
        self._objectives.append(self._Objective(type,function,scale,weight))

    def addEquality(self,function,target=0.0,scale=1.0):
        """
        Add an equality constraint, function = target, the optimizer will see (function-target)*scale.
        """
        if scale <= 0.0: raise ValueError("Scale must be positive.")
        self._constraintsEQ.append(self._Constraint(function,scale,target))

    def addLowerBound(self,function,bound=0.0,scale=1.0):
        """Add a lower bound inequality constraint."""
        if scale <= 0.0: raise ValueError("Scale must be positive.")
        self._constraintsGT.append(self._Constraint(function,scale,bound))

    def addUpperBound(self,function,bound=0.0,scale=1.0):
        """Add an upper bound inequality constraint."""
        if scale <= 0.0: raise ValueError("Scale must be positive.")
        self._constraintsGT.append(self._Constraint(function,-1*scale,bound))

    def addUpLowBound(self,function,lower=-1.0,upper=1.0):
        """Add a range constraint, this is converted into lower/upper bounds."""
        if lower >= upper: raise ValueError("Upper bound must be greater than lower bound.")
        scale = 1.0/(upper-lower)
        self._constraintsGT.append(self._Constraint(function,scale,lower))
        self._constraintsGT.append(self._Constraint(function,-1*scale,upper))

    def addMonitor(self,function):
        """Add a function to monitor its value, does not participate in the optimization."""
        self._monitors.append(self._Monitor(function))

    def setWorkingDirectory(self,dir):
        """Set the name of the working directory where each iteration runs, it should not exist."""
        self._workDir = dir

    def getNumVariables(self):
        """Returns the size of the design vector."""
        N=0
        for var in self._variables: N+=var.getSize()
        return N

    def setLogger(self,obj,width=13):
        """Attach a log file object to the driver."""
        self._logObj = obj
        self._logColWidth = width

    def setHistorian(self,obj,delim=",  "):
        """Attach a history file object to the driver, function values printed every iteration."""
        self._hisObj = obj
        self._hisDelim = delim

    # methods to retrieve information in a format that the optimizer understands
    def _getConcatenatedVector(self,name):
        x = np.ndarray((self.getNumVariables(),))
        idx = 0
        for var in self._variables:
            for val in var.get(name):
                x[idx] = val
                idx += 1
            #end
        #end
        return x
    #end

    def getInitial(self):
        """Returns the initial design vector."""
        return self._getConcatenatedVector("Initial")*self._varScales

    def getLowerBound(self):
        """Returns the lower bounds of the variables."""
        return self._getConcatenatedVector("LowerBound")*self._varScales

    def getUpperBound(self):
        """Returns the upper bounds of the variables."""
        return self._getConcatenatedVector("UpperBound")*self._varScales

    # update design variables with the design vector from the optimizer
    def _setCurrent(self,x):
        startIdx = 0
        for var in self._variables:
            endIdx = startIdx+var.getSize()
            var.setCurrent(x[startIdx:endIdx]/var.getScale())
            startIdx = endIdx
        #end
    #end

    def _getVarsAndParsFromFun(self,functions):
        for obj in functions:
            for var in obj.function.getVariables():
                if var not in self._variables: self._variables.append(var)
            for par in obj.function.getParameters():
                if par not in self._parameters: self._parameters.append(par)

            # inform evaluations about which variables they depend on
            for evl in obj.function.getValueEvalChain():
                evl.updateVariables(obj.function.getVariables())
            for evl in obj.function.getGradientEvalChain():
                evl.updateVariables(obj.function.getVariables())
        #end
    #end

    # build variable and parameter vectors from function data
    def _preprocessVariables(self):
        # build ordered non duplicated lists of variables and parameters
        self._variables = []
        self._parameters = []
        self._getVarsAndParsFromFun(self._objectives)
        self._getVarsAndParsFromFun(self._constraintsEQ)
        self._getVarsAndParsFromFun(self._constraintsGT)
        self._getVarsAndParsFromFun(self._monitors)

        # map the start index of each variable in the design vector
        idx = [0]
        for var in self._variables[0:-1]:
            idx.append(idx[-1]+var.getSize())
        self._variableStartMask = dict(zip(self._variables,idx))

        self._varScales = self._getConcatenatedVector("Scale")

        # initialize current values such that evaluations are triggered on first call
        self._nVar = self.getNumVariables()
        self._x = np.ones([self._nVar,])*1e20

        # store the absolute current path
        self._userDir = os.path.abspath(os.curdir)
    #end

    def setStorageMode(self,keepDesigns=False,dirPrefix="DSN_"):
        """
        Set whether to keep or discard (default) old optimization iterations.

        Parameters
        ----------
        keepDesigns : True to keep all designs.
        dirPrefix   : Prefix used to name folders with old designs.
        """
        self._keepDesigns = keepDesigns
        self._dirPrefix = dirPrefix

    def setFailureMode(self,mode):
        """
        Set the failure behavior, for "HARD" (default) an exception is throw if function evaluations fail,
        for "SOFT" the driver catches exceptions and uses default function values (if they have them).
        The "SOFT" mode is useful if the optimizer does not handle exceptions.
        """
        assert mode == "HARD" or mode == "SOFT", "Mode must be either \"HARD\" (exceptions) or \"SOFT\" (default function values)."
        self._failureMode = mode

    def setUserPreProcessFun(self,callableOrString):
        """Set a preprocessing action executed before evaluating function values."""
        self._userPreProcessFun = callableOrString

    def setUserPreProcessGrad(self,callableOrString):
        """Set a preprocessing action executed before evaluating function gradients."""
        self._userPreProcessGrad = callableOrString

    def setUserPostProcessFun(self,callableOrString):
        """Set a postprocessing action executed after evaluating function values."""
        self._userPostProcessFun = callableOrString

    def setUserPostProcessGrad(self,callableOrString):
        """Set a postprocessing action executed after evaluating function gradients."""
        self._userPostProcessGrad = callableOrString

    def _resetAllValueEvaluations(self):
        for obj in self._objectives:
            obj.function.resetValueEvalChain()
        for obj in self._constraintsEQ:
            obj.function.resetValueEvalChain()
        for obj in self._constraintsGT:
            obj.function.resetValueEvalChain()
        for obj in self._monitors:
            obj.function.resetValueEvalChain()
    #end

    def _resetAllGradientEvaluations(self):
        for obj in self._objectives:
            obj.function.resetGradientEvalChain()
        for obj in self._constraintsEQ:
            obj.function.resetGradientEvalChain()
        for obj in self._constraintsGT:
            obj.function.resetGradientEvalChain()
        for obj in self._monitors:
            obj.function.resetGradientEvalChain()
    #end

    # Writes a line to the history file.
    def _writeHisLine(self):
        if self._hisObj is None: return
        hisLine = str(self._funEval)+self._hisDelim
        for val in self._ofval:
            hisLine += str(val)+self._hisDelim
        for val in self._eqval:
            hisLine += str(val)+self._hisDelim
        for val in self._gtval:
            hisLine += str(val)+self._hisDelim
        for val in self._monval:
            hisLine += str(val)+self._hisDelim
        hisLine = hisLine.strip(self._hisDelim)+"\n"
        self._hisObj.write(hisLine)
    #end

    # Detect a change in the design vector, reset directories and evaluation state.
    def _handleVariableChange(self, x):
        assert x.size == self._nVar, "Wrong size of design vector."

        newValues = (abs(self._x-x) > np.finfo(float).eps).any()

        if not newValues: return False

        # otherwise...

        # update the values of the variables
        self._setCurrent(x)
        self._x[()] = x

        # trigger evaluations
        self._funReady = False
        self._jacReady = False
        self._resetAllValueEvaluations()
        self._resetAllGradientEvaluations()

        # manage working directories
        os.chdir(self._userDir)
        if os.path.isdir(self._workDir):
            if self._keepDesigns:
                dirName = self._dirPrefix+str(self._funEval).rjust(3,"0")
                if os.path.isdir(dirName): shutil.rmtree(dirName)
                os.rename(self._workDir,dirName)
            else:
                shutil.rmtree(self._workDir)
            #end
        #end
        os.mkdir(self._workDir)

        return True
    #end
#end

