"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of PyAVL.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.PyAVL import (
    INCLUDE_GUI,
    AVL_DISTR_XPATH,
    AVL_EXPAND_VALUES_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_FREESTREAM_MACH_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="rates",
    var_type="multiselect",
    default_value=[0.0],
    unit="[deg/s]",
    descr="List of p, q, r rates",
    xpath=AVL_ROTRATES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Rotation Rates",
    gui_group="Rate settings",
)

cpacs_inout.add_input(
    var_name="ctrl_surf_angles",
    var_type="multiselect",
    default_value=[0.0],
    unit="[deg]",
    descr="List of Aileron, Elevator, Rudder angles",
    xpath=AVL_CTRLSURF_ANGLES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Aileron/Elevator/Rudder Angles",
    gui_group="Control surface settings",
)

cpacs_inout.add_input(
    var_name="integrate_fuselage",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select to integrate the fuselage in the AVL model",
    xpath=AVL_FUSELAGE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Integrate fuselage",
    gui_group="Simulation Settings",
)

cpacs_inout.add_input(
    var_name="panel_distribution",
    var_type=list,
    default_value=["cosine", "sine", "equal"],
    unit=None,
    descr=("Select the type of distribution"),
    xpath=AVL_DISTR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choice of distribution",
    gui_group="Simulation Settings",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=AVL_NCHORDWISE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of chordwise vortices",
    gui_group="Simulation Settings",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=50,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=AVL_NSPANWISE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of spanwise vortices",
    gui_group="Simulation Settings",
)

cpacs_inout.add_input(
    var_name="default_freestream_mach",
    var_type=float,
    default_value=0.6,
    unit="[Mach]",
    descr="Usually 0.2 < default value < 0.8",
    xpath=AVL_FREESTREAM_MACH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Default freestream Mach for Prandtl-Glauert corrections",
    gui_group="Default freestream Mach",
)

# Integrate In AeroMap Settings
# cpacs_inout.add_input(
#     var_name="expand_values",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="""
#     Selected values from aeromap will form a n-dimension cube (Specific for Dynamic Stability)
#     For example (alt, mach): (0.0, 0.1), (1000.0, 0.5)
#     Will transform into (alt, mach): (0.0, 0.1), (1000.0, 0.1), (0.0, 0.5), (1000.0, 0.5)
#     """,
#     xpath=AVL_EXPAND_VALUES_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Values Expansion",
#     gui_group="Values Expansion",
#     expanded=False,
# )
