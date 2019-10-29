#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH

AEROMAPS_PATH = CEASIOM_XPATH +  '/cpacs/vehicles/aircraft/model/analyses/aeroperormance/aeroMapUID'

# ===== RCE integration =====

RCE = {
    "name": "StabilityStatic",
    "description": "Determine if a vehicle is statically stable or not  ",
    "exec": "pwd\npython stabilitystatic.py",
    "author": "Loïc Verdier",
    "email": "loic.verdier@epfl.ch",
}

# ===== CPACS inputs and outputs =====
cpacs_inout = CPACSInOut()

include_gui = True

# ===== Input =====

# Select the aeromap to analyse
cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    cpacs_path=AEROMAPS_PATH,
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group=None,
)


# ===== Output =====

# cpacs_inout.add_output(
#     var_name='cd0',
#     default_value=None,
#     unit='1',
#     descr='Skin friction drag coefficient',
#     cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/skinFriction/cd0',
# )
#
# cpacs_inout.add_output(
#     var_name='wing_area',
#     default_value=None,
#     unit='m^2',
#     descr='Wing area of the main (largest) wing',
#     cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingArea',
# )
#
# cpacs_inout.add_output(
#     var_name='wing_span',
#     default_value=None,
#     unit='m',
#     descr='Wing span of the main (largest) wing',
#     cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingSpan',
# )
