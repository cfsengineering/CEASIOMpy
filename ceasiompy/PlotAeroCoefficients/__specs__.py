#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "PlotAeroCoef",
    "description": "Plot aerodynamic coefficient from a CPACS file",
    "exec": "pwd\npython plotaerocoef.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


#===== Input =====

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    descr='List of aeroMap to plot',
    xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient/aeroMapToPlot',
    gui=True,
    gui_name='__AEROMAP_CHECHBOX',
)
