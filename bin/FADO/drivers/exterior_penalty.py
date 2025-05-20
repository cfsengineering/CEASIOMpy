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
import time
import copy
import numpy as np
from .parallel_eval_driver import ParallelEvalDriver


class ExteriorPenaltyDriver(ParallelEvalDriver):
    """
    Exterior Penalty method wrapper, exposes a penalized function and its gradient
    to an optimizer via methods fun(x) and grad(x).
    Implements the logic to ramp up/down the penalty factors for each constraint.

    Parameters
    ----------
    tol         : Constraint violation tolerance.
    freq        : Frequency for auto updating the penalty factors, 0 disables auto update.
    rini        : Initial penalty factor.
    rmax        : Maximum penalty factor.
    factorUp    : Multiplicative increase rate for penalties of constraints out of tolerance.
    factorDown  : Multiplicative decrease rate for penalties of inactive constraints.
    """
    def __init__(self, tol, freq=40, rini=8, rmax=1024, factorUp=4, factorDown=0.5):
        ParallelEvalDriver.__init__(self, True)

        # parameters of the method
        self._tol = tol
        self._freq = freq
        self._rini = rini
        self._rmax = rmax
        self._cup = factorUp
        self._cdown = factorDown

        # constraint penalties
        self._eqpen = None
        self._gtpen = None

        # gradient vector
        self._grad = None
        self._old_grad = None

        # timers, counters, flags
        self._isInit = False
        self._isFeasible = False
        self._logRowFormat = ""
    #end

    def preprocessVariables(self):
        """Setup method that must be called after all functions are added to the driver."""
        self._preprocessVariables()

    def preprocess(self):
        """Alias for preprocessVariables."""
        self._preprocessVariables()

    # method for lazy initialization
    def _initialize(self):
        if self._isInit: return

        self._ofval = np.zeros((len(self._objectives),))
        self._eqval = np.zeros((len(self._constraintsEQ),))
        self._gtval = np.zeros((len(self._constraintsGT),))
        self._monval = np.zeros((len(self._monitors),))

        self._eqpen = np.ones((len(self._constraintsEQ),))*self._rini
        self._gtpen = np.ones((len(self._constraintsGT),))*self._rini

        self._grad = np.zeros((self.getNumVariables(),))
        self._old_grad = copy.deepcopy(self._grad)

        # write the header for the log file and set the format
        if self._logObj is not None:
            w = self._logColWidth
            headerData = ["FUN EVAL","FUN TIME","GRAD EVAL","GRAD TIME","FEASIBLE"]
            self._logRowFormat = "{:>W}"+"{:>W.3e}{:>W}"*2
            for obj in self._objectives:
                headerData.append(obj.function.getName(w-1))
                self._logRowFormat += "{:>W.Pg}"
            for obj in self._constraintsEQ:
                headerData.append(obj.function.getName(w-1))
                headerData.append("PEN COEFF")
                self._logRowFormat += "{:>W.Pg}"*2
            for obj in self._constraintsGT:
                headerData.append(obj.function.getName(w-1))
                headerData.append("PEN COEFF")
                self._logRowFormat += "{:>W.Pg}"*2
            for obj in self._monitors:
                headerData.append(obj.function.getName(w-1))
                self._logRowFormat += "{:>W.Pg}"
            # right-align, set width in format and a precision that fits it
            self._logRowFormat = self._logRowFormat.replace("W",str(w))+"\n"
            self._logRowFormat = self._logRowFormat.replace("P",str(min(8,w-7)))
            header = ""
            for data in headerData:
                header += data.rjust(w)
            self._logObj.write(header+"\n")
        #end

        # write the header for the history file
        if self._hisObj is not None:
            header = "ITER"+self._hisDelim
            for obj in self._objectives:
                header += obj.function.getName()+self._hisDelim
            for obj in self._constraintsEQ:
                header += obj.function.getName()+self._hisDelim
            for obj in self._constraintsGT:
                header += obj.function.getName()+self._hisDelim
            for obj in self._monitors:
                header += obj.function.getName()+self._hisDelim
            header = header.strip(self._hisDelim)+"\n"
            self._hisObj.write(header)
        #end

        self._isInit = True
    #end

    def _writeLogLine(self):
        if self._logObj is None: return
        data = [self._funEval, self._funTime, self._jacEval, self._jacTime]
        data.append(("NO","YES")[self._isFeasible])
        for f in self._ofval:
            data.append(f)
        for (g,r) in zip(self._eqval,self._eqpen):
            data.append(g)
            data.append(r)
        for (g,r) in zip(self._gtval,self._gtpen):
            data.append(g)
            data.append(r)
        for f in self._monval:
            data.append(f)
        self._logObj.write(self._logRowFormat.format(*data))
    #end

    def fun(self,x):
        """Evaluate the penalized function at "x"."""
        self._initialize()
        self._evaluateFunctions(x)

        # combine results
        f  = self._ofval.sum()
        f += (self._eqpen*self._eqval**2).sum()
        for (g,r) in zip(self._gtval,self._gtpen): f += r*min(0.0,g)*g

        return f
    #end

    def grad(self,x):
        """Evaluate the gradient of the penalized function at "x"."""
        try:
            self._evaluateGradients(x)
            return self._grad
        except:
            if self._failureMode == "HARD": raise
            return self._old_grad
        #end
    #end

    # this method decorates the parent method by combining the gradient
    def _evaluateGradients(self,x):
        self._initialize()

        # if nothing is evaluated return without doing more work
        if not ParallelEvalDriver._evaluateGradients(self,x): return

        # evaluate all required gradients (skip those where the constraint is not active)
        self._jacTime -= time.time()
        os.chdir(self._workDir)

        self._grad[()] = 0.0

        for obj in self._objectives:
            self._grad += obj.function.getGradient(self._variableStartMask)*obj.scale

        for (obj,f,r) in zip(self._constraintsEQ,self._eqval,self._eqpen):
            self._grad += 2.0*r*f*obj.function.getGradient(self._variableStartMask)*obj.scale

        for (obj,f,r) in zip(self._constraintsGT,self._gtval,self._gtpen):
            if f < 0.0:
                self._grad += 2.0*r*f*obj.function.getGradient(self._variableStartMask)*obj.scale

        self._grad /= self._varScales

        if not self._parallelEval:
            self._runAction(self._userPostProcessGrad)

        self._jacTime += time.time()
        os.chdir(self._userDir)

        # update penalties and params (evaluating the gradient concludes an outer iteration)
        if self._freq > 0:
            if self._jacEval % self._freq == 0: self.update()

        # make copy to use as fallback
        self._old_grad[()] = self._grad
    #end

    def update(self,paramsIfFeasible=False):
        """
        If a constraint is active and above tolerance increase the penalties, otherwise decrease them
        (minimum and maximum are constrained).
        Increment all Parameters associated with the Functions of the problem (via the evaluation steps).
        If paramsIfFeasible=True the Parameter update only takes place if the current design is feasible.
        """
        self._isFeasible = True

        # equality (always active)
        for i in range(self._eqpen.size):
            if abs(self._eqval[i]) > self._tol:
                self._eqpen[i] = min(self._eqpen[i]*self._cup,self._rmax)
                self._isFeasible = False

        # lower bound
        for i in range(self._gtpen.size):
            if self._gtval[i] < -self._tol:
                self._gtpen[i] = min(self._gtpen[i]*self._cup,self._rmax)
                self._isFeasible = False
            elif self._gtval[i] > 0.0:
                self._gtpen[i] = max(self._gtpen[i]*self._cdown,self._rini)

        # update the values of the parameters
        if not paramsIfFeasible or self._isFeasible:
            for par in self._parameters:
                par.increment()

        # trigger new evaluations
        self._x[()] = 1e20
        self._funReady = False
        self._jacReady = False
        self._resetAllValueEvaluations()
        self._resetAllGradientEvaluations()

        # log update
        self._writeLogLine()
    #end

    def feasibleDesign(self):
        """Return True if all constraints meet the tolerance."""
        return self._isFeasible
#end

