#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# ===== RCE integration =====

RCE = {
    "name": "SU2Run",
    "description": "Moudule to run SU2 calculation",
    "exec": "pwd\npython su2run.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No inputs value for this modules

# ----- Output -----

cpacs_inout.add_output(
    var_name='start_time',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Start time of the last SU2 calculation',
    cpacs_path=SU2_XPATH + '/startTime',
)

cpacs_inout.add_output(
    var_name='end_time',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Start time of the last SU2 calculation',
    cpacs_path=SU2_XPATH + '/endTime',
)

cpacs_inout.add_output(
    var_name='wetted_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Aircraft wetted area calculated by SU2',
    cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wettedArea',
)

#TODO : The aeroMap is filled by this module, how to say that in terms of output...
