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
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/aeroMapUID',
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
    xpath=AIRCRAFT_XPATH + '/model/reference/length',
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
    xpath=AIRCRAFT_XPATH + '/model/reference/area',
    gui=False,
    gui_name=None,
    gui_group=None,
)


for direction in ['x', 'y', 'z']:
    cpacs_inout.add_input(
        var_name=f'ref_ori_moment_{direction}',
        var_type=float,
        default_value=0.0,
        unit='m',
        descr=f"Fuselage scaling on {direction} axis",
        xpath=AIRCRAFT_XPATH + f'/model/reference/point/{direction}',
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
    xpath=CEASIOM_XPATH + '/ranges/cruiseAltitude',
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
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/targetCL',
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
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/fixedCL',
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='damping_der',
    var_type=bool,
    default_value=False,
    unit='1',
    descr='To check if damping derivatives should be calculated or not',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/options/clalculateDampingDerivatives',
    gui=True,
    gui_name='Damping Derivatives',
    gui_group='Aeromap Options',
)

cpacs_inout.add_input(
    var_name='rotation_rate',
    var_type=float,
    default_value=1.0,
    unit='rad/s',
    descr='Rotation rate use to calculate damping derivatives',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/options/rotationRate',
    gui=True,
    gui_name='Rotation Rate',
    gui_group='Aeromap Options',
)

cpacs_inout.add_input(
    var_name='control_surf',
    var_type=bool,
    default_value=False,
    unit='1',
    descr='To check if control surfaces deflections should be calculated or not',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/options/clalculateCotrolSurfacesDeflections',
    gui=True,
    gui_name='Control Surfaces',
    gui_group='Aeromap Options',
)

cpacs_inout.add_input(
    var_name='nb_proc',
    var_type=int,
    default_value=1,
    unit='1',
    descr='Number of proc to use to run SU2',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/settings/nbProc',
    gui=True,
    gui_name='Nb of processor',
    gui_group='CPU',
)

cpacs_inout.add_input(
    var_name='max_iter',
    var_type=int,
    default_value=200,
    unit='1',
    descr='Maximum number of iterations performed by SU2',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/settings/maxIter',
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
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/settings/cflNumber',
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
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/settings/multigridLevel',
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
    xpath=CEASIOM_XPATH + '/filesPath/su2Mesh',
    gui=True,
    gui_name='SU2 Mesh',
    gui_group='Inputs',
)

cpacs_inout.add_input(
    var_name='check_extract_loads',
    var_type=bool,
    default_value=False,
    unit='1',
    descr='Option to extract loads from results',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/results/extractLoads',
    gui=True,
    gui_name='Extract loads',
    gui_group='Results',
)


# ----- Output -----

cpacs_inout.add_output(
    var_name='start_time',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Start time of the last SU2 calculation',
    xpath=SU2_XPATH + '/startTime',
)

cpacs_inout.add_output(
    var_name='end_time',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Start time of the last SU2 calculation',
    xpath=SU2_XPATH + '/endTime',
)

cpacs_inout.add_output(
    var_name='wetted_area',
    var_type=float,
    default_value=None,
    unit='m^2',
    descr='Aircraft wetted area calculated by SU2',
    xpath=CEASIOM_XPATH + '/geometry/analyses/wettedArea',
)

cpacs_inout.add_output(
    var_name='bc_wall_list',
    var_type=list,
    default_value=None,
    unit='1',
    descr='Wall boundary conditions found in the SU2 mesh',
    xpath=CEASIOM_XPATH + '/aerodynamics/su2/boundaryConditions/wall'
)

cpacs_inout.add_output(
    var_name='aeromap_SU2',  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit='-',
    descr='aeroMap with aero coefficients calculated by SU2',
    xpath='/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aeroMap[i]/aeroPerformanceMap',
)
