"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of CPACS xpath which are used in CEASIOMpy, if possible base xpath must be
called only from here to avoid mistakes.
XPath may be changed from here to avoid mistakes, but if it is the case, be careful to also change
xpath and field name in all the test CPACS files, which are in the CEASIOMpy repository.

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2021-10-21

TODO:

    *

"""

# Header
AIRCRAFT_NAME_XPATH = "/cpacs/header/name"

# model
REF_XPATH = "/cpacs/vehicles/aircraft/model/reference"
FUSELAGES_XPATH = "/cpacs/vehicles/aircraft/model/fuselages"
WINGS_XPATH = "/cpacs/vehicles/aircraft/model/wings"
PYLONS_XPATH = "/cpacs/vehicles/aircraft/model/enginePylons"
ENGINES_XPATH = "/cpacs/vehicles/aircraft/model/engines"

# analyses
AEROPERFORMANCE_XPATH = "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"
AEROMAP_XPATH = "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"  # To remove
MASSBREAKDOWN_XPATH = "/cpacs/vehicles/aircraft/model/analyses/massBreakdown"

# fuel
F_XPATH = "/cpacs/vehicles/fuels/fuel"

# CEASIOMpy
CEASIOMPY_XPATH = "/cpacs/toolspecific/CEASIOMpy"
EXPORT_XPATH = "/cpacs/toolspecific/CEASIOMpy/export"
FUEL_XPATH = "/cpacs/toolspecific/CEASIOMpy/fuels"
FUEL_CONSUMPTION_XPATH = "/cpacs/toolspecific/CEASIOMpy/fuelConsumption"
GEOM_XPATH = "/cpacs/toolspecific/CEASIOMpy/geometry"
MESH_XPATH = "/cpacs/toolspecific/CEASIOMpy/mesh"
OPTIM_XPATH = "/cpacs/toolspecific/CEASIOMpy/optimisation"
PROP_XPATH = "/cpacs/toolspecific/CEASIOMpy/propulsion"
RANGE_XPATH = "/cpacs/toolspecific/CEASIOMpy/ranges"
WEIGHT_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight"

CLCALC_XPATH = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/clCalculation"
PLOT_XPATH = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient"

SF_XPATH = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction"

WETTED_AREA_XPATH = "/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea"

SMTRAIN_XPATH = "/cpacs/toolspecific/CEASIOMpy/surrogateModel"
SMUSE_XPATH = "/cpacs/toolspecific/CEASIOMpy/surrogateModelUse"

STABILITY_STATIC_XPATH = "/cpacs/toolspecific/CEASIOMpy/stability/static"
STABILITY_DYNAMIC_XPATH = "/cpacs/toolspecific/CEASIOMpy/stability/dynamic"

PASS_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight/passengers"
ML_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight/massLimits"
CREW_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight/crew"
PILOTS_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight/crew/pilots"
CAB_CREW_XPATH = "/cpacs/toolspecific/CEASIOMpy/weight/crew/cabinCrewMembers"

OPTWKDIR_XPATH = "/cpacs/toolspecific/CEASIOMpy/filesPath/optimPath"
SMFILE_XPATH = "/cpacs/toolspecific/CEASIOMpy/filesPath/SMpath"
SU2MESH_XPATH = "/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh"
SUMOFILE_XPATH = "/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath"
WKDIR_XPATH = "/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath"


# GMSH


# SU2
SU2_XPATH = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2"
SU2_AEROMAP_UID_XPATH = SU2_XPATH + "/aeroMapUID"
SU2_NB_CPU_XPATH = SU2_XPATH + "/settings/nbCPU"
SU2_EXTRACT_LOAD_XPATH = SU2_XPATH + "/results/extractLoads"

SU2_MAX_ITER_XPATH = SU2_XPATH + "/settings/maxIter"
SU2_CFL_NB_XPATH = SU2_XPATH + "/settings/cflNumber"
SU2_MG_LEVEL_XPATH = SU2_XPATH + "/settings/multigridLevel"

SU2_BC_WALL_XPATH = SU2_XPATH + "/boundaryConditions/wall"
SU2_BC_FARFIELD_XPATH = SU2_XPATH + "/boundaryConditions/farfield"

SU2_FIXED_CL_XPATH = SU2_XPATH + "/fixedCL"
SU2_TARGET_CL_XPATH = SU2_XPATH + "/targetCL"

SU2_DAMPING_DER_XPATH = SU2_XPATH + "/options/calculateDampingDerivatives"
SU2_ROTATION_RATE_XPATH = SU2_XPATH + "/options/rotationRate"

SU2_CONTROL_SURF_XPATH = SU2_XPATH + "/options/calculateControlSurfacesDeflections"
SU2_DEF_MESH_XPATH = SU2_XPATH + "/availableDeformedMesh"


# pytornado
PYTORNADO_XPATH = "/cpacs/toolspecific/pytornado"
