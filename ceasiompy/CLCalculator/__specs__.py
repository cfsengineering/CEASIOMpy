#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.xpath import (REF_XPATH, CLCALC_XPATH, SU2_XPATH)

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
    var_name='mass_type',
    var_type=list,
    default_value= ['mTOM', 'mZFM', 'Custom','% fuel mass'],
    unit=None,
    descr='Type of mass to use for CL calculation',
    xpath=CLCALC_XPATH +'/massType',
    gui=True,
    gui_name='Type',
    gui_group='Mass'
)

cpacs_inout.add_input(
    var_name='custom_mass',
    var_type=float,
    default_value=0.0,
    unit='kg',
    descr='Mass value if Custom is selected',
    xpath=CLCALC_XPATH +'/customMass',
    gui=True,
    gui_name='Custom mass',
    gui_group='Mass',
)

cpacs_inout.add_input(
    var_name='percent_fuel_mass',
    var_type=float,
    default_value=100,
    unit='-',
    descr='Percentage of fuel mass between mTOM and mZFM, if % fuel mass is selected',
    xpath=CLCALC_XPATH + '/percentFuelMass',
    gui=True,
    gui_name='Percent fuel mass',
    gui_group='Mass',
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    var_type=float,
    default_value=0.78,
    unit='1',
    descr='Aircraft cruise Mach number',
    xpath=CLCALC_XPATH + '/cruiseMach',
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
    xpath=CLCALC_XPATH + '/cruiseAltitude',
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
    xpath=CLCALC_XPATH + '/loadFactor',
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
    xpath=REF_XPATH + '/area',
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
    xpath=SU2_XPATH + '/targetCL',
)

cpacs_inout.add_output(
    var_name='fixed_cl',
    default_value=None,
    unit='-',
    descr='FIXED_CL_MODE parameter for SU2',
    xpath=SU2_XPATH + '/fixedCL',
)
