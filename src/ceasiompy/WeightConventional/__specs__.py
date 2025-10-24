"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of WeightConventional.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.WeightConventional import INCLUDE_GUI

from ceasiompy.utils.guixpaths import (
    FUEL_XPATH,
    GEOM_XPATH,
    PROP_XPATH,
    WB_ROW_NB_XPATH,
    WB_CREW_NB_XPATH,
    WB_TOILET_NB_XPATH,
    WB_CREW_MASS_XPATH,
    WB_ABREAST_NB_XPATH,
    WB_CAB_CREW_NB_XPATH,
    WB_MAX_PAYLOAD_XPATH,
    WB_PEOPLE_MASS_XPATH,
    WB_DOUBLE_FLOOR_XPATH,
    WB_MAX_FUEL_VOL_XPATH,
    WB_PASSENGER_NB_XPATH,
    WB_PASSENGER_MASS_XPATH,
)
from ceasiompy.utils.cpacsxpaths import (
    MOEM_XPATH,
    MTOM_XPATH,
    MZFM_XPATH,
    FUEL_MASS_XPATH,
    MASS_CARGO_XPATH,
    PAYLOAD_MASS_XPATH,
    MASSBREAKDOWN_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="is_double_floor",
    var_type=list,
    default_value=[0, 1, 2],
    unit=None,
    descr="0: no 2nd floor, 1: full 2nd floor (A380), 2: half 2nd floor (B747)",
    xpath=WB_DOUBLE_FLOOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Double deck",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="max_payload",
    var_type=float,
    default_value=0,
    unit="[kg]",
    descr="Maximum payload allowed, set 0 if equal to max passenger mass.",
    xpath=WB_MAX_PAYLOAD_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Max payload",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="max_fuel_volume",
    var_type=float,
    default_value=0,
    unit="[l]",
    descr="Maximum fuel volume allowed [l]",
    xpath=WB_MAX_FUEL_VOL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Max Fuel volum",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="mass_cargo",
    var_type=float,
    default_value=0,
    unit="[kg]",
    descr="Cargo mass [kg]",
    xpath=MASS_CARGO_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Mass cargo",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="fuel_density",
    var_type=float,
    default_value=800,
    unit="[kg/m^3]",
    descr="Fuel density [kg/m^3]",
    xpath=FUEL_XPATH + "/density",
    gui=INCLUDE_GUI,
    gui_name="Fuel density",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="turboprop",
    var_type=bool,
    default_value=False,
    unit=None,
    descr='"True" only if the aircraft is a turboprop',
    xpath=PROP_XPATH + "/turboprop",
    gui=INCLUDE_GUI,
    gui_name="Turboprop",
    gui_group="User inputs",
)

cpacs_inout.add_input(
    var_name="fuse_thick",
    var_type=float,
    default_value=6.63,
    unit="[%]",
    descr="Fuselage thickness, percentage of fuselage width",
    xpath=GEOM_XPATH + "/fuseThick",
    gui=INCLUDE_GUI,
    gui_name="Fuselage thickness",
    gui_group="Fuselage",
)

# InsideDimensions ---
cpacs_inout.add_input(
    var_name="seat_length",
    var_type=float,
    default_value=0.74,
    unit="[m]",
    descr="Seats length",
    xpath=GEOM_XPATH + "/seatLength",
    gui=INCLUDE_GUI,
    gui_name="Seat length",
    gui_group="Inside dimension",
)

cpacs_inout.add_input(
    var_name="seat_width",
    var_type=float,
    default_value=0.525,
    unit="[m]",
    descr="Seats width",
    xpath=GEOM_XPATH + "/seatWidth",
    gui=INCLUDE_GUI,
    gui_name="Seat width",
    gui_group="Inside dimension",
)

cpacs_inout.add_input(
    var_name="aisle_width",
    var_type=float,
    default_value=0.42,
    unit="[m]",
    descr="Aisles width",
    xpath=GEOM_XPATH + "/aisleWidth",
    gui=INCLUDE_GUI,
    gui_name="Aisles width",
    gui_group="Inside dimension",
)

cpacs_inout.add_input(
    var_name="toilet_length",
    var_type=float,
    default_value=1.9,
    unit="[m]",
    descr="Common space length",
    xpath=GEOM_XPATH + "/toiletLength",
    gui=INCLUDE_GUI,
    gui_name="Toilet length",
    gui_group="Inside dimension",
)

cpacs_inout.add_input(
    var_name="cabin_length",
    var_type=float,
    default_value=0.0,
    unit="[m]",
    descr="Length of the aircraft cabin",
    xpath=GEOM_XPATH + "/cabinLength",  # Xpath to check
    gui=False,
    gui_name="Cabin length",
    gui_group="Inside dimension",
)

# Is it really an input?
# cpacs_inout.add_input(
#     var_name='cabin_width',
#     var_type=float,
#     default_value=0.0,
#     unit='[m]',
#     descr='Width of the aircraft cabin',
#     xpath=GEOM_XPATH+'/cabinWidth', # Xpath to check
#     gui=False,
#     gui_name='Cabin width',
#     gui_group='Inside dimension',
# )

# cpacs_inout.add_input(
#     var_name='cabin_area',
#     var_type=float,
#     default_value=None,
#     unit='[m^2]',
#     descr='Area of the aircraft cabin',
#     xpath=GEOM_XPATH+'/cabinArea', # Xpath to check
#     gui=False,
#     gui_name='Cabin area',
#     gui_group='Inside dimension',
# )


# USER_ENGINE
# NE
# EN_NAME
# en_mass

# /cpacs/toolspecific/CEASIOMpy/propulsion/userEngineOption
# /cpacs/toolspecific/CEASIOMpy/propulsion/engineNumber
# cpacs/vehicles/engines/engine[..]/name
# cpacs/vehicles/engines/engine/analyses/mass/mass

# True if the User define the Engines in the EngineData class 	Belongs to the UserInputs Class
# Number of Engines	Belongs to the EngineData class
# Name of each engine	Belongs to the EngineData class, [..] stands for the number of the engine
# Mass of a single mounted engine (Dry Weight)	Belongs to the EngineData class


# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="mtom",
    default_value=None,
    unit="[kg]",
    descr="Maximum take of mass",
    xpath=MTOM_XPATH,
)

cpacs_inout.add_output(
    var_name="oem",
    default_value=None,
    unit="[kg]",
    descr="Operating empty mass",
    xpath=MOEM_XPATH,
)

cpacs_inout.add_output(
    var_name="zfm",
    default_value=None,
    unit="[kg]",
    descr="Zero fuel mass",
    xpath=MZFM_XPATH,
)

cpacs_inout.add_output(
    var_name="mass_fuel_max_passenger",
    default_value=None,
    unit="[kg]",
    descr="Maximum fuel mass with maximum payload",
    xpath=FUEL_MASS_XPATH,
)

cpacs_inout.add_output(
    var_name="payload_mass",
    default_value=None,
    unit="[kg]",
    descr="Maximum payload mass",
    xpath=PAYLOAD_MASS_XPATH,
)

cpacs_inout.add_output(
    var_name="mass_fuel_max",
    default_value=None,
    unit="[kg]",
    descr="Maximum fuel mass",
    xpath=MASSBREAKDOWN_XPATH + "/fuel/massDescription/mass",
)

cpacs_inout.add_output(
    var_name="passenger_nb",
    default_value=None,
    unit="[-]",
    descr="Maximum number of passengers",
    xpath=WB_PASSENGER_NB_XPATH,
)

cpacs_inout.add_output(
    var_name="passenger_mass",
    default_value=None,
    unit="[kg]",
    descr="Mass all of passengers",
    xpath=WB_PASSENGER_MASS_XPATH,
)

cpacs_inout.add_output(
    var_name="cabin_crew_nb",
    default_value=None,
    unit="[-]",
    descr="Number of cabin crew members",
    xpath=WB_CAB_CREW_NB_XPATH,
)

cpacs_inout.add_output(
    var_name="crew_nb",
    default_value=None,
    unit="[-]",
    descr="Number of cabin crew members (pilot and cabin crew)",
    xpath=WB_CREW_NB_XPATH,
)

cpacs_inout.add_output(
    var_name="crew_mass",
    default_value=None,
    unit="[kg]",
    descr="Mass of all cabin crew members (pilot and cabin crew)",
    xpath=WB_CREW_MASS_XPATH,
)

cpacs_inout.add_output(
    var_name="people_mass",
    default_value=None,
    unit="[kg]",
    descr="Mass of all people (pilot, cabin crew and passengers)",
    xpath=WB_PEOPLE_MASS_XPATH,
)

cpacs_inout.add_output(
    var_name="row_nb",
    default_value=None,
    unit="[-]",
    descr="Number of seat rows",
    xpath=WB_ROW_NB_XPATH,
)

cpacs_inout.add_output(
    var_name="abreast_nb",
    default_value=None,
    unit="[-]",
    descr="Number of abreasts",
    xpath=WB_ABREAST_NB_XPATH,
)

cpacs_inout.add_output(
    var_name="toilet_nb",
    default_value=None,
    unit="[-]",
    descr="Number of toilets",
    xpath=WB_TOILET_NB_XPATH,
)
