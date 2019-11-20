#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "CLCalculator",
    "description": "Calculate required Lift coefficient to fly",
    "exec": "pwd\npython clcalculator.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
    var_name='mtom',
    var_type=float,
    default_value=None,
    unit='kg',
    descr='Maximum take off mass (MTOM)',
    xpath=AIRCRAFT_XPATH + '/model/analyses/massBreakdown/designMasses/mTOM/mass',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    var_type=float,
    default_value=0.78,
    unit='1',
    descr='Aircraft cruise Mach number',
    xpath=CEASIOM_XPATH + '/ranges/cruiseMach',
    gui=True,
    gui_name='Mach',
    gui_group='Cruise',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    var_type=float,
    default_value=12000.0,
    unit='m',
    descr='Aircraft cruise altitude',
    xpath=CEASIOM_XPATH + '/ranges/cruiseAltitude',
    gui=True,
    gui_name='Altitude',
    gui_group='Cruise',
)

cpacs_inout.add_input(
    var_name='load_fact',
    var_type=float,
    default_value=1.05,
    unit='1',
    descr='Aircraft cruise altitude',
    xpath=CEASIOM_XPATH + '/ranges/loadFactor',
    gui=True,
    gui_name='Load Factor',
    gui_group='Cruise',
)

cpacs_inout.add_input(
    var_name='ref_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Aircraft reference area',
    xpath=AIRCRAFT_XPATH + '/model/reference/area',
    gui=False,
    gui_name=None,
    gui_group=None,
)


#===== Output =====

cpacs_inout.add_output(
    var_name='target_cl',
    default_value=None,
    unit='1',
    descr='Value of CL to achieve to have a level flight with the given conditions',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/targetCL',
)

cpacs_inout.add_output(
    var_name='fixed_cl',
    default_value=None,
    unit='-',
    descr='FIXED_CL_MODE parameter for SU2',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/fixedCL',

)
