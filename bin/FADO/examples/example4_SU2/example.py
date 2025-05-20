# Shape optimization of fluid structure interaction

from FADO import *
import subprocess
subprocess.call("unzip -o data.zip",shell=True)

# Design variables ----------------------------------------------------- #

x0 = np.zeros((17,))
ffd = InputVariable(x0,ArrayLabelReplacer("__FFD_PTS__"),0,(1/0.03),-0.03,0.03)

# Parameters ----------------------------------------------------------- #

# switch from direct to adjoint mode and adapt settings
enable_direct = Parameter([""], LabelReplacer("%__DIRECT__"))
enable_adjoint = Parameter([""], LabelReplacer("%__ADJOINT__"))

# switch input mesh to perform deformation
mesh_in = Parameter(["MESH_FILENAME= mesh_ffd.su2"],\
       LabelReplacer("MESH_FILENAME= mesh_def.su2"))

# switch from compliance to lift or drag
func_drag = Parameter(["OBJECTIVE_FUNCTION= DRAG"],\
         LabelReplacer("OBJECTIVE_FUNCTION= TOPOL_COMPLIANCE"))
func_lift = Parameter(["OBJECTIVE_FUNCTION= LIFT"],\
         LabelReplacer("OBJECTIVE_FUNCTION= TOPOL_COMPLIANCE"))
func_mom = Parameter(["OBJECTIVE_FUNCTION= MOMENT_Z"],\
        LabelReplacer("OBJECTIVE_FUNCTION= TOPOL_COMPLIANCE"))


# Evaluations ---------------------------------------------------------- #

def_command = "SU2_DEF config.cfg"

geo_command = "SU2_GEO config_geo.cfg"

dir_command = "SU2_CFD config.cfg"

adj_command = "mpirun -n 4 SU2_CFD_AD config.cfg && mpirun -n 4 SU2_DOT_AD config.cfg"

max_tries = 1

# mesh deformation
deform = ExternalRun("DEFORM",def_command,True)
deform.setMaxTries(max_tries)
deform.addConfig("config.cfg")
deform.addConfig("configFlow.cfg")
deform.addConfig("configFEA.cfg")
deform.addData("mesh_ffd.su2")
deform.addExpected("mesh_def.su2")
deform.addParameter(enable_direct)
deform.addParameter(mesh_in)

# geometric properties
geometry = ExternalRun("GEOMETRY",geo_command,True)
geometry.setMaxTries(max_tries)
geometry.addConfig("config_geo.cfg")
geometry.addConfig("configFlow.cfg")
geometry.addConfig("configFEA.cfg")
geometry.addData("DEFORM/mesh_def.su2")
geometry.addExpected("of_func.csv")

# direct run
direct = ExternalRun("DIRECT",dir_command,True)
direct.setMaxTries(max_tries)
direct.addConfig("config.cfg")
direct.addConfig("configFlow.cfg")
direct.addConfig("configFEA.cfg")
direct.addData("DEFORM/mesh_def.su2")
direct.addExpected("solution_0.dat")
direct.addParameter(enable_direct)

def makeAdjRun(name, func=None) :
    adj = ExternalRun(name,adj_command,True)
    adj.setMaxTries(max_tries)
    adj.addConfig("config.cfg")
    adj.addConfig("configFlow.cfg")
    adj.addConfig("configFEA.cfg")
    adj.addData("DEFORM/mesh_def.su2")
    adj.addData("DIRECT/solution_0.dat")
    adj.addData("DIRECT/solution_1.dat")
    adj.addExpected("of_grad.dat")
    adj.addParameter(enable_adjoint)
    if (func is not None) : adj.addParameter(func)
    return adj
#end

# adjoints of lift
lift_adj = makeAdjRun("LIFT_ADJ",func_lift)

# adjoints of drag
drag_adj = makeAdjRun("DRAG_ADJ",func_drag)

# adjoints of moment
mom_adj = makeAdjRun("MOM_ADJ",func_mom)

# adjoints of compliance
comp_adj = makeAdjRun("COMP_ADJ")


# Functions ------------------------------------------------------------ #

lift = Function("lift","DIRECT/history_0.csv",LabeledTableReader('"CL"'))
lift.addInputVariable(ffd,"LIFT_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
lift.addValueEvalStep(deform)
lift.addValueEvalStep(direct)
lift.addGradientEvalStep(lift_adj)
lift.setDefaultValue(0.0)

drag = Function("drag","DIRECT/history_0.csv",LabeledTableReader('"CD"'))
drag.addInputVariable(ffd,"DRAG_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
drag.addValueEvalStep(deform)
drag.addValueEvalStep(direct)
drag.addGradientEvalStep(drag_adj)
drag.setDefaultValue(1.0)

mom = Function("mom","DIRECT/history_0.csv",LabeledTableReader('"CMz"'))
mom.addInputVariable(ffd,"MOM_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
mom.addValueEvalStep(deform)
mom.addValueEvalStep(direct)
mom.addGradientEvalStep(mom_adj)
mom.setDefaultValue(-1.0)

comp = Function("comp","DIRECT/history_1.csv",LabeledTableReader('"TopComp"'))
comp.addInputVariable(ffd,"COMP_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
comp.addValueEvalStep(deform)
comp.addValueEvalStep(direct)
comp.addGradientEvalStep(comp_adj)
comp.setDefaultValue(100.0)

min_thick = Function("t_min","GEOMETRY/of_func.csv",LabeledTableReader('"AIRFOIL_THICKNESS"'))
min_thick.addInputVariable(ffd,"GEOMETRY/of_grad.csv",LabeledTableReader('"AIRFOIL_THICKNESS"',',',(0,None)))
min_thick.addValueEvalStep(deform)
min_thick.addValueEvalStep(geometry)
min_thick.setDefaultValue(0.0)

# Driver --------------------------------------------------------------- #

driver = ScipyDriver()
driver.addObjective("min", drag, 125.0)
driver.addLowerBound(lift, 0.4, 2.5)
driver.addLowerBound(mom, -0.01, 100)
driver.addUpperBound(comp, 5.0, 0.2)
driver.addLowerBound(min_thick, 0.03, 30)

driver.setWorkingDirectory("OPTIM")
driver.setEvaluationMode(False,2.0)
driver.setStorageMode(True,"DSN_")
driver.setFailureMode("SOFT")

his = open("optim.his","w",1)
driver.setHistorian(his)

# Optimization, SciPy -------------------------------------------------- #

import scipy.optimize

driver.preprocess()
x = driver.getInitial()

options = {'disp': True, 'ftol': 1e-7, 'maxiter': 100}

optimum = scipy.optimize.minimize(driver.fun, x, method="SLSQP", jac=driver.grad,\
          constraints=driver.getConstraints(), bounds=driver.getBounds(), options=options)

his.close()

