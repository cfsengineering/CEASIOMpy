#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH
from ceasiompy.StabilityStatic.staticstability import LONGI_XPATH , DIREC_XPATH

STATICSTAB_XPATH = CEASIOM_XPATH +  '/stability/static'


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


# ===== Input =====

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=STATICSTAB_XPATH + '/aeroMapUid',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group=None,
)


# ===== Output =====

cpacs_inout.add_output(
    var_name='longitudinaly_stable',
    default_value=None,
    unit='1',
    descr='Is the aircraft longitudinaly stable',
    xpath=LONGI_XPATH,
)

cpacs_inout.add_output(
    var_name='dirrectionaly_stable',
    default_value=None,
    unit='1',
    descr='Is the aircraft dirrectionaly stable',
    xpath= DIREC_XPATH,
)
