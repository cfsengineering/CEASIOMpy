# Plain topology optimization example

from FADO import *
import subprocess
import ipyopt
subprocess.call("unzip -o ../example1_SU2/data.zip",shell=True)

# Design variables
rho = InputVariable(0.5,TableWriter("  ",(1,-1)),1600,1.0,0.0,1.0)

# Parameters
adjointOutput = Parameter(["= NONE"], LabelReplacer("= RESTART"))
fType_objective = Parameter(["TOPOL_COMPLIANCE"], LabelReplacer("__FUNCTION__"))
fType_constraint = Parameter(["VOLUME_FRACTION"], LabelReplacer("__FUNCTION__"))
linIters_constraint = Parameter(["LINEAR_SOLVER_ITER= 1"],
                   LabelReplacer("LINEAR_SOLVER_ITER= 1000"))
beta = Parameter([0.01, 1, 4, 16, 64, 200],LabelReplacer("__BETA__"))

# Evaluations
direct = ExternalRun("DIRECT","SU2_CFD -t 1 settings.cfg",True)
direct.addConfig("settings.cfg")
direct.addConfig("element_properties.dat")
direct.addData("mesh.su2")
direct.addParameter(fType_objective)
direct.addParameter(beta)

objective = ExternalRun("OBJECTIVE","SU2_CFD_AD settings.cfg",True)
objective.addConfig("settings.cfg")
objective.addConfig("element_properties.dat")
objective.addData("mesh.su2")
objective.addData("DIRECT/solution.dat")
objective.addParameter(fType_objective)
objective.addParameter(adjointOutput)
objective.addParameter(beta)

constraint = ExternalRun("CONSTRAINT","SU2_CFD_AD settings.cfg",True)
constraint.addConfig("settings.cfg")
constraint.addConfig("element_properties.dat")
constraint.addData("mesh.su2")
constraint.addData("DIRECT/solution.dat")
constraint.addParameter(fType_constraint)
constraint.addParameter(linIters_constraint)
constraint.addParameter(adjointOutput)
constraint.addParameter(beta)

# Functions
fun1 = Function("compliance","DIRECT/history.csv",LabeledTableReader('"TopComp"'))
fun1.addInputVariable(rho,"OBJECTIVE/grad.dat",TableReader(None,0))
fun1.addValueEvalStep(direct)
fun1.addGradientEvalStep(objective)

fun2 = Function("solid_fraction","DIRECT/history.csv",LabeledTableReader('"VolFrac"'))
fun2.addInputVariable(rho,"CONSTRAINT/grad.dat",TableReader(None,0))
fun2.addValueEvalStep(direct)
fun2.addGradientEvalStep(constraint)

# Driver
driver = IpoptDriver()
driver.addObjective("min",fun1,800.0)
driver.addUpperBound(fun2,0.5,2.0)

driver.setEvaluationMode(True,0.05)
driver.setStorageMode(False)

nlp = driver.getNLP()

ipyopt.set_loglevel(ipyopt.LOGGING_DEBUG)

# Optimization
x = driver.getInitial()

# initial multipliers, we need to keep these for warm starts
conMult = np.zeros(1)
lbMult = np.zeros(x.size)
ubMult = np.zeros(x.size)

stop = False
while not stop:
    stop = beta.isAtTop()

    nlp.set(warm_start_init_point = ("yes","no")[beta.isAtBottom()], # use warm start ["no"]
            nlp_scaling_method = "none",    # we are already doing some scaling
            accept_every_trial_step = "no", # can be used to force single ls per iteration
            limited_memory_max_history = 15,# the "L" in L-BFGS
            max_iter = (25,200)[stop],
            tol = 1e-6,                     # this and max_iter are the main stopping criteria
            acceptable_iter = 10,
            acceptable_tol = 1e-3,
            acceptable_obj_change_tol=1e-6, # Cauchy-type convergence over "acceptable_iter"
            mu_min = 1e-8,                  # for very low values (e-10) the problem "flip-flops"
            recalc_y_feas_tol = 0.1)        # helps converging the dual problem with L-BFGS

    x, obj, status = nlp.solve(x, mult_g = conMult, mult_x_L = lbMult, mult_x_U = ubMult)

    print("\n\n")

    driver.update()
#end

