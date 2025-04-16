"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of PyAVL.


| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.ceasiompyutils import get_reasonable_nb_cpu

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.PyAVL import include_gui

from ceasiompy.PyAVL import (
    AVL_PLOT_XPATH,
    AVL_DISTR_XPATH,
    AVL_NB_CPU_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_PLOTLIFT_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_AEROMAP_UID_XPATH,
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
    var_name="aeromap_uid",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=AVL_AEROMAP_UID_XPATH,
    gui=include_gui,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="rates",
    var_type="multiselect",
    default_value=[0.0],
    unit="[deg/s]",
    descr="List of p, q, r rates",
    xpath=AVL_ROTRATES_XPATH,
    gui=include_gui,
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
    gui=include_gui,
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
    gui=include_gui,
    gui_name="Integrate fuselage",
    gui_group="Fuselage",
)

cpacs_inout.add_input(
    var_name="panel_distribution",
    var_type=list,
    default_value=["cosine", "sine", "equal"],
    unit=None,
    descr=("Select the type of distribution"),
    xpath=AVL_DISTR_XPATH,
    gui=include_gui,
    gui_name="Choice of distribution",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=AVL_NCHORDWISE_XPATH,
    gui=include_gui,
    gui_name="Number of chordwise vortices",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=50,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=AVL_NSPANWISE_XPATH,
    gui=include_gui,
    gui_name="Number of spanwise vortices",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="nb_proc",
    var_type=int,
    default_value=get_reasonable_nb_cpu(),
    unit=None,
    descr="Number of proc to use to run SU2",
    xpath=AVL_NB_CPU_XPATH,
    gui=include_gui,
    gui_name="Nb of processor",
    gui_group="CPU",
)

cpacs_inout.add_input(
    var_name="default_freestream_mach",
    var_type=float,
    default_value=0.6,
    unit="[Mach]",
    descr="Usually 0.2 < default value < 0.8",
    xpath=AVL_FREESTREAM_MACH_XPATH,
    gui=include_gui,
    gui_name="Default freestream Mach for Prandtl-Glauert corrections",
    gui_group="Default freestream Mach",
)

cpacs_inout.add_input(
    var_name="plot_lift",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select to plot lift along wing",
    xpath=AVL_PLOTLIFT_XPATH,
    gui=include_gui,
    gui_name="Plot Lift",
    gui_group="Plots Settings",
)

cpacs_inout.add_input(
    var_name="save_plots",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select to save geometry and results plots",
    xpath=AVL_PLOT_XPATH,
    gui=include_gui,
    gui_name="Save plots",
    gui_group="Plots Settings",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
