#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH

SKINFRICTION_PATH = CEASIOM_XPATH + '/aerodynamics/skinFriction'

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
    var_name='',
    var_type=list,
    default_value=None,
    descr='To which aeroMap the skin priction coef shoud be added',
    xpath=SKINFRICTION_PATH + '/aeroMapToCalculate',
    gui=True,
    gui_name='__AEROMAP_CHECHBOX',
)

cpacs_inout.add_input(
    var_name='wetted_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Wetted area of the aircraft (calculated by SU2)',
    xpath=CEASIOM_XPATH + '/geometry/analysis/wettedArea',
    gui=False,
    gui_name='Wetted Area',
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='',
    var_type=bool,
    default_value=False,
    unit=None,
    descr='Delete orignal aeroMap once skin friction coefficient has been added',
    xpath=SKINFRICTION_PATH + '/deleteOriginal',
    gui=True,
    gui_name='Delete Orignal',
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    default_value=0.78,
    unit='-',
    descr='Aircraft cruise Mach number',
    xpath=CEASIOM_XPATH + '/ranges/cruiseMach',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    default_value=12000,
    unit='m',
    descr='Aircraft cruise altitude',
    xpath=CEASIOM_XPATH + '/ranges/cruiseAltitude',
)

# ===== Output =====

cpacs_inout.add_output(
    var_name='cd0',
    default_value=None,
    unit='1',
    descr='Skin friction drag coefficient',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/skinFriction/cd0',
)

cpacs_inout.add_output(
    var_name='main_wing_area',
    default_value=None,
    unit='m^2',
    descr='Wing area of the main (largest) wing',
    xpath=CEASIOM_XPATH + '/geometry/analyses/wingArea',
)

cpacs_inout.add_output(
    var_name='main_wing_span',
    default_value=None,
    unit='m',
    descr='Wing span of the main (largest) wing',
    xpath=CEASIOM_XPATH + '/geometry/analyses/wingSpan',
)

cpacs_inout.add_output(
    var_name='new_aeromap_to_plot',
    default_value=None,
    unit='m',
    descr='List of aeroMap to plot',
    xpath=CEASIOM_XPATH + '/aerodynamics/plotAeroCoefficient/aeroMapToPlot',
)
