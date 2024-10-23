"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of CPACS xpath which are used in CEASIOMpy, if possible base xpath must be
called only from here to avoid mistakes.
XPath may be changed from here to avoid mistakes, but if it is the case, be careful to also change
xpath and field name in all the test CPACS files, which are in the CEASIOMpy repository.

Python version: >=3.8

| Author: Aidan jungo
| Creation: 2021-10-21
| Last modifiction: 2024-01-05 (Mengmeng Zhang, added M-Edge XPATHs )

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

MASSBREAKDOWN_XPATH = "/cpacs/vehicles/aircraft/model/analyses/massBreakdown"

MTOM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass"
MZFM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass"
MOEM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/massDescription/mass"
FUEL_MASS_XPATH = MASSBREAKDOWN_XPATH + "/fuel/massDescription/mass"
PAYLOAD_DESCRIPTION_XPATH = MASSBREAKDOWN_XPATH + "/payload/massDescription"
PAYLOAD_MASS_XPATH = MASSBREAKDOWN_XPATH + "/payload/mass"
PAYLOAD_CARGO_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo"

F_XPATH = "/cpacs/vehicles/fuels/fuel"  # TODO remove
FUEL_DENSITY_XPATH = "/cpacs/vehicles/fuels/fuel/density"
MASS_CARGO_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo/massDescription/mass"

# CEASIOMpy
CEASIOMPY_XPATH = "/cpacs/toolspecific/CEASIOMpy"
EXPORT_XPATH = CEASIOMPY_XPATH + "/export"
FUEL_XPATH = CEASIOMPY_XPATH + "/fuels"
FUEL_CONSUMPTION_XPATH = CEASIOMPY_XPATH + "/fuelConsumption"
GEOM_XPATH = CEASIOMPY_XPATH + "/geometry"
MESH_XPATH = CEASIOMPY_XPATH + "/mesh"
OPTIM_XPATH = CEASIOMPY_XPATH + "/optimisation"
PROP_XPATH = CEASIOMPY_XPATH + "/propulsion"
RANGE_XPATH = CEASIOMPY_XPATH + "/ranges"
WEIGHT_XPATH = CEASIOMPY_XPATH + "/weight"

CLCALC_XPATH = CEASIOMPY_XPATH + "/aerodynamics/clCalculation"
PLOT_XPATH = CEASIOMPY_XPATH + "/aerodynamics/plotAeroCoefficient"

SF_XPATH = CEASIOMPY_XPATH + "/aerodynamics/skinFriction"

WETTED_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wettedArea"
WING_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingArea"
WING_SPAN_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingSpan"

SMTRAIN_XPATH = CEASIOMPY_XPATH + "/surrogateModel"
SMUSE_XPATH = CEASIOMPY_XPATH + "/surrogateModelUse"

STABILITY_STATIC_XPATH = CEASIOMPY_XPATH + "/stability/static"
STABILITY_DYNAMIC_XPATH = CEASIOMPY_XPATH + "/stability/dynamic"

OPTWKDIR_XPATH = CEASIOMPY_XPATH + "/filesPath/optimPath"
SMFILE_XPATH = CEASIOMPY_XPATH + "/filesPath/SMpath"
SU2MESH_XPATH = CEASIOMPY_XPATH + "/filesPath/su2Mesh"
EDGE_MESH_XPATH = CEASIOMPY_XPATH + "/filesPath/edgeMesh"

SUMOFILE_XPATH = CEASIOMPY_XPATH + "/filesPath/sumoFilePath"
WKDIR_XPATH = CEASIOMPY_XPATH + "/filesPath/wkdirPath"

# Propulsion
TURBOPROP_XPATH = PROP_XPATH + "/turboprop"

# SUMO
SUMO_OUTPUT_MESH_FORMAT_XPATH = MESH_XPATH + "sumoOptions/format"
SUMO_REFINE_LEVEL_XPATH = MESH_XPATH + "/sumoOptions/refinementLevel"
SUMO_INCLUDE_PYLON_XPATH = CEASIOMPY_XPATH + "/engine/includePylon"
SUMO_INCLUDE_ENGINE_XPATH = CEASIOMPY_XPATH + "/engine/includeEngine"

# GMSH
GMSH_XPATH = MESH_XPATH + "/gmshOptions"
GMSH_OPEN_GUI_XPATH = GMSH_XPATH + "/open_gui"
GMSH_SYMMETRY_XPATH = GMSH_XPATH + "/symmetry"
GMSH_EXPORT_PROP_XPATH = GMSH_XPATH + "/exportPropellers"
GMSH_FARFIELD_FACTOR_XPATH = GMSH_XPATH + "/farfield_factor"
GMSH_N_POWER_FACTOR_XPATH = GMSH_XPATH + "/n_power_factor"
GMSH_N_POWER_FIELD_XPATH = GMSH_XPATH + "/n_power_field"
GMSH_MESH_TYPE_XPATH = GMSH_XPATH + "/type_mesh"
GMSH_MESH_SIZE_FARFIELD_XPATH = GMSH_XPATH + "/mesh_size/farfield"
GMSH_MESH_SIZE_FUSELAGE_XPATH = GMSH_XPATH + "/mesh_size/fuselage/value"
GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH = GMSH_XPATH + "/mesh_size/fuselage/factor"
GMSH_MESH_SIZE_WINGS_XPATH = GMSH_XPATH + "/mesh_size/wings/value"
GMSH_MESH_SIZE_FACTOR_WINGS_XPATH = GMSH_XPATH + "/mesh_size/wings/factor"
GMSH_MESH_SIZE_ENGINES_XPATH = GMSH_XPATH + "/mesh_size/engines"
GMSH_MESH_SIZE_PROPELLERS_XPATH = GMSH_XPATH + "/mesh_size/propellers"
GMSH_REFINE_FACTOR_XPATH = GMSH_XPATH + "/refine_factor"
GMSH_REFINE_TRUNCATED_XPATH = GMSH_XPATH + "/refine_truncated"
GMSH_AUTO_REFINE_XPATH = GMSH_XPATH + "/auto_refine"
GMSH_INTAKE_PERCENT_XPATH = GMSH_XPATH + "/intake_percent"
GMSH_EXHAUST_PERCENT_XPATH = GMSH_XPATH + "/exhaust_percent"
GMSH_MESH_FORMAT_XPATH = GMSH_XPATH + "/type_output_penta"
GMSH_NUMBER_LAYER_XPATH = GMSH_XPATH + "/number_layer"
GMSH_H_FIRST_LAYER_XPATH = GMSH_XPATH + "/height_first_layer"
GMSH_MAX_THICKNESS_LAYER_XPATH = GMSH_XPATH + "/max_thickness_layer"
GMSH_GROWTH_FACTOR_XPATH = GMSH_XPATH + "/growth_factor"
GMSH_GROWTH_RATIO_XPATH = GMSH_XPATH + "/growth_ratio"
MIN_GMSH_SURFACE_MESH_SIZE_XPATH = GMSH_XPATH + "min_mesh_factor"
MAX_GMSH_SURFACE_MESH_SIZE_XPATH = GMSH_XPATH + "max_mesh_factor"
GMSH_FEATURE_ANGLE_XPATH = GMSH_XPATH + "/feature_angle"

# SU2
SU2_XPATH = CEASIOMPY_XPATH + "/aerodynamics/su2"
SU2_AEROMAP_UID_XPATH = SU2_XPATH + "/aeroMapUID"
SU2_NB_CPU_XPATH = SU2_XPATH + "/settings/nbCPU"
SU2_EXTRACT_LOAD_XPATH = SU2_XPATH + "/results/extractLoads"
SU2_UPDATE_WETTED_AREA_XPATH = SU2_XPATH + "/results/updateWettedArea"

SU2_MAX_ITER_XPATH = SU2_XPATH + "/settings/maxIter"
SU2_CFL_NB_XPATH = SU2_XPATH + "/settings/cflNumber/value"
SU2_CFL_ADAPT_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/value"
SU2_CFL_ADAPT_PARAM_DOWN_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/factor_down"
SU2_CFL_ADAPT_PARAM_UP_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/factor_up"
SU2_CFL_MIN_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/min"
SU2_CFL_MAX_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/max"
SU2_MG_LEVEL_XPATH = SU2_XPATH + "/settings/multigridLevel"

SU2_BC_WALL_XPATH = SU2_XPATH + "/boundaryConditions/wall"
SU2_BC_FARFIELD_XPATH = SU2_XPATH + "/boundaryConditions/farfield"

SU2_FIXED_CL_XPATH = SU2_XPATH + "/fixedCL"
SU2_TARGET_CL_XPATH = SU2_XPATH + "/targetCL"

SU2_DAMPING_DER_XPATH = SU2_XPATH + "/options/calculateDampingDerivatives"
SU2_ROTATION_RATE_XPATH = SU2_XPATH + "/options/rotationRate"

SU2_CONTROL_SURF_XPATH = SU2_XPATH + "/options/calculateControlSurfacesDeflections"
SU2_DEF_MESH_XPATH = SU2_XPATH + "/availableDeformedMesh"

SU2_ACTUATOR_DISK_XPATH = SU2_XPATH + "/options/includeActuatorDisk"
SU2_CONFIG_RANS_XPATH = SU2_XPATH + "/options/config_type"

# EDGE
EDGE_XPATH = CEASIOMPY_XPATH + "/aerodynamics/medge"
EDGE_AEROMAP_UID_XPATH = EDGE_XPATH + "/aeroMapUID"
EDGE_NB_CPU_XPATH = EDGE_XPATH + "/settings/nbCPU"
EDGE_SOLVER_XPATH = EDGE_XPATH + "/settings/solver"
EDGE_MAX_ITER_XPATH = EDGE_XPATH + "/settings/maxIter"
EDGE_CFL_NB_XPATH = EDGE_XPATH + "/settings/cflNumber/value"
EDGE_MG_LEVEL_XPATH = EDGE_XPATH + "/settings/multigridLevel"
EDGE_FIXED_CL_XPATH = EDGE_XPATH + "/fixedCL"
EDGE_ABOC_XPATH = EDGE_XPATH + "/boundary_condition"

# RANGE
RANGE_LD_RATIO_XPATH = CEASIOMPY_XPATH + "/ranges/lDRatio"

# TODO: remove those 4 when not use anymore
PASS_XPATH = CEASIOMPY_XPATH + "/weight/passengers"
CREW_XPATH = CEASIOMPY_XPATH + "/weight/crew"
PILOTS_XPATH = CEASIOMPY_XPATH + "/weight/crew/pilots"
CAB_CREW_XPATH = CEASIOMPY_XPATH + "/weight/crew/cabinCrewMembers"

# TODO: improve xpaths maybe remove some sub xpaths
WB_ROW_NB_XPATH = CEASIOMPY_XPATH + "/weight/passengers/rowNb"
WB_ABREAST_NB_XPATH = CEASIOMPY_XPATH + "/weight/passengers/abreastNb"
WB_PASSENGER_NB_XPATH = CEASIOMPY_XPATH + "/weight/passengers/passNb"
WB_PASSENGER_MASS_XPATH = CEASIOMPY_XPATH + "/weight/passengers/passMass"
WB_TOILET_NB_XPATH = CEASIOMPY_XPATH + "/weight/passengers/toiletNb"
WB_PEOPLE_MASS_XPATH = CEASIOMPY_XPATH + "/weight/passengers/peopleMass"
WB_CAB_CREW_NB_XPATH = CEASIOMPY_XPATH + "/weight/cab_crew/cabinCrewMemberNb"
WB_CREW_NB_XPATH = CEASIOMPY_XPATH + "/weight/crew/crewMemberNb"
WB_CREW_MASS_XPATH = CEASIOMPY_XPATH + "/weight/crew/crewMemberMass"

WB_MASS_LIMIT_XPATH = CEASIOMPY_XPATH + "/weight/massLimits"
WB_MAX_PAYLOAD_XPATH = WB_MASS_LIMIT_XPATH + "/maxPayload"
WB_MAX_FUEL_VOL_XPATH = WB_MASS_LIMIT_XPATH + "/maxFuelVol"

WB_SEAT_WIDTH_XPATH = GEOM_XPATH + "/seatWidth"
WB_SEAT_LENGTH_XPATH = GEOM_XPATH + "/seatLength"
WB_AISLE_WIDTH_XPATH = GEOM_XPATH + "/aisleWidth"
WB_FUSELAGE_THICK_XPATH = GEOM_XPATH + "/fuseThick"
WB_TOILET_LENGTH_XPATH = GEOM_XPATH + "/toiletLength"
WB_DOUBLE_FLOOR_XPATH = GEOM_XPATH + "/isDoubleFloor"

# pytornado
PYTORNADO_XPATH = "/cpacs/toolspecific/pytornado"
PYTORNADO_EXTRACT_LOAD_XPATH = PYTORNADO_XPATH + "/save_results/extractLoads"

# Stability
STABILITY_XPATH = CEASIOMPY_XPATH + "/stability"
STABILITY_AEROMAP_TO_ANALYZE_XPATH = STABILITY_XPATH + "/aeroMapToAnalyze"
CHECK_LONGITUDINAL_STABILITY_XPATH = STABILITY_XPATH + "/stabilityToCheck/longitudinal"
CHECK_DIRECTIONAL_STABILITY_XPATH = STABILITY_XPATH + "/stabilityToCheck/directional"
CHECK_LATERAL_STABILITY_XPATH = STABILITY_XPATH + "/stabilityToCheck/lateral"

# PYCYCLE
ENGINE_TYPE_XPATH = CEASIOMPY_XPATH + "/ThermoData"
ENGINE_BC = CEASIOMPY_XPATH + "/BC"

# AVL
AVL_XPATH = CEASIOMPY_XPATH + "/aerodynamics/avl"
AVL_AEROMAP_UID_XPATH = AVL_XPATH + "/aeroMapUID"
AVL_PLOT_XPATH = AVL_XPATH + "/SavePlots"
AVL_FUSELAGE_XPATH = AVL_XPATH + "/IntegrateFuselage"
AVL_VORTEX_DISTR_XPATH = AVL_XPATH + "/VortexDistribution"
