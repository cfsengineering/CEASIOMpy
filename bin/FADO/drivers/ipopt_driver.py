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
import ipyopt as opt
from .constrained_optim_driver import ConstrainedOptimizationDriver


class IpoptDriver(ConstrainedOptimizationDriver):
    """
    Driver to use with the Ipopt optimizer via IPyOpt.
    """
    def __init__(self):
        ConstrainedOptimizationDriver.__init__(self)

        # sparse indices of the constraint gradient, for now assumed to be dense
        self._sparseIndices = None

        # the optimization problem
        self._nlp = None
    #end

    def getNLP(self):
        """
        Prepares and returns the optimization problem for Ipopt (an instance of ipyopt.Problem).
        For convenience also does other preprocessing, must be called after all functions are set.
        Do not destroy the driver after obtaining the problem.
        """
        ConstrainedOptimizationDriver.preprocess(self)

        conLowerBound = np.zeros([self._nCon,])
        conUpperBound = np.zeros([self._nCon,])

        i = len(self._constraintsEQ)
        conUpperBound[i:(i+len(self._constraintsGT))] = 1e20

        # assume row major storage for gradient sparsity
        rg = range(self._nVar * self._nCon)
        self._sparseIndices = (np.array([i // self._nVar for i in rg], dtype=int),
                               np.array([i % self._nVar for i in rg], dtype=int))

        # create the optimization problem
        self._nlp = opt.Problem(self._nVar, self.getLowerBound(), self.getUpperBound(),
                                self._nCon, conLowerBound, conUpperBound, self._sparseIndices, 0,
                                self._eval_f, self._eval_grad_f, self._eval_g, self._eval_jac_g)
        return self._nlp
    #end

    # Method passed to Ipopt to get the objective value,
    # evaluates all functions if necessary.
    def _eval_f(self, x):
        self._evaluateFunctions(x)
        return self._ofval.sum()
    #end

    # Method passed to Ipopt to get the objective gradient, evaluates gradients and
    # functions if necessary, otherwise it simply combines and scales the results.
    def _eval_grad_f(self, x, out):
        assert out.size >= self._nVar, "Wrong size of gradient vector (\"out\")."

        self._jacTime -= time.time()
        try:
            self._evaluateGradients(x)

            os.chdir(self._workDir)

            out[()] = 0.0
            for obj in self._objectives:
                out += obj.function.getGradient(self._variableStartMask) * obj.scale
            out /= self._varScales

            # keep reference to result to use as fallback on next iteration if needed
            self._old_grad_f = out
        except:
            if self._failureMode == "HARD": raise
            if self._old_grad_f is None: out[()] = 0.0
            else: out[()] = self._old_grad_f
        #end

        if not self._parallelEval:
            self._runAction(self._userPostProcessGrad)

        self._jacTime += time.time()
        os.chdir(self._userDir)

        return out
    #end

    # Method passed to Ipopt to expose the constraint vector, see also "_eval_f"
    def _eval_g(self, x, out):
        assert out.size >= self._nCon, "Wrong size of constraint vector (\"out\")."

        self._evaluateFunctions(x)

        i = 0
        out[i:(i+len(self._constraintsEQ))] = self._eqval

        i += len(self._constraintsEQ)
        out[i:(i+len(self._constraintsGT))] = self._gtval

        return out
    #end

    # Method passed to Ipopt to expose the constraint Jacobian, see also "_eval_grad_f".
    def _eval_jac_g(self, x, out):
        assert out.size >= self._nCon*self._nVar, "Wrong size of constraint Jacobian vector (\"out\")."

        self._jacTime -= time.time()
        try:
            self._evaluateGradients(x)

            os.chdir(self._workDir)

            i = 0
            mask = self._variableStartMask

            for con in self._constraintsEQ:
                out[i:(i+self._nVar)] = con.function.getGradient(mask) * con.scale / self._varScales
                i += self._nVar
            #end
            for (con,f) in zip(self._constraintsGT, self._gtval):
                if f < 0.0 or not self._asNeeded:
                    out[i:(i+self._nVar)] = con.function.getGradient(mask) * con.scale / self._varScales
                else:
                    out[i:(i+self._nVar)] = 0.0
                #end
                i += self._nVar
            #end

            # keep reference to result to use as fallback on next iteration if needed
            self._old_jac_g = out
        except:
            if self._failureMode == "HARD": raise
            if self._old_jac_g is None: out[()] = 0.0
            else: out[()] = self._old_jac_g
        #end

        if not self._parallelEval:
            self._runAction(self._userPostProcessGrad)

        self._jacTime += time.time()
        os.chdir(self._userDir)

        return out
    #end
#end

