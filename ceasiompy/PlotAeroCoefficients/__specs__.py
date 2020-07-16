#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

PLOT_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient'

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
    xpath=PLOT_XPATH + '/aeroMapToPlot',
    gui=True,
    gui_name='__AEROMAP_CHECHBOX',
    # gui_group='Multipe aeromap'
)

cpacs_inout.add_input(
    var_name='alt_crit',
    var_type=str,
    default_value='None',
    descr='Altitude inclusion criteria',
    xpath=PLOT_XPATH + '/criterion/alt',
    gui=True,
    gui_name='Altitdue criteria',
    gui_group='Plot vs AoA'
)

cpacs_inout.add_input(
    var_name='mach_crit',
    var_type=str,
    default_value='None',
    descr='Mach inclusion criteria',
    xpath=PLOT_XPATH + '/criterion/mach',
    gui=True,
    gui_name='Mach criteria',
    gui_group='Plot vs AoA'
)

cpacs_inout.add_input(
    var_name='aos_crit',
    var_type=str,
    default_value='None',
    descr='Angle of Sideslip (AoS) inclusion criteria',
    xpath=PLOT_XPATH + '/criterion/aos',
    gui=True,
    gui_name='AoS criteria',
    gui_group='Plot vs AoA'
)

cpacs_inout.add_input(
    var_name='manual_selct',
    var_type=bool,
    default_value=False,
    descr='Angle of Sideslip (AoS) inclusion criteria',
    xpath=PLOT_XPATH + '/manualSelection',
    gui=True,
    gui_name='Select AeroMaps manualy',
    gui_group='Other options'
)
