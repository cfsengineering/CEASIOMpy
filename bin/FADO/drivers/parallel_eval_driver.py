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
import subprocess as sp
from .base_driver import DriverBase


class ParallelEvalDriver(DriverBase):
    """
    Intermediate class that adds parallel evaluation capabilities to the base driver.
    In parallel mode, the evaluation steps of the functions are started asynchronously
    as soon as all their dependencies are met.

    Parameters
    ----------
    asNeeded: If True, the gradients of constraints are only evaluated if they are
              active, this is possible for the exterior penalty driver.
    """
    def __init__(self, asNeeded = False):
        DriverBase.__init__(self)

        # timers, counters, etc.
        self._funTime = 0
        self._jacTime = 0
        self._funEval = 0
        self._jacEval = 0

        # variables for parallelization of evaluations
        self._asNeeded = asNeeded
        self._parallelEval = False
        self._funEvalGraph = None
        self._jacEvalGraph = None
        self._waitTime = 10.0
    #end

    def setEvaluationMode(self,parallel=True,waitTime=10.0):
        """
        Set parallel or sequential (default) evaluation modes. In parallel mode the
        driver will check if it can start new evaluations every "waitTime" seconds.
        Builds the evaluation graphs (dependencies) for parallel execution.
        """
        self._parallelEval = parallel
        if not parallel: return # no need to build graphs
        self._waitTime = waitTime

        # get all unique evaluation steps
        valEvals = set()
        jacEvals = set()

        def _addEvals(flist,vlist,jlist):
            for obj in flist:
                vlist.update(obj.function.getValueEvalChain())
                jlist.update(obj.function.getGradientEvalChain())
            #end
        #end
        _addEvals(self._objectives   ,valEvals,jacEvals)
        _addEvals(self._constraintsEQ,valEvals,jacEvals)
        _addEvals(self._constraintsGT,valEvals,jacEvals)
        _addEvals(self._monitors     ,valEvals,jacEvals)

        # for each unique evaluation list its direct dependencies
        self._funEvalGraph = dict(zip(valEvals,[set() for i in range(len(valEvals))]))
        self._jacEvalGraph = dict(zip(jacEvals,[set() for i in range(len(jacEvals))]))

        def _addDependencies(flist,funGraph,jacGraph):
            for obj in flist:
                evals = obj.function.getValueEvalChain()
                for i in range(1,len(evals)):
                    funGraph[evals[i]].add(evals[i-1])

                evals = obj.function.getGradientEvalChain()
                for i in range(1,len(evals)):
                    jacGraph[evals[i]].add(evals[i-1])
            #end
        #end
        _addDependencies(self._objectives   ,self._funEvalGraph,self._jacEvalGraph)
        _addDependencies(self._constraintsEQ,self._funEvalGraph,self._jacEvalGraph)
        _addDependencies(self._constraintsGT,self._funEvalGraph,self._jacEvalGraph)
        _addDependencies(self._monitors     ,self._funEvalGraph,self._jacEvalGraph)
    #end

    # run the active evaluations of a dependency graph
    def _evalInParallel(self,dependGraph,active):
        # to avoid exiting with dangling evaluations we need to catch
        # all exceptions and throw when the infinite loop finishes
        error = False
        completed = lambda evl: evl.isRun() or evl.isError()
        while True:
            allRun = True
            for evl,depList in dependGraph.items():
                if not active[evl]: continue

                # ensure all dependencies are active
                for dep in depList:
                    active[dep] = True

                # either running or finished, move on
                if evl.isIni() or completed(evl):
                    try:
                        evl.poll() # (starts or updates internal state)
                        allRun &= completed(evl)
                    except:
                        error = True
                    #end
                    continue
                #end
                allRun &= completed(evl)

                # if dependencies are met start evaluation, error is considered
                # as "met" otherwise the outer loop would never exit
                for dep in depList:
                    if not completed(dep): break
                else:
                    try:
                        evl.initialize()
                        evl.poll()
                    except:
                        error = True
                    #end
                #end
            #end
            if allRun: break
            time.sleep(self._waitTime)
        #end
        if error: raise RuntimeError("Evaluations failed.")
    #end

    # run evaluations extracting maximum parallelism
    def _evalFunInParallel(self):
        self._funTime -= time.time()

        # all function evaluations are active by definition
        active = dict(zip(self._funEvalGraph.keys(), [True]*len(self._funEvalGraph)))

        self._evalInParallel(self._funEvalGraph, active)

        self._funTime += time.time()
    #end

    # same for gradients but having in mind which functions are active
    def _evalJacInParallel(self):
        self._jacTime -= time.time()

        # determine what evaluations are active based on functions
        active = dict(zip(self._jacEvalGraph.keys(), [False]*len(self._jacEvalGraph)))

        for obj in self._objectives:
            for evl in obj.function.getGradientEvalChain():
                active[evl] = True

        for obj in self._constraintsEQ:
            for evl in obj.function.getGradientEvalChain():
                active[evl] = True

        for (obj,f) in zip(self._constraintsGT,self._gtval):
            if f < 0.0 or not self._asNeeded:
                for evl in obj.function.getGradientEvalChain():
                    active[evl] = True

        # gradients are not needed for monitor functions

        self._evalInParallel(self._jacEvalGraph, active)

        self._jacTime += time.time()
    #end

    # runs a pre/post processing user action
    def _runAction(self, action):
        if action is None: return
        os.chdir(self._userDir)
        if isinstance(action,str):
            sp.call(action,shell=True)
        else:
            action()
        #end
    #end

    # Evaluate all functions (objectives and constraints), immediately
    # retrieves and stores the results after shifting and scaling.
    def _evaluateFunctions(self, x):
        self._handleVariableChange(x)

        # lazy evaluation
        if self._funReady: return False

        self._runAction(self._userPreProcessFun)

        os.chdir(self._workDir)

        if self._parallelEval:
            try:
                self._evalFunInParallel()
            except:
                if self._failureMode == "HARD": raise
        #end

        self._funEval += 1
        self._funTime -= time.time()

        def fetchValues(dst, src):
            for i, obj in enumerate(src):
                try:
                    dst[i] = obj.function.getValue()
                except:
                    if obj.function.hasDefaultValue() and self._failureMode == "SOFT":
                        dst[i] = obj.function.getDefaultValue()
                    else:
                        raise
                #end
            #end
        #end

        fetchValues(self._ofval, self._objectives)
        fetchValues(self._eqval, self._constraintsEQ)
        fetchValues(self._gtval, self._constraintsGT)
        fetchValues(self._monval, self._monitors)

        self._funTime += time.time()

        # monitor convergence (raw function values)
        self._writeHisLine()

        # shift constraints and scale as required
        for i, obj in enumerate(self._objectives):
            self._ofval[i] *= obj.scale

        for i, obj in enumerate(self._constraintsEQ):
            self._eqval[i] = (self._eqval[i] - obj.bound) * obj.scale

        for i, obj in enumerate(self._constraintsGT):
            self._gtval[i] = (self._gtval[i] - obj.bound) * obj.scale

        self._runAction(self._userPostProcessFun)

        os.chdir(self._userDir)
        self._funReady = True
        return True
    #end

    # Evaluates all gradients in parallel execution mode, otherwise
    # it only runs the user preprocessing and the execution takes place
    # when the results are read in "function.getGradient".
    def _evaluateGradients(self, x):
        # we assume that evaluating the gradients requires the functions
        self._evaluateFunctions(x)

        # lazy evaluation
        if self._jacReady: return False

        self._runAction(self._userPreProcessGrad)

        os.chdir(self._workDir)

        # evaluate everything, either in parallel or sequentially,
        # in the latter case the evaluations occur when retrieving the values
        if self._parallelEval:
            self._evalJacInParallel()
            self._runAction(self._userPostProcessGrad)
        #end

        os.chdir(self._userDir)
        self._jacReady = True
        self._jacEval += 1
        return True
    #end
#end

