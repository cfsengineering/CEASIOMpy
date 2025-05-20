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
from .parallel_eval_driver import ParallelEvalDriver


class ConstrainedOptimizationDriver(ParallelEvalDriver):
    """
    Intermediate class to define common methods between the other constrained optimization drivers.
    """
    def __init__(self):
        ParallelEvalDriver.__init__(self)

        # counters, flags, sizes...
        self._nCon = 0

        # list of constraints and variable bounds
        self._constraints = []
        self._bounds = []

        # Current and old values of the gradients, as fallback in case of evaluation failure
        self._grad_f = None
        self._old_grad_f = None
        self._jac_g = None
        self._old_jac_g = None
    #end

    def update(self):
        """Update the problem parameters (triggers new evaluations)."""
        for par in self._parameters: par.increment()

        self._x[()] = 1e20
        self._funReady = False
        self._jacReady = False
        self._resetAllValueEvaluations()
        self._resetAllGradientEvaluations()

        if self._hisObj is not None:
            self._hisObj.write("Parameter update.\n")
    #end

    def setConstraintGradientEvalMode(self, onlyWhenActive=False):
        """
        Set the evaluation mode for constraint gradients.
        If onlyWhenActive==True the driver will not evaluate the gradients of
        inactive constraints, this may be acceptable for some optimizers or if
        the gradients are known to be zero in the inactive region.
        """
        self._asNeeded = onlyWhenActive
    #end

    # Basic preparation of the optimization problem
    def preprocess(self):
        self._preprocessVariables()

        self._ofval = np.zeros((len(self._objectives),))
        self._eqval = np.zeros((len(self._constraintsEQ),))
        self._gtval = np.zeros((len(self._constraintsGT),))
        self._monval = np.zeros((len(self._monitors),))

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

        # store number of constraints
        self._nCon = len(self._constraintsEQ) + len(self._constraintsGT)
    #end
#end

