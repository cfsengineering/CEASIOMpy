#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "Range",
    "description": "Module to calculate the rage of an aircraft",
    "exec": "pwd\npython rangemain.py",
    "author": "Stefano Piccini",
    "email": "info@ceasiom.com",
}

CEASIOMPY_XPATH = '/cpacs/toolspecific/CEASIOMpy'
WEIGHT_XPATH = '/cpacs/toolspecific/CEASIOMpy/weight'
RANGE_XPATH = '/cpacs/toolspecific/CEASIOMpy/ranges'
FUEL_CONSUMPTION_XPATH = '/cpacs/toolspecific/CEASIOMpy/fuelConsumption'
MASSBREAKDOWN_XPATH = '/cpacs/vehicles/aircraft/model/analysis/massBreakdown'

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

### Masses

cpacs_inout.add_input(
    var_name='maximum_take_off_mass',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Maximum take off mass (MTOM)',
    cpacs_path=MASSBREAKDOWN_XPATH + '/designMasses/mTOM/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='mass_fuel_max',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Maximum fuel mass (MFM)',
    cpacs_path=MASSBREAKDOWN_XPATH + '/fuel/massDescription/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='mass_fuel_maxpass',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Fuel mass with maximum payload',
    cpacs_path=WEIGHT_XPATH + '/passengers/fuelMassMaxpass/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='operating_empty_mass',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Operating empty mass (OEM)',
    cpacs_path=MASSBREAKDOWN_XPATH + '/mOEM/massDescription/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='mass_payload',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Maximum payload mass',
    cpacs_path=MASSBREAKDOWN_XPATH + '/payload/massDescription/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

# Pilots, crew, passengers

cpacs_inout.add_input(
    var_name='pilot_nb',
    var_type=int,
    default_value=2,
    unit='-',
    descr='Number of pilots',
    cpacs_path=WEIGHT_XPATH + '/crew/pilots/pilotNb',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='cabin_crew_nb',
    var_type=int,
    default_value=None,
    unit='-',
    descr='Number of cabin crew members',
    cpacs_path=WEIGHT_XPATH + '/crew/cabinCrewMembers/cabinCrewMemberNB',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='MASS_PILOT',
    var_type=float,
    default_value=102.0,
    unit='kg',
    descr='Mass of one pilot',
    cpacs_path=WEIGHT_XPATH + '/crew/pilots/pilotMass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='MASS_CABIN_CREW',
    var_type=float,
    default_value=68.0,
    unit='kg',
    descr='Mass of one cabin crew member',
    cpacs_path=WEIGHT_XPATH + '/crew/cabinCrewMembers/cabinCrewMemberMass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='MASS_PASS',
    var_type=float,
    default_value=105.0,
    unit='kg',
    descr='Mass of on passenger',
    cpacs_path=WEIGHT_XPATH + '/passengers/passMass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

### Options

cpacs_inout.add_input(
    var_name='TURBOPROP',
    var_type=bool,
    default_value=False,
    unit=None,
    descr='"True" only if the aircraft is a turboprop',
    cpacs_path=CEASIOMPY_XPATH + '/propulsion/turboprop',
    gui=True,
    gui_name='Turboprop',
    gui_group='Options',
)

cpacs_inout.add_input(
    var_name='WINGLET',
    var_type=list,
    default_value=[0,1,2],
    unit=None,
    descr='Winglet option (0 = no winglets, 1 = normal winglets, 2 = high efficiency winglet for cruise',
    cpacs_path=CEASIOMPY_XPATH + '/geometry/winglet',
    gui=True,
    gui_name='Winglet type',
    gui_group='Options',
)


### Cruise

# This one should probalby be removed, at least use cruise_mach
cpacs_inout.add_input(
    var_name='cruise_speed',
    var_type=float,
    default_value=272,
    unit='m/s',
    descr='Cruise speed used to calculate the range',
    cpacs_path=CEASIOMPY_XPATH + '/ranges/cruiseSpeed',
    gui=True,
    gui_name='Speed',
    gui_group='Cruise',
)

cpacs_inout.add_input(
    var_name='TSFC_CRUISE',
    var_type=float,
    default_value=0.5,
    unit='1/h',
    descr='Thrust specific fuel consumption on cruise',
    cpacs_path=CEASIOMPY_XPATH + '/propulsion/tSFC/tsfcCruise',
    gui=True,
    gui_name='TSFC',
    gui_group='Cruise',
)

cpacs_inout.add_input(
    var_name='LD',
    var_type=float,
    default_value=17.0,
    unit='-',
    descr='On cruise efficiency, CL/CD ratio',
    cpacs_path=CEASIOMPY_XPATH + '/ranges/lDRatio',
    gui=True,
    gui_name='CL/CD',
    gui_group='Cruise',
)

### Loiter
cpacs_inout.add_input(
    var_name='TSFC_LOITER',
    var_type=float,
    default_value=0.4,
    unit='1/h',
    descr='Thrust specific fuel consumption on loiter',
    cpacs_path=CEASIOMPY_XPATH + '/propulsion/tSFC/tsfcLoiter',
    gui=True,
    gui_name='TSFC',
    gui_group='Loiter',
)

cpacs_inout.add_input(
    var_name='LOITER_TIME',
    var_type=float,
    default_value=30.0,
    unit='min', # TODO: change by seconde?
    descr='Loiter time to include in the range calculation',
    cpacs_path=CEASIOMPY_XPATH + '/ranges/loiterTime',
    gui=True,
    gui_name='Duration',
    gui_group='Loiter',
)

### Fuel

cpacs_inout.add_input(
    var_name='FUEL_DENSITY',
    var_type=float,
    default_value=0.8,
    unit='kg/m^3',
    descr='Fuel density',
    cpacs_path='/cpacs/vehicles/fuels/fuel/density',
    gui=True,
    gui_name='Density',
    gui_group='Fuel',
)

cpacs_inout.add_input(
    var_name='RES_FUEL_PERC',
    var_type=float,
    default_value=0.1,
    unit='-',
    descr='Unusable fuel percentage [0 - 1]',
    cpacs_path=CEASIOMPY_XPATH + '/fuels/resFuelPerc',
    gui=True,
    gui_name='Unusable fuel',
    gui_group='Fuel',
)


# ----- Output -----

cpacs_inout.add_output(
    var_name='mf_for_climb',
    default_value=None,
    unit='kg',
    descr='Fuel used for climb',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelForClimb',
)

cpacs_inout.add_output(
    var_name='mf_for_cruise',
    default_value=None,
    unit='kg',
    descr='Fuel used for Cruise',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelForCruise',
)

cpacs_inout.add_output(
    var_name='mf_for_loiter',
    default_value=None,
    unit='kg',
    descr='Fuel used for loiter',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelForLoiter',
)

cpacs_inout.add_output(
    var_name='mf_for_landing',
    default_value=None,
    unit='kg',
    descr='Fuel used for landing',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelForLanding',
)

cpacs_inout.add_output(
    var_name='mf_after_land',
    default_value=None,
    unit='kg',
    descr='Fuel remained after landing',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelRemained',
)

cpacs_inout.add_output(
    var_name='mf_for_to',
    default_value=None,
    unit='kg',
    descr='Fuel used for taking off',
    cpacs_path=FUEL_CONSUMPTION_XPATH + '/fuelForTakeOff',
)

cpacs_inout.add_output(
    var_name='ranges[0]',
    default_value=None,
    unit='kg',
    descr='Range with max payload and fuel to reach MTOM',
    cpacs_path=RANGE_XPATH + '/rangeMaxP/rangeDescription/range',
)

cpacs_inout.add_output(
    var_name='ranges[1]',
    default_value=None,
    unit='kg',
    descr='Range with max fuel mass and remaining payload to reach MTOM',
    cpacs_path=RANGE_XPATH + '/rangeMaxF/rangeDescription/range',
)

cpacs_inout.add_output(
    var_name='ranges[2]',
    default_value=None,
    unit='kg',
    descr='Range with max fuel and no payload',
    cpacs_path=RANGE_XPATH + '/rangeMaxMaximum/rangeDescription/range',
)


cpacs_inout.add_output(
    var_name='payloads[0]',
    default_value=None,
    unit='kg',
    descr='Payload corresponding to range[0] (max payload)',
    cpacs_path=RANGE_XPATH + '/rangeMaxMaximum/rangeDescription/payload',
)

cpacs_inout.add_output(
    var_name='payloads[1]',
    default_value=None,
    unit='kg',
    descr='Payload corresponding to range[1]',
    cpacs_path=RANGE_XPATH + '/rangeMaxMaximum/rangeDescription/payload',
)

cpacs_inout.add_output(
    var_name='payloads[2]',
    default_value=None,
    unit='kg',
    descr='Payload = 0 kg',
    cpacs_path=RANGE_XPATH + '/rangeMaxMaximum/rangeDescription/payload',
)

cpacs_inout.add_output(
    var_name='cabin_crew_nb',
    default_value=None,
    unit='-',
    descr='Number of cabin crew members',
    cpacs_path=WEIGHT_XPATH + '/crew/cabinCrewMembers/cabinCrewMemberNB',
)
