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
| modification: 2024-01-05 (Mengmeng Zhang, added M-Edge XPATHs )
| Modified: Leon Deligny
| Date: 25 March 2025

# TODO: Someome please Organize these paths

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy import log

# =================================================================================================
#   CSTS
# =================================================================================================

# Header
AIRCRAFT_NAME_XPATH = "/cpacs/header/name"

# model
REF_XPATH = "/cpacs/vehicles/aircraft/model/reference"
FUSELAGES_XPATH = "/cpacs/vehicles/aircraft/model/fuselages"
WINGS_XPATH = "/cpacs/vehicles/aircraft/model/wings"
PYLONS_XPATH = "/cpacs/vehicles/aircraft/model/enginePylons"
ENGINES_XPATH = "/cpacs/vehicles/aircraft/model/engines"
AIRFOILS_XPATH = "/cpacs/vehicles/profiles/wingAirfoils"

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
PROPELLER_THRUST_XPATH = PROP_XPATH + "/propeller/thrust"
PROPELLER_BLADE_LOSS_XPATH = PROP_XPATH + "/propeller/blade/loss"
AEROMAP_TO_EXPORT_XPATH = CEASIOMPY_XPATH + "/export/aeroMapToExport"

RANGE_XPATH = CEASIOMPY_XPATH + "/ranges"
RANGE_CRUISE_MACH_XPATH = RANGE_XPATH + "/CruiseMach"
RANGE_CRUISE_ALT_XPATH = RANGE_XPATH + "/CruiseAltitude"
WEIGHT_XPATH = CEASIOMPY_XPATH + "/weight"

CLCALC_XPATH = CEASIOMPY_XPATH + "/aerodynamics/clCalculation"
PLOT_XPATH = CEASIOMPY_XPATH + "/aerodynamics/plotAeroCoefficient"
AEROMAP_TO_PLOT_XPATH = PLOT_XPATH + "/aeroMapToPlot"

SF_XPATH = CEASIOMPY_XPATH + "/aerodynamics/skinFriction"

WETTED_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wettedArea"
WING_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingArea"
WING_SPAN_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingSpan"

SMTRAIN_XPATH = CEASIOMPY_XPATH + "/surrogateModel"
SMUSE_XPATH = CEASIOMPY_XPATH + "/surrogateModelUse"

STATICSTABILITY_XPATH = CEASIOMPY_XPATH + "/StaticStability"
STATICSTABILITY_LR_XPATH = STATICSTABILITY_XPATH + "/LinearRegression"

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

# CPACS2SUMO
CPACS2SUMO_XPATH = CEASIOMPY_XPATH + "/CPACS2SUMO"
CPACS2SUMO_SUMO_GUI_XPATH = CPACS2SUMO_XPATH + "/GUI"

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
GMSH_MESH_SIZE_CTRLSURFS_XPATH = GMSH_XPATH + "/mesh_size/controlsurfaces/value"
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
GMSH_SURFACE_MESH_SIZE_XPATH = GMSH_XPATH + "min_max_mesh_factor"
GMSH_FEATURE_ANGLE_XPATH = GMSH_XPATH + "/feature_angle"
GMSH_CTRLSURF_ANGLE_XPATH = GMSH_XPATH + "/DeflectionAngle"

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

SU2_CONTROL_SURF_XPATH = SU2_XPATH + "/ControlSurfaces"
SU2_CONTROL_SURF_BOOL_XPATH = SU2_CONTROL_SURF_XPATH + "/Bool"
SU2_CONTROL_SURF_ANGLE_XPATH = SU2_CONTROL_SURF_XPATH + "/Angle"
SU2_DEF_MESH_XPATH = SU2_XPATH + "/availableDeformedMesh"

SU2_ACTUATOR_DISK_XPATH = SU2_XPATH + "/options/includeActuatorDisk"
SU2_CONFIG_RANS_XPATH = SU2_XPATH + "/options/config_type"

SU2_DYNAMICDERIVATIVES_XPATH = SU2_XPATH + "/DynamicDerivatives"
SU2_DYNAMICDERIVATIVES_BOOL_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Bool"
SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/TimeSize"
SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Amplitude"
SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/AngularFrequency"
SU2_DYNAMICDERIVATIVES_INNERITER_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/InnerIter"
SU2_DYNAMICDERIVATIVES_DATA_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Data"
SU2_CEASIOMPYDATA_XPATH = SU2_XPATH + "/CeasiompyData"
SU2_AIRCRAFT_XPATH = SU2_XPATH + "/Aircraft"

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
PYTORNADO_XPATH = CEASIOMPY_XPATH + "/pytornado"
PYTORNADO_EXTRACT_LOAD_XPATH = PYTORNADO_XPATH + "/save_results/extractLoads"

# Stability
STABILITY_XPATH = CEASIOMPY_XPATH + "/stability"
STABILITY_AEROMAP_TO_ANALYZE_XPATH = STABILITY_XPATH + "/aeroMapToAnalyze"
CHECK_STABILITY_XPATH = STABILITY_XPATH + "/stabilityToCheck"

# PYCYCLE
ENGINE_TYPE_XPATH = CEASIOMPY_XPATH + "/ThermoData"
ENGINE_BC = CEASIOMPY_XPATH + "/BC"
ENGINE_BC_TEMPERATUREOUTLET_XPATH = ENGINE_BC + "/TemperatureOutlet"
ENGINE_BC_PRESSUREOUTLET_XPATH = ENGINE_BC + "/PressureOutlet"

# AVL
AVL_XPATH = CEASIOMPY_XPATH + "/avl"
AVL_ROTRATES_XPATH = AVL_XPATH + "/RotationRates"
AVL_AEROMAP_UID_XPATH = AVL_XPATH + "/aeroMapUID"
AVL_TABLE_XPATH = AVL_XPATH + "/Table"
AVL_CTRLTABLE_XPATH = AVL_XPATH + "/CtrlTable"
AVL_PLOT_XPATH = AVL_XPATH + "/SavePlots"
AVL_FUSELAGE_XPATH = AVL_XPATH + "/IntegrateFuselage"
AVL_VORTEX_DISTR_XPATH = AVL_XPATH + "/VortexDistribution"
AVL_NCHORDWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nchordwise"
AVL_NSPANWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nspanwise"
AVL_DISTR_XPATH = AVL_VORTEX_DISTR_XPATH + "/Distribution"
AVL_PLOTLIFT_XPATH = AVL_XPATH + "/PlotLift"
AVL_NB_CPU_XPATH = AVL_XPATH + "NbCPU"
AVL_CTRLSURF_ANGLES_XPATH = AVL_XPATH + "/ControlSurfaceAngles"

# DYNAMICSTABILITY
DYNAMICSTABILITY_XPATH = CEASIOMPY_XPATH + "/DynamicStability"
DYNAMICSTABILITY_AIRCRAFT_XPATH = DYNAMICSTABILITY_XPATH + "/Aircraft"
DYNAMICSTABILITY_CEASIOMPYDATA_XPATH = DYNAMICSTABILITY_XPATH + "/CeasiompyData"
DYNAMICSTABILITY_AEROMAP_UID_XPATH = DYNAMICSTABILITY_XPATH + "/aeroMapUID"
DYNAMICSTABILITY_NCHORDWISE_XPATH = DYNAMICSTABILITY_XPATH + "/NChordwise"
DYNAMICSTABILITY_NSPANWISE_XPATH = DYNAMICSTABILITY_XPATH + "/NSpanwise"
DYNAMICSTABILITY_WINGS_XPATH = DYNAMICSTABILITY_XPATH + "/WingSelection"
DYNAMICSTABILITY_VISUALIZATION_XPATH = DYNAMICSTABILITY_XPATH + "/Visualization"
DYNAMICSTABILITY_CGRID_XPATH = DYNAMICSTABILITY_XPATH + "/CGrid"
DYNAMICSTABILITY_SOFTWARE_XPATH = DYNAMICSTABILITY_XPATH + "/Software"
DYNAMICSTABILITY_MACHLIST_XPATH = DYNAMICSTABILITY_XPATH + "/Mach"

# CPACSUPDATER
CPACSUPDATER_XPATH = CEASIOMPY_XPATH + "/CPACSUpdater"
CPACSUPDATER_CTRLSURF_XPATH = CPACSUPDATER_XPATH + "/CtrlSurf"
CPACSUPDATER_ADD_CTRLSURFACES_XPATH = CEASIOMPY_XPATH + "/AddControlSurfaces"
CPACSUPDATER_CPACSCREATOR_XPATH = CPACSUPDATER_XPATH + "/CPACSCreator"

# DATABASE
DATABASE_XPATH = CEASIOMPY_XPATH + "/Database"
DATABASE_STOREDATA_XPATH = DATABASE_XPATH + "/StoreData"

# FramAT
FRAMAT_XPATH = CEASIOMPY_XPATH + "/structure/FramAT"
FRAMAT_MATERIAL_XPATH = FRAMAT_XPATH + "/MaterialProperties"
FRAMAT_SECTION_XPATH = FRAMAT_XPATH + "/SectionProperties"
FRAMAT_MESH_XPATH = FRAMAT_XPATH + "/BeamMesh"
FRAMAT_RESULTS_XPATH = FRAMAT_XPATH + "/Results"
# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
