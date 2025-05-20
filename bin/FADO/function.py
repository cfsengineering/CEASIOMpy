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

import numpy as np
import abc


class FunctionBase(abc.ABC):
    """Abstract base class to define the essential interface of Function objects."""
    def __init__(self,name):
        self._name = name
        # inputs
        self._variables = []

    def getName(self,maxLen=0):
        name = self._name
        if maxLen==0: return name
        if maxLen<len(name): name = name[:maxLen]
        return name

    def getVariables(self):
        return self._variables

    @abc.abstractmethod
    def getValue(self):
        return NotImplemented

    @abc.abstractmethod
    def getGradient(self,mask):
        return NotImplemented

    def getParameters(self):
        return []

    def resetValueEvalChain(self):
        pass

    def resetGradientEvalChain(self):
        pass

    def getValueEvalChain(self):
        return []

    def getGradientEvalChain(self):
        return []
#end


class Function(FunctionBase):
    """
    Defines a mathematical function R^n -> R as a series of evaluation steps.
    Functions are associated with optimization drivers to define optimization problems,
    they are not designed (nor intended) to be passed directly to optimization methods.

    Parameters
    ----------
    name      : String to identify the function.
    outFile   : Where to read the result from.
    outParser : Object used to read the outFile.

    See also
    --------
    ExternalRun, currently the only way to define the evaluation steps.
    Variable, the class used to define optimization variables.
    """
    def __init__(self,name="",outFile="",outParser=None):
        FunctionBase.__init__(self,name)

        # where and how the output value is obtained
        self.setOutput(outFile,outParser)

        # evaluation pipelines for value and gradient
        self._funEval = []
        self._gradEval = []

        # where and how their gradients are obtained
        self._gradFiles = []
        self._gradParse = []

        # default value when evaluation fails
        self._defaultValue = None

    def addInputVariable(self,variable,gradFile,gradParser):
        """
        Attach a variable object to the function.

        Parameters
        ----------
        variable    : The variable object.
        gradFile    : Where to get the gradient of the function w.r.t. the variable.
        gradParser  : The object used to read the gradFile.
        """
        self._variables.append(variable)
        self._gradFiles.append(gradFile)
        self._gradParse.append(gradParser)

    def getParameters(self):
        parameters = []
        for evl in self._funEval:
            parameters += evl.getParameters()
        for evl in self._gradEval:
            parameters += evl.getParameters()
        return parameters

    def setOutput(self,file,parser):
        self._outFile = file
        self._outParser = parser

    def addValueEvalStep(self,evaluation):
        """Add a required step to compute the function value."""
        self._funEval.append(evaluation)

    def addGradientEvalStep(self,evaluation):
        """Add a required step to compute the function gradient."""
        self._gradEval.append(evaluation)

    # check if any evaluation is in error state
    def _checkError(self,evals):
        for evl in evals:
            if evl.isError(): raise RuntimeError("Evaluations failed.")
        #end
    #end

    def getValue(self):
        """
        Get the function value, i.e. apply the parser to the output file.
        Run the evaluation steps if they have not been executed yet.
        Note that this method does not have parameters, the current value of the variables
        is set via the Variable objects.
        """
        # check if we can retrive the value
        self._checkError(self._funEval)

        for evl in self._funEval:
            if not evl.isRun():
                self._sequentialEval(self._funEval)
                break
        #end
        return self._outParser.read(self._outFile)

    def getGradient(self,mask=None):
        """
        Get the gradient (as a dense vector) of the function, i.e. applies each variable's
        parser. If no mask (dictionary) is provided simple concatenation is performed,
        otherwise each variable's gradient is copied starting at an offset. Note that if a
        mask is provided the size of the resulting vector is the sum of the sizes of the
        variables used as keys for the dictionary.

        Example
        -------
        addVariable(z,...) # z = [1, 1] and df/dz = [2, 2]
        getGradient({x : 0, z : 3}) -> [0, 0, 0, 2, 2]
        """
        # check if we can retrive the gradient
        self._checkError(self._gradEval)

        for evl in self._gradEval:
            if not evl.isRun():
                self._sequentialEval(self._gradEval)
                break
        #end

        # determine size of gradient vector
        size = 0
        if mask is None: src = self._variables
        else:            src = mask.keys()
        for var in src:
            size += var.getSize()

        # populate gradient vector
        gradient = np.ndarray((size,))
        idx = 0
        for var,file,parser in zip(self._variables,self._gradFiles,self._gradParse):
            grad = parser.read(file)
            if var.getSize() == 1:
                # Convert the value to a scalar if it is not yet.
                try: grad = sum(grad)
                except: pass
            #end
            if mask is not None: idx = mask[var]
            try:
                for val in grad:
                    gradient[idx] = val
                    idx += 1
            except:
                gradient[idx] = grad
                idx += 1
            #end
        #end

        return gradient
    #end

    def _sequentialEval(self,evals):
        for evl in evals:
            evl.initialize()
            evl.run()
        #end
    #end

    def resetValueEvalChain(self):
        self._resetEvals(self._funEval)

    def resetGradientEvalChain(self):
        self._resetEvals(self._gradEval)

    def _resetEvals(self,evals):
        for evl in evals:
            evl.finalize()
        #end
    #end

    def getValueEvalChain(self):
        return self._funEval

    def getGradientEvalChain(self):
        return self._gradEval

    def hasDefaultValue(self):
        return self._defaultValue is not None

    def setDefaultValue(self,value):
        """Give a default value to the function, to be used in case the evaluation fails."""
        self._defaultValue = value

    def getDefaultValue(self):
        return self._defaultValue
#end


class NonDiscreteness(FunctionBase):
    """
    Continuous measure of non-discreteness (usually to use as a constraint).
    The function is zero when the variables are at either bound (lower or upper)
    and 1 (maximum) when they are at the mid-point.
    """
    def __init__(self,name=""):
        FunctionBase.__init__(self,name)

    def addInputVariable(self,variable):
        self._variables.append(variable)

    def getValue(self):
        y = 0.0
        N = 0
        for var in self._variables:
            N += var.getSize()
            x  = var.getCurrent()
            lb = var.getLowerBound()
            ub = var.getUpperBound()
            y += ((ub-x)*(x-lb)/(ub+lb)**2).sum()
        return 4*y/N

    def getGradient(self,mask=None):
        # determine size of gradient vector
        N = 0
        for var in self._variables:
            N += var.getSize()

        size = 0
        if mask is None:
            size = N
        else:
            for var in mask.keys():
                size += var.getSize()

        # populate gradient vector
        gradient = np.ndarray((size,))
        idx = 0
        for var in self._variables:
            x  = var.getCurrent()
            lb = var.getLowerBound()
            ub = var.getUpperBound()
            grad = (4.0/N)*(ub+lb-2*x)/(ub+lb)**2

            if mask is not None: idx = mask[var]

            try:
                for val in grad:
                    gradient[idx] = val
                    idx += 1
            except:
                gradient[idx] = grad
                idx += 1
            #end
        #end

        return gradient
    #end
#end

