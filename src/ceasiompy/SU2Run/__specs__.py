"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of ModuleTemplate.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.ceasiompyutils import get_reasonable_nb_cpu

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import NO_YES_LIST
from ceasiompy.SU2Run import (
    INCLUDE_GUI,
    TEMPLATE_TYPE,
    SU2_AEROMAP_UID_XPATH,
    SU2_DAMPING_DER_XPATH,
    SU2_ROTATION_RATE_XPATH,
    SU2_CONTROL_SURF_BOOL_XPATH,
    SU2_CONTROL_SURF_ANGLE_XPATH,
    SU2_NB_CPU_XPATH,
    SU2_CONFIG_RANS_XPATH,
    SU2_MAX_ITER_XPATH,
    SU2_CFL_NB_XPATH,
    SU2_CFL_ADAPT_XPATH,
    SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
    SU2_CFL_ADAPT_PARAM_UP_XPATH,
    SU2_CFL_MIN_XPATH,
    SU2_CFL_MAX_XPATH,
    SU2_MG_LEVEL_XPATH,
    SU2_UPDATE_WETTED_AREA_XPATH,
    SU2_EXTRACT_LOAD_XPATH,
    SU2_ACTUATOR_DISK_XPATH,
    SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
    SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
    SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
    SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
    SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_BC_WALL_XPATH,
    SU2_BC_FARFIELD_XPATH,
)

from ceasiompy.utils.commonxpaths import (
    PROPELLER_THRUST_XPATH,
    PROPELLER_BLADE_LOSS_XPATH,
    RANGE_CRUISE_MACH_XPATH,
    RANGE_CRUISE_ALT_XPATH,
    GEOM_XPATH,
    USED_SU2_MESH_XPATH,
    AEROPERFORMANCE_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=SU2_AEROMAP_UID_XPATH,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="mesh_choice",
    var_type="DynamicChoice",
    default_value=["CPACS2GMSH mesh", "Path", "db"],
    unit=None,
    descr="Choose from where to upload the mesh",
    xpath=USED_SU2_MESH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choose mesh",
    gui_group="Data Settings",
)

cpacs_inout.add_input(
    var_name="damping_der",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="To check if damping derivatives should be calculated or not",
    xpath=SU2_DAMPING_DER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Damping Derivatives",
    gui_group="Damping Derivative Option",
)

cpacs_inout.add_input(
    var_name="rotation_rate",
    var_type=float,
    default_value=1.0,
    unit="[rad/s]",
    descr="Rotation rate use to calculate damping derivatives",
    xpath=SU2_ROTATION_RATE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Rotation Rate",
    gui_group="Rotation Rates Setting",
)

cpacs_inout.add_input(
    var_name="control_surf",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="To check if control surfaces deflections should be calculated or not",
    xpath=SU2_CONTROL_SURF_BOOL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Control Surfaces",
    gui_group="Control Surface Option",
)

cpacs_inout.add_input(
    var_name="ctrl_surf_deflection",
    var_type="multiselect",
    default_value=[0.0],
    unit="[deg]",
    descr="Rotation of control surface",
    xpath=SU2_CONTROL_SURF_ANGLE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Control surface angle",
    gui_group="Aeromap Options",
)

cpacs_inout.add_input(
    var_name="nb_proc",
    var_type=int,
    default_value=get_reasonable_nb_cpu(),
    unit=None,
    descr="Number of proc to use to run SU2",
    xpath=SU2_NB_CPU_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Nb of processor",
    gui_group="CPU",
)

cpacs_inout.add_input(
    var_name="RANS calculation",
    var_type=list,
    default_value=TEMPLATE_TYPE,
    unit=None,
    descr="Running EULER or RANS calculation",
    xpath=SU2_CONFIG_RANS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="EULER or RANS simulation",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="max_iter",
    var_type=int,
    default_value=1000,
    unit=None,
    descr="Maximum number of iterations performed by SU2",
    xpath=SU2_MAX_ITER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Maximum iterations",
    gui_group="SU2 Parameters",
    test_value=1,
)

cpacs_inout.add_input(
    var_name="cfl_nb",
    var_type=float,
    default_value=1.0,
    unit=None,
    descr="CFL Number, Courant–Friedrichs–Lewy condition",
    xpath=SU2_CFL_NB_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Number",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_adapt",
    var_type=list,
    default_value=NO_YES_LIST,
    unit=None,
    descr="CFL Adaptation",
    xpath=SU2_CFL_ADAPT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Adaptation",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_adapt_param_factor_down",
    var_type=float,
    default_value=0.5,
    unit=None,
    descr="CFL Adaptation Factor Down",
    xpath=SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Adaptation Factor Down",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_adapt_param_factor_up",
    var_type=float,
    default_value=1.5,
    unit=None,
    descr="CFL Adaptation Factor Up",
    xpath=SU2_CFL_ADAPT_PARAM_UP_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Adaptation Factor Up",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_adapt_param_min",
    var_type=float,
    default_value=0.5,
    unit=None,
    descr="CFL Minimum Value",
    xpath=SU2_CFL_MIN_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Min Value",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_adapt_param_max",
    var_type=float,
    default_value=100,
    unit=None,
    descr="CFL Maximum Value",
    xpath=SU2_CFL_MAX_XPATH,
    gui=INCLUDE_GUI,
    gui_name="CFL Max Value",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="mg_level",
    var_type=int,
    default_value=3,
    unit=None,
    descr="Multi-grid level (0 = no multigrid)",
    xpath=SU2_MG_LEVEL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Multigrid Level",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="update_wetted_area",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Option to update the wetted area from the latest SU2 result.",
    xpath=SU2_UPDATE_WETTED_AREA_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Update Wetted Area",
    gui_group="Results",
)

cpacs_inout.add_input(
    var_name="check_extract_loads",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Option to extract loads (forces in each point) from results",
    xpath=SU2_EXTRACT_LOAD_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Extract loads",
    gui_group="Results",
)

# Actuator disk
cpacs_inout.add_input(
    var_name="include_actuator_disk",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="To check if actuator disk(s) should be included in the SU2 calculation",
    xpath=SU2_ACTUATOR_DISK_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Include actuator disk(s)",
    gui_group="Actuator disk",
)

cpacs_inout.add_input(
    var_name="thrust",
    var_type=float,
    default_value=3000,
    unit="N",
    descr="Aircraft thrust",
    xpath=PROPELLER_THRUST_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Thrust",
    gui_group="Actuator disk",
)

# cpacs_inout.add_input(
#     var_name="n",
#     var_type=float,
#     default_value=33,
#     unit="1/s",
#     descr="Propeller rotational velocity",
#     xpath=PROP_XPATH + "/propeller/rotational_velocity",
#     gui=INCLUDE_GUI,
#     gui_name="Rotational velocity setting",
#     gui_group="Actuator disk",
# )

cpacs_inout.add_input(
    var_name="prandtl",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Enable or disable the tip loss correction of Prandtl",
    xpath=PROPELLER_BLADE_LOSS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Tip loss correction",
    gui_group="Actuator disk",
)

# cpacs_inout.add_input(
#     var_name="blades_number",
#     var_type=int,
#     default_value=3,
#     unit=None,
#     descr="Number of propeller blades",
#     xpath=PROP_XPATH + "/propeller/bladeNumber",
#     gui=INCLUDE_GUI,
#     gui_name="Propeller blades numbers",
#     gui_group="Actuator disk",
# )

# Dynamic Stability Settings
cpacs_inout.add_input(
    var_name="dot_derivatives",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Computing dot derivatives",
    xpath=SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Compute derivatives",
    gui_group="Dynamic Stability Settings",
)

cpacs_inout.add_input(
    var_name="time_steps",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Size of time vector i.e. t = 2pi * (0, 1/n-1, ..., n-2/n-1)",
    xpath=SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Time Size (n > 1)",
    gui_group="Dynamic Stability Settings",
)

cpacs_inout.add_input(
    var_name="amplitude",
    var_type=float,
    default_value=1.0,
    unit="[deg]",
    descr="Oscillation: a * sin(w t) and a > 0",
    xpath=SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Oscillation's amplitude (a): ",
    gui_group="Dynamic Stability Settings",
)

cpacs_inout.add_input(
    var_name="angular_frequency",
    var_type=float,
    default_value=0.087,
    unit="[rad/s]",
    descr="Oscillation: a * sin(w t) and w > 0",
    xpath=SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Oscillation's angular frequency (w)",
    gui_group="Dynamic Stability Settings",
)

cpacs_inout.add_input(
    var_name="inner_iter",
    var_type=int,
    default_value=10,
    unit=None,
    descr="Per time step, the maximum number of iterations the solver will use.",
    xpath=SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Maximum number of inner iterations",
    gui_group="Dynamic Stability Settings",
)
cpacs_inout.add_input(
    var_name="cruise_mach",
    var_type=float,
    default_value=0.78,
    unit=None,
    descr="Aircraft cruise Mach number",
    xpath=RANGE_CRUISE_MACH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Cruise Mach",
    gui_group="If fixed CL",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    var_type=float,
    default_value=120000.0,
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=RANGE_CRUISE_ALT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Cruise Altitude",
    gui_group="If fixed CL",
)

cpacs_inout.add_input(
    var_name="target_cl",
    var_type=float,
    default_value=1.0,
    unit=None,
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Target CL value",
    gui_group="If fixed CL",
)

cpacs_inout.add_input(
    var_name="fixed_cl",
    var_type=list,
    default_value=NO_YES_LIST,
    unit=None,
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Fixed CL value",
    gui_group="If fixed CL",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="wetted_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Aircraft wetted area calculated by SU2",
    xpath=GEOM_XPATH + "/analyses/wettedArea",
)

cpacs_inout.add_output(
    var_name="bc_wall_list",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Wall boundary conditions found in the SU2 mesh",
    xpath=SU2_BC_WALL_XPATH,
)

cpacs_inout.add_output(
    var_name="bc_farfield_list",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Farfield boundary conditions found in the SU2 mesh (for off engines)",
    xpath=SU2_BC_FARFIELD_XPATH,
)

cpacs_inout.add_output(
    var_name="aeromap_SU2",  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit="-",
    descr="aeroMap with aero coefficients calculated by SU2",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
