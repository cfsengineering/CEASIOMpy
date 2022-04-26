"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of CPACS xpath which are used in CEASIOMpy, if possible base xpath must be
called only from here to avoid mistakes.

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2021-10-21

TODO:

    *

"""


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
SU2_XPATH = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2"

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

# pytornado
PYTORNADO_XPATH = "/cpacs/toolspecific/pytornado"

# GMSH
GMSHFILE_XPATH = "/cpacs/toolspecific/CEASIOMpy/mesh/gmsh"
