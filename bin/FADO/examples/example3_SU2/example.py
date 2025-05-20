# Shape and Topology optimization with 2 load cases

from FADO import *
import scipy.optimize
import os

import subprocess
subprocess.call("unzip -o data.zip",shell=True)

# Design variables
ffd = InputVariable(0.0,PreStringHandler("DV_VALUE= "),9,1.0,-15.0,15.0)
rho = InputVariable(0.5,TableWriter("  ",(1,-1)),4800,1.0,0.0,1.0)

# Parameters
# switch from displacement to volume fraction
func_constraint = Parameter(["OBJECTIVE_FUNCTION= VOLUME_FRACTION"],\
               LabelReplacer("OBJECTIVE_FUNCTION= REFERENCE_NODE"))
# computing the volume constraint gradients does not require an accurate solution
iter_constraint = Parameter(["LINEAR_SOLVER_ITER= 1"], LabelReplacer("LINEAR_SOLVER_ITER= 1000"))
# two load cases
load_horizontal = Parameter(["1.0,  0.0"],LabelReplacer("__LOAD_DIR__"))
load_vertical   = Parameter(["0.0, -1.0"],LabelReplacer("__LOAD_DIR__"))
# this is a meta-parameter, for SU2_GEO the FFD variables are the FD step sizes
vars_geometry = Parameter(["DV_VALUE=0.001"+",0.001"*(ffd.getSize()-1)],\
             LabelReplacer("DV_VALUE= 0"+",0"*(ffd.getSize()-1)))
# filter kernels and radius
filter_type = Parameter(["CONICAL","ERODE,DILATE"],LabelReplacer("__FILTER__"))
filter_radius = Parameter([3.5,1.5],LabelReplacer("__RADIUS__"))
# the ramp for the filter kernel parameter
beta = Parameter([0.01, 64],LabelReplacer("__BETA__"))

# Evaluations
# mesh deformation
deform = ExternalRun("DEFORM","SU2_DEF settings.cfg",True)
deform.addConfig("settings.cfg")
deform.addData("mesh_ffd.su2")
# these parameters are not relevant but are needed to make a valid config
deform.addParameter(load_vertical)
deform.addParameter(filter_type)
deform.addParameter(filter_radius)
deform.addParameter(beta)

# geometric properties
geometry = ExternalRun("GEOMETRY","SU2_GEO settings.cfg",True)
geometry.addConfig("settings.cfg")
geometry.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
geometry.addParameter(vars_geometry)
# these parameters are not relevant but are needed to make a valid config
geometry.addParameter(load_vertical)
geometry.addParameter(filter_type)
geometry.addParameter(filter_radius)
geometry.addParameter(beta)

# horizontal load case
hload_dir = ExternalRun("HLOAD","SU2_CFD -t 2 settings.cfg",True)
hload_dir.addConfig("settings.cfg")
hload_dir.addConfig("element_properties.dat")
hload_dir.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
hload_dir.addParameter(load_horizontal)
hload_dir.addParameter(filter_type)
hload_dir.addParameter(filter_radius)
hload_dir.addParameter(beta)

# vertical load case
vload_dir = ExternalRun("VLOAD","SU2_CFD -t 2 settings.cfg",True)
vload_dir.addConfig("settings.cfg")
vload_dir.addConfig("element_properties.dat")
vload_dir.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
vload_dir.addParameter(load_vertical)
vload_dir.addParameter(filter_type)
vload_dir.addParameter(filter_radius)
vload_dir.addParameter(beta)

adj_command = "mpirun -n 2 --bind-to none SU2_CFD_AD settings.cfg &&\
               mv restart_adj_FUN.dat solution_adj_FUN.dat &&\
               SU2_DOT_AD settings.cfg"

# volume fraction and its derivatives
volume = ExternalRun("VOLUME",adj_command.replace("FUN","volfrac"),True)
volume.addConfig("settings.cfg")
volume.addConfig("element_properties.dat")
volume.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
volume.addData("direct.dat") # dummy solution file
volume.addParameter(func_constraint)
volume.addParameter(iter_constraint)
volume.addParameter(filter_type)
volume.addParameter(filter_radius)
volume.addParameter(beta)
# this one is not relevant
volume.addParameter(load_vertical)

# adjoints of the horizontal load
hload_adj = ExternalRun("HLOAD_ADJ",adj_command.replace("FUN","refnode"),True)
hload_adj.addConfig("settings.cfg")
hload_adj.addConfig("element_properties.dat")
hload_adj.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
hload_adj.addData("HLOAD/direct.dat")
hload_adj.addParameter(load_horizontal)
hload_adj.addParameter(filter_type)
hload_adj.addParameter(filter_radius)
hload_adj.addParameter(beta)

# adjoints of the vertical load
vload_adj = ExternalRun("VLOAD_ADJ",adj_command.replace("FUN","refnode"),True)
vload_adj.addConfig("settings.cfg")
vload_adj.addConfig("element_properties.dat")
vload_adj.addData("DEFORM/mesh_def.su2",destination="mesh_ffd.su2")
vload_adj.addData("VLOAD/direct.dat")
vload_adj.addParameter(load_vertical)
vload_adj.addParameter(filter_type)
vload_adj.addParameter(filter_radius)
vload_adj.addParameter(beta)

# Functions
vert_disp = Function("vert_disp","VLOAD/history.csv",LabeledTableReader('"RefNode"'))
vert_disp.addInputVariable(ffd,"VLOAD_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
vert_disp.addInputVariable(rho,"VLOAD_ADJ/grad.dat",TableReader(None,0))
vert_disp.addValueEvalStep(deform)
vert_disp.addValueEvalStep(vload_dir)
vert_disp.addGradientEvalStep(vload_adj)

horiz_disp = Function("horiz_disp","HLOAD/history.csv",LabeledTableReader('"RefNode"'))
horiz_disp.addInputVariable(ffd,"HLOAD_ADJ/of_grad.dat",TableReader(None,0,(1,0)))
horiz_disp.addInputVariable(rho,"HLOAD_ADJ/grad.dat",TableReader(None,0))
horiz_disp.addValueEvalStep(deform)
horiz_disp.addValueEvalStep(hload_dir)
horiz_disp.addGradientEvalStep(hload_adj)

vol_frac = Function("vol_frac","VLOAD/history.csv",LabeledTableReader('"VolFrac"'))
vol_frac.addInputVariable(ffd,"VOLUME/of_grad.dat",TableReader(None,0,(1,0)))
vol_frac.addInputVariable(rho,"VOLUME/grad.dat",TableReader(None,0))
vol_frac.addValueEvalStep(deform)
vol_frac.addValueEvalStep(vload_dir)
vol_frac.addGradientEvalStep(volume)

vol_total = Function("vol_total","GEOMETRY/of_func.csv",LabeledTableReader('"AIRFOIL_AREA"'))
vol_total.addInputVariable(ffd,"GEOMETRY/of_grad.csv",TableReader(None,1,(1,0),(None,None),","))
vol_total.addValueEvalStep(deform)
vol_total.addValueEvalStep(geometry)

# Driver
driver = ExteriorPenaltyDriver(0.01,0,8.0,256.0,np.sqrt(2))
driver.addObjective("min",vert_disp, 1.0,0.5)
driver.addObjective("min",horiz_disp,3.5,0.5)
driver.addUpperBound(vol_frac,0.5,2.0)
driver.addUpperBound(vol_total,4800,2e-4)

driver.setWorkingDirectory("currentDesign")
driver.preprocessVariables()
driver.setEvaluationMode(True,0.1)
driver.setStorageMode(True)

log = open("log.txt","w",1)
his = open("history.txt","w",1)
driver.setLogger(log)
driver.setHistorian(his)

# Optimization
x  = driver.getInitial()
lb = driver.getLowerBound()
ub = driver.getUpperBound()
bounds = np.array((lb,ub),float).transpose()
update_iters = 18
max_iters = 1000
fin_tol = 1e-7

options={'disp': True, 'maxcor': 10, 'ftol': fin_tol*10, 'gtol': 1e-12, 'maxls': 5, 'maxiter': update_iters}

# respect constraints with grey settings
while not driver.feasibleDesign() and max_iters > 0:
  optimum = scipy.optimize.minimize(driver.fun, x, method="L-BFGS-B",\
            jac=driver.grad, bounds=bounds, options=options)
  x = optimum.x
  max_iters -= optimum.nit
  driver.update(True)
#end

# converge to solid-void settings
options['ftol'] = fin_tol
options['maxiter'] = max_iters
optimum = scipy.optimize.minimize(driver.fun, x, method="L-BFGS-B",\
          jac=driver.grad, bounds=bounds, options=options)
driver.update()

log.close()
his.close()

