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

cpacs_inout.add_input(
    var_name='aeromap_uid',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to calculate",
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/aeroMapUID',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='ref_len',
    var_type=float,
    default_value=None,
    unit='m',
    descr='Reference length of the aircraft',
    cpacs_path=AIRCRAFT_XPATH + '/model/reference/length',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='ref_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Reference area of the aircraft',
    cpacs_path=AIRCRAFT_XPATH + '/model/reference/area',
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
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseMach',
    gui=False,
    gui_name='Cruise Mach',
    gui_group='If fixed CL',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    var_type=float,
    default_value=120000.0,
    unit='m',
    descr='Aircraft cruise altitude',
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseAltitude',
    gui=False,
    gui_name='Cruise Altitude',
    gui_group='If fixed CL',
)

cpacs_inout.add_input(
    var_name='target_cl',
    var_type=float,
    default_value=1.0,
    unit='1',
    descr='Value of CL to achieve to have a level flight with the given conditions',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/targetCL',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='fixed_cl',
    var_type=str,
    default_value='NO',
    unit='-',
    descr='FIXED_CL_MODE parameter for SU2',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/fixedCL',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='max_iter',
    var_type=int,
    default_value=200,
    unit='1',
    descr='Maximum number of iterations performed by SU2',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/settings/maxIter',
    gui=True,
    gui_name='Maximum iterations',
    gui_group='SU2 Parameters',
)

cpacs_inout.add_input(
    var_name='cfl_nb',
    var_type=float,
    default_value=1.0,
    unit='1',
    descr='CFL Number, Courant–Friedrichs–Lewy condition',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/settings/cflNumber',
    gui=True,
    gui_name='CFL Number',
    gui_group='SU2 Parameters',
)

cpacs_inout.add_input(
    var_name='mg_level',
    var_type=int,
    default_value=3,
    unit='1',
    descr='CFL Number, Courant–Friedrichs–Lewy condition',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/settings/multigridLevel',
    gui=True,
    gui_name='Multigrid Level',
    gui_group='SU2 Parameters',
)

cpacs_inout.add_input(
    var_name='su2_mesh_path',
    var_type='pathtype',
    default_value='-',
    unit='1',
    descr='Absolute path of the SU2 mesh',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/meshPath',
    gui=True,
    gui_name='SU2 Mesh',
    gui_group='Inputs',
)


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

cpacs_inout.add_output(
    var_name='bc_wall_list',
    var_type=list,
    default_value=None,
    unit='1',
    descr='Wall boundary conditions found in the SU2 mesh',
    cpacs_path=CEASIOM_XPATH + 'su2/boundaryConditions/wall'
)


# TODO mayby remove
cpacs_inout.add_output(
    var_name='config_path',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Location of the configuration path for SU2',
    cpacs_path=CEASIOM_XPATH + 'su2/configPath'
)

#TODO : The aeroMap is filled by this module, how to say that in terms of output...
