#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

# ===== RCE integration =====

RCE = {
    "name": "WeightConventional",
    "description": "Estimate weights of conventional aircraft",
    "exec": "pwd\npython weightconventional.py",
    "author": "Stefano Piccini",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()



# ----- Input -----

# User inputs ----
cpacs_inout.add_input(
    var_name='IS_DOUBLE_FLOOR',
    var_type=list,
    default_value=[0,1,2],
    unit=None,
    descr='0: no 2nd floor, 1: full 2nd floor (A380), 2: half 2nd floor (B747)',
    xpath=CEASIOM_XPATH + '/geometry/isDoubleFloor',
    gui=True,
    gui_name='Double deck',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='PILOT_NB',
    var_type=int,
    default_value=2,
    unit=None,
    descr='Number of pilot',
    xpath=CEASIOM_XPATH + '/weight/crew/pilots/pilotNb',
    gui=True,
    gui_name='Number of pilot',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MASS_PILOT',
    var_type=int,
    default_value=102,
    unit='[kg]',
    descr='Pilot mass',
    xpath=CEASIOM_XPATH + '/weight/crew/pilots/pilotMass',
    gui=False,
    gui_name='Pilot mass',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MASS_CABIN_CREW',
    var_type=int,
    default_value=68,
    unit='[kg]',
    descr='Cabin crew mass',
    xpath=CEASIOM_XPATH + '/weight/crew/cabinCrewMembers/cabinCrewMemberMass',
    gui=True,
    gui_name='Cabin crew mass',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MASS_PASS',
    var_type=int,
    default_value=105,
    unit='[kg]',
    descr='Passenger mass',
    xpath=CEASIOM_XPATH + '/weight/passengers/passMass',
    gui=True,
    gui_name='Passenger mass',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='PASS_PER_TOILET',
    var_type=int,
    default_value=50,
    unit='[pax/toilet]',
    descr='Number of passenger per toilet',
    xpath=CEASIOM_XPATH + '/weight/passengers/passPerToilet',
    gui=True,
    gui_name='Passenger/toilet',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MAX_PAYLOAD',
    var_type=float,
    default_value=0,
    unit='[kg]',
    descr='Maximum payload allowed, set 0 if equal to max passenger mass.',
    xpath=CEASIOM_XPATH + '/weight/massLimits/maxPayload',
    gui=True,
    gui_name='Max payload',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MAX_FUEL_VOL',
    var_type=float,
    default_value=0,
    unit='[l]',
    descr='Maximum fuel volume allowed [l]',
    xpath=CEASIOM_XPATH + '/weight/massLimits/maxFuelVol',
    gui=True,
    gui_name='Max Fuel volum',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='MASS_CARGO',
    var_type=float,
    default_value=0,
    unit='[kg]',
    descr='Cargo mass [kg]',
    xpath=AIRCRAFT_XPATH + '/model/analyses/massBreakdown/payload/mCargo/massDescription/mass',
    gui=True,
    gui_name='Mass cargo',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='FUEL_DENSITY',
    var_type=float,
    default_value=800,
    unit='[kg/m^3]',
    descr='Fuel density [kg/m^3]',
    xpath=CEASIOM_XPATH + '/fuels/density',
    gui=True,
    gui_name='Fuel density',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='TURBOPROP',
    var_type=bool,
    default_value=False,
    unit=None,
    descr='"True" only if the aircraft is a turboprop',
    xpath=CEASIOM_XPATH + '/propulsion/turboprop',
    gui=True,
    gui_name='Turboprop',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='RES_FUEL_PERC',
    var_type=float,
    default_value=0.06,
    unit='[-]',
    descr='percentage of the total fuel, unusable fuel_consumption (0 to 1)',
    xpath=CEASIOM_XPATH + '/fuels/resFuelPerc',
    gui=True,
    gui_name='RES_FUEL_PERC',
    gui_group='User inputs',
)

cpacs_inout.add_input(
    var_name='fuse_thick',
    var_type=float,
    default_value=6.63,
    unit='[%]',
    descr='Fuselage thickness, percentage of fuselage width',
    xpath=CEASIOM_XPATH + '/geometry/fuseThick',
    gui=True,
    gui_name='Fuselage thickness',
    gui_group='Fuselage',
)


# InsideDimensions ---

cpacs_inout.add_input(
    var_name='seat_length',
    var_type=float,
    default_value=0.74,
    unit='[m]',
    descr='Seats length',
    xpath=CEASIOM_XPATH + '/geometry/seatLength',
    gui=True,
    gui_name='Seat length',
    gui_group='Inside dimension',
)

cpacs_inout.add_input(
    var_name='seat_width',
    var_type=float,
    default_value=0.525,
    unit='[m]',
    descr='Seats width',
    xpath=CEASIOM_XPATH + '/geometry/seatWidth',
    gui=True,
    gui_name='Seat width',
    gui_group='Inside dimension',
)

cpacs_inout.add_input(
    var_name='aisle_width',
    var_type=float,
    default_value=0.42,
    unit='[m]',
    descr='Aisles width',
    xpath=CEASIOM_XPATH + '/geometry/aisleWidth',
    gui=True,
    gui_name='Aisles width',
    gui_group='Inside dimension',
)

cpacs_inout.add_input(
    var_name='toilet_length',
    var_type=float,
    default_value=1.9,
    unit='[m]',
    descr='Common space length',
    xpath=CEASIOM_XPATH + '/geometry/toiletLength',
    gui=True,
    gui_name='Toilet length',
    gui_group='Inside dimension',
)

cpacs_inout.add_input(
    var_name='cabin_length',
    var_type=float,
    default_value=0.0,
    unit='[m]',
    descr='Length of the aircraft cabin',
    xpath=CEASIOM_XPATH + '/geometry/cabinLength', # Xpath to check
    gui=False,
    gui_name='Cabin length',
    gui_group='Inside dimension',
)

# Is it relly an input?
# cpacs_inout.add_input(
#     var_name='cabin_width',
#     var_type=float,
#     default_value=0.0,
#     unit='[m]',
#     descr='Width of the aircraft cabin',
#     xpath=CEASIOM_XPATH + '/geometry/cabinWidth', # Xpath to check
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
#     xpath=CEASIOM_XPATH + '/geometry/cabinArea', # Xpath to check
#     gui=False,
#     gui_name='Cabin area',
#     gui_group='Inside dimension',
# )

"""

USER_ENGINE
NE
EN_NAME
en_mass

/cpacs/toolspecific/CEASIOMpy/propulsion/userEngineOption
/cpacs/toolspecific/CEASIOMpy/propulsion/engineNumber
cpacs/vehicles/engines/engine[..]/name
cpacs/vehicles/engines/engine/analyses/mass/mass

True if the User define the Engines in the EngineData class 	Belongs to the UserInputs Class
Number of Engines	Belongs to the EngineData class
Name of each engine	Belongs to the EngineData class, [..] stands for the number of the engine
Mass of a single mounted engine (Dry Weight)	Belongs to the EngineData class

"""

# ----- Output -----

cpacs_inout.add_output(
    var_name='maximum_take_off_mass',
    default_value=None,
    unit='[kg]',
    descr='Maximum take of mass',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/designMasses/mTOM/mass',
)

cpacs_inout.add_output(
    var_name='zero_fuel_mass',
    default_value=None,
    unit='[kg]',
    descr='Zero fuel mass',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/designMasses/mZFM/mass',
)

cpacs_inout.add_output(
    var_name='mass_fuel_max',
    default_value=None,
    unit='[kg]',
    descr='Maximum fuel mass',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/fuel/massDescription/mass',
)

cpacs_inout.add_output(
    var_name='mass_fuel_maxpass',
    default_value=None,
    unit='[kg]',
    descr='Maximum fuel mass with maximum payload',
    xpath=CEASIOM_XPATH+'/weight/passengers/fuelMassMaxpass/mass',
)

cpacs_inout.add_output(
    var_name='operating_empty_mass',
    default_value=None,
    unit='[kg]',
    descr='Operating empty mass',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/mOEM/massDescription/mass',
)

cpacs_inout.add_output(
    var_name='mass_payload',
    default_value=None,
    unit='[kg]',
    descr='Maximum payload mass',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/payload/massDescription/mass',
)

cpacs_inout.add_output(
    var_name='mass_cargo',
    default_value=None,
    unit='[kg]',
    descr='xtra payload mass in case of max fuel and total mass less than MTOM',
    xpath=AIRCRAFT_XPATH+'/model/analyses/massBreakdown/mCargo/massDescription/massCargo',
)

cpacs_inout.add_output(
    var_name='pass_nb',
    default_value=None,
    unit='[kg]',
    descr='Maximum number of passengers',
    xpath=CEASIOM_XPATH+'/weight/passengers/passNb',
)

cpacs_inout.add_output(
    var_name='cabin_crew_nb',
    default_value=None,
    unit='[-]',
    descr='Number of cabin crew members',
    xpath=CEASIOM_XPATH+'/weight/crew/cabinCrewMembers/cabinCrewMemberNb',
)

cpacs_inout.add_output(
    var_name='row_nb',
    default_value=None,
    unit='[-]',
    descr='Number of seat rows',
    xpath=CEASIOM_XPATH+'/weight/passengers/rowNb',
)

cpacs_inout.add_output(
    var_name='abreast_nb',
    default_value=None,
    unit='[-]',
    descr='Number of abreasts',
    xpath=CEASIOM_XPATH+'/weight/passengers/abreastNb',
)

cpacs_inout.add_output(
    var_name='aisle_nb',
    default_value=None,
    unit='[-]',
    descr='Number of aisles',
    xpath=CEASIOM_XPATH+'/weight/passengers/aisleNb',
)

cpacs_inout.add_output(
    var_name='toilet_nb',
    default_value=None,
    unit='[-]',
    descr='Number of toilets',
    xpath=CEASIOM_XPATH+'/weight/passengers/toiletNb',
)
