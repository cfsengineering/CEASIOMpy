# The basic Rosenbrock example using Ipopt via IPyOpt

from FADO import *
import ipyopt
from shutil import copy

copy("../rosenbrock/direct.py",".")
copy("../rosenbrock/adjoint.py",".")
copy("../rosenbrock/config_tmpl.txt",".")
copy("../rosenbrock/data1.txt",".")
copy("../rosenbrock/data2.txt",".")

# Design variables of the problem
# this defines initial value and how they are written to an arbitrary file
var1 = InputVariable(0.0,LabelReplacer("__X__"))
var2 = InputVariable(0.0,LabelReplacer("__Y__"))

# Parameters
# these parameters tailor the template config to each function
parData1 = Parameter(["data1.txt"],LabelReplacer("__DATA_FILE__"))
parData2 = Parameter(["data2.txt"],LabelReplacer("__DATA_FILE__"))
parFunc1 = Parameter(["rosenbrock"],LabelReplacer("__FUNCTION__"))
parFunc2 = Parameter(["constraint"],LabelReplacer("__FUNCTION__"))

# Evaluations
# "runs" that are needed to compute functions and their gradients
evalFun1 = ExternalRun("RUN1","python3 ../../direct.py config_tmpl.txt")
evalFun1.addConfig("config_tmpl.txt")
evalFun1.addData("data1.txt")
evalFun1.addParameter(parData1)

evalJac1 = ExternalRun("JAC1","python3 ../../adjoint.py config_tmpl.txt")
evalJac1.addConfig("config_tmpl.txt")
evalJac1.addData("data1.txt")
evalJac1.addData("RUN1/results.txt") # simulate we need data from the direct run
evalJac1.addParameter(parData1)
evalJac1.addParameter(parFunc1)

evalFun2 = ExternalRun("RUN2","python3 ../../direct.py config_tmpl.txt")
evalFun2.addConfig("config_tmpl.txt")
evalFun2.addData("data2.txt")
evalFun2.addParameter(parData2)

evalJac2 = ExternalRun("JAC2","python3 ../../adjoint.py config_tmpl.txt")
evalJac2.addConfig("config_tmpl.txt")
evalJac2.addData("data2.txt")
evalJac2.addData("RUN2/results.txt") # simulate we need data from the direct run
evalJac2.addParameter(parData2)
evalJac2.addParameter(parFunc1)

evalJac3 = ExternalRun("JAC3","python3 ../../adjoint.py config_tmpl.txt")
evalJac3.addConfig("config_tmpl.txt")
evalJac3.addData("data2.txt")
evalJac3.addData("RUN2/results.txt") # simulate we need data from the direct run
evalJac3.addParameter(parData2)
evalJac3.addParameter(parFunc2)

# Functions
# now variables, parameters, and evaluations are combined
fun1 = Function("Rosenbrock1","RUN1/results.txt",TableReader(0,0))
fun1.addInputVariable(var1,"JAC1/gradient.txt",TableReader(0,0))
fun1.addInputVariable(var2,"JAC1/gradient.txt",TableReader(1,0))
fun1.addValueEvalStep(evalFun1)
fun1.addGradientEvalStep(evalJac1)

fun2 = Function("Rosenbrock2","RUN2/results.txt",TableReader(0,0))
fun2.addInputVariable(var1,"JAC2/gradient.txt",TableReader(0,0))
fun2.addInputVariable(var2,"JAC2/gradient.txt",TableReader(1,0))
fun2.addValueEvalStep(evalFun2)
fun2.addGradientEvalStep(evalJac2)

fun3 = Function("Constraint2","RUN2/results.txt",TableReader(1,0))
fun3.addInputVariable(var1,"JAC3/gradient.txt",TableReader(0,0))
fun3.addInputVariable(var2,"JAC3/gradient.txt",TableReader(1,0))
fun3.addValueEvalStep(evalFun2)
fun3.addGradientEvalStep(evalJac3)

# Driver
# the optimization is defined by the objectives and constraints
driver = IpoptDriver()
driver.addObjective("min",fun1,0.5)
driver.addObjective("min",fun2,0.5)
driver.addUpperBound(fun3,2.0)

driver.setStorageMode(False)
driver.setEvaluationMode(True,1.0)
nlp = driver.getNLP()

ipyopt.set_loglevel(ipyopt.LOGGING_DEBUG)

# Optimization
x0 = driver.getInitial()
results = nlp.solve(x0)

# report the results
print(results)

