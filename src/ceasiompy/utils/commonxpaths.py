"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of CPACS xpath which are used in CEASIOMpy, if possible base xpath must be
called only from here to avoid mistakes.
XPath may be changed from here to avoid mistakes, but if it is the case, be careful to also change
xpath and field name in all the test CPACS files, which are in the CEASIOMpy repository.

Note:
    This contains only COMMON xpaths,
    please do NOT add specific xpaths of your module in here.
    You can always add specific xpaths in the __init__.py of your module.

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
AREA_XPATH = "/cpacs/vehicles/aircraft/model/reference/area"
LENGTH_XPATH = "/cpacs/vehicles/aircraft/model/reference/length"

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
RS_XPATH = PLOT_XPATH + "/responseSurface"
AEROMAP_TO_PLOT_XPATH = PLOT_XPATH + "/aeroMapToPlot"
USED_SU2_MESH_XPATH = CEASIOMPY_XPATH + "/MeshPath"

SF_XPATH = CEASIOMPY_XPATH + "/aerodynamics/skinFriction"

WETTED_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wettedArea"
WING_AREA_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingArea"
WING_SPAN_XPATH = CEASIOMPY_XPATH + "/geometry/analysis/wingSpan"

# SMTRAIN_XPATH = CEASIOMPY_XPATH + "/surrogateModel"
# SMUSE_XPATH = CEASIOMPY_XPATH + "/surrogateModelUse"

STATICSTABILITY_XPATH = CEASIOMPY_XPATH + "/StaticStability"
STATICSTABILITY_LR_XPATH = STATICSTABILITY_XPATH + "/LinearRegression"

OPTWKDIR_XPATH = CEASIOMPY_XPATH + "/filesPath/optimPath"
SMFILE_XPATH = CEASIOMPY_XPATH + "/filesPath/SMpath"
SU2MESH_XPATH = CEASIOMPY_XPATH + "/filesPath/su2Mesh"
EDGE_MESH_XPATH = CEASIOMPY_XPATH + "/filesPath/edgeMesh"

WKDIR_XPATH = CEASIOMPY_XPATH + "/filesPath/wkdirPath"

SM_XPATH = CEASIOMPY_XPATH + "/filesPath/surrogateModelPath"
SUGGESTED_POINTS_XPATH = CEASIOMPY_XPATH + "/filesPath/suggestedPointsPath"
SM_PREDICTIONS = CEASIOMPY_XPATH + "/filesPath/predictionsDatasetPath"

# Propulsion
TURBOPROP_XPATH = PROP_XPATH + "/turboprop"

# SUMO
SUMO_OUTPUT_MESH_FORMAT_XPATH = MESH_XPATH + "sumoOptions/format"
SUMO_REFINE_LEVEL_XPATH = MESH_XPATH + "/sumoOptions/refinementLevel"

SPECIFIED_SUMOFILE_XPATH = CEASIOMPY_XPATH + "/SUMOAutoMesh" + "/specifiedSumoPath"

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

# PYCYCLE
ENGINE_TYPE_XPATH = CEASIOMPY_XPATH + "/ThermoData"
ENGINE_BC = CEASIOMPY_XPATH + "/BC"
ENGINE_BC_TEMPERATUREOUTLET_XPATH = ENGINE_BC + "/TemperatureOutlet"
ENGINE_BC_PRESSUREOUTLET_XPATH = ENGINE_BC + "/PressureOutlet"

# FramAT
FRAMAT_XPATH = CEASIOMPY_XPATH + "/structure/FramAT"
FRAMAT_MATERIAL_XPATH = FRAMAT_XPATH + "/MaterialProperties"
FRAMAT_SECTION_XPATH = FRAMAT_XPATH + "/SectionProperties"
FRAMAT_MESH_XPATH = FRAMAT_XPATH + "/BeamMesh"
FRAMAT_RESULTS_XPATH = FRAMAT_XPATH + "/Results"

# AeroFrame
AEROFRAME_XPATH = CEASIOMPY_XPATH + "/aeroelasticity/AeroFrame"
AEROFRAME_SETTINGS = AEROFRAME_XPATH + "/Settings"

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
