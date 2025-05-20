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
import numpy as np
from .constrained_optim_driver import ConstrainedOptimizationDriver


class ScipyDriver(ConstrainedOptimizationDriver):
    """
    Driver to use with the SciPy optimizers, especially the constrained ones.
    """
    def __init__(self):
        ConstrainedOptimizationDriver.__init__(self)
    #end

    def preprocess(self):
        """
        Prepares the optimization problem, including preprocessing variables,
        and setting up the lists of constraints and variable bounds that SciPy
        needs. Must be called after all functions are added to the driver.
        """
        ConstrainedOptimizationDriver.preprocess(self)

        class _fun:
            def __init__(self,fun,idx):
                self._f = fun
                self._i = idx
            def __call__(self,x):
                return self._f(x,self._i)
        #end

        # setup the constraint list, the callbacks are the same for all
        # constraints, an index argument (i) is used to distinguish them.
        self._constraints = []
        for i in range(self._nCon):
            self._constraints.append({'type' : ('ineq','eq')[i<len(self._constraintsEQ)],
                                      'fun' : _fun(self._eval_g,i),
                                      'jac' : _fun(self._eval_jac_g,i)})
        #end

        # variable bounds
        self._bounds = np.array((self.getLowerBound(),self.getUpperBound()),float).transpose()

        # size the gradient and constraint jacobian
        self._grad_f = np.zeros((self._nVar,))
        self._old_grad_f = np.zeros((self._nVar,))
        self._jac_g = np.zeros((self._nVar,self._nCon))
        self._old_jac_g = np.zeros((self._nVar,self._nCon))
    #end

    def getConstraints(self):
        """Returns the constraint list that can be passed to SciPy."""
        return self._constraints

    def getBounds(self):
        """Return the variable bounds in a format compatible with SciPy."""
        return self._bounds

    def fun(self, x):
        """Method passed to SciPy to get the objective function value."""
        # Evaluates all functions if necessary.
        self._evaluateFunctions(x)
        return self._ofval.sum()
    #end

    def grad(self, x):
        """Method passed to SciPy to get the objective function gradient."""
        # Evaluates gradients and functions if necessary, otherwise it
        # simply combines and scales the results.
        self._jacTime -= time.time()
        try:
            self._evaluateGradients(x)

            os.chdir(self._workDir)

            self._grad_f[()] = 0.0
            for obj in self._objectives:
                self._grad_f += obj.function.getGradient(self._variableStartMask) * obj.scale
            self._grad_f /= self._varScales

            # keep copy of result to use as fallback on next iteration if needed
            self._old_grad_f[()] = self._grad_f
        except:
            if self._failureMode == "HARD": raise
            self._grad_f[()] = self._old_grad_f
        #end

        if not self._parallelEval:
            self._runAction(self._userPostProcessGrad)

        self._jacTime += time.time()
        os.chdir(self._userDir)

        return self._grad_f
    #end

    # Method passed to SciPy to expose the constraint vector.
    def _eval_g(self, x, idx):
        self._evaluateFunctions(x)

        if idx < len(self._constraintsEQ):
            out = self._eqval[idx]
        else:
            out = self._gtval[idx-len(self._constraintsEQ)]
        #end

        return out
    #end

    # Method passed to SciPy to expose the constraint Jacobian.
    def _eval_jac_g(self, x, idx):
        self._jacTime -= time.time()
        try:
            self._evaluateGradients(x)

            os.chdir(self._workDir)

            mask = self._variableStartMask

            if idx < len(self._constraintsEQ):
                con = self._constraintsEQ[idx]
                f = -1.0 # for purposes of lazy evaluation equality is always active
            else:
                con = self._constraintsGT[idx-len(self._constraintsEQ)]
                f = self._gtval[idx-len(self._constraintsEQ)]
            #end

            if f < 0.0 or not self._asNeeded:
                self._jac_g[:,idx] = con.function.getGradient(mask) * con.scale / self._varScales
            else:
                self._jac_g[:,idx] = 0.0
            #end

            # keep reference to result to use as fallback on next iteration if needed
            self._old_jac_g[:,idx] = self._jac_g[:,idx]
        except:
            if self._failureMode == "HARD": raise
            self._jac_g[:,idx] = self._old_jac_g[:,idx]
        #end

        if not self._parallelEval:
            self._runAction(self._userPostProcessGrad)

        self._jacTime += time.time()
        os.chdir(self._userDir)

        return self._jac_g[:,idx]
    #end
#end

