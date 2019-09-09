#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH


# ===== RCE =====

RCE = {
    "name": "SkinFriction",
    "description": "Calculate skin friction drag coefficent",
    "exec": "pwd\npython skinfriction.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}


cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
    var_name='wetted_area',
    default_value=None,
    unit='m^2',
    descr='Wetted area of the aircraft (calculated by SU2)',
    cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wettedArea',
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    default_value=0.78,
    unit='-',
    descr='Aircraft cruise Mach number',
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseMach',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    default_value=12000,
    unit='m',
    descr='Aircraft cruise altitude',
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseAltitude',
)

# ===== Output =====

cpacs_inout.add_output(
    var_name='cd0',
    default_value=None,
    unit='1',
    descr='Skin friction drag coefficient',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/skinFriction/cd0',
)

cpacs_inout.add_output(
    var_name='wing_area',
    default_value=None,
    unit='m^2',
    descr='Wing area of the main (largest) wing',
    cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingArea',
)

cpacs_inout.add_output(
    var_name='wing_span',
    default_value=None,
    unit='m',
    descr='Wing span of the main (largest) wing',
    cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingSpan',
)


# ===== GUI =====

SKINFRICTION_PATH = CEASIOM_XPATH + '/aerodynamics/skinFriction'

GUI_SETTINGS = {
    'AeroMap name': ['', list, None, SKINFRICTION_PATH + '/aeroMapToCalculate', 'To which aeroMap the skin priction coef shoud be added.'],
    'Delete Orignal': [False, bool, None, SKINFRICTION_PATH + '/deleteOriginal', 'Delete orignal aeroMap once skin friction coefficient has been added.'],
    'Wetted Area': [None, float, 'm^2', CEASIOM_XPATH + '/geometry/analysis/wettedArea', 'Aircraft total wetted area']
}
