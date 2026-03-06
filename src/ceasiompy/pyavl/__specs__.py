"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of PyAVL.
"""

# Imports
import streamlit as st

from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    # bool_vartype,
    dataframe_vartype,
)

from typing import Literal
from cpacspy.cpacspy import CPACS

from ceasiompy import MAIN_GAP
from ceasiompy.pyavl import (
    AVL_DISTR_XPATH,
    AVL_ROTRATES_XPATH,
    # AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    # AVL_FREESTREAM_MACH_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)


# Methods

def _display_panel_representation(
    cpacs: CPACS,
    spanwise_vertices: int,
    chordwise_vertices: int,
    panel_distribution: Literal["cosine", "sine", "equal"],
) -> None:
    # TODO: Add a display of the aircraft panel geometry used in pyavl (3D), look at code and how it converts to show the correct representation



# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    # TODO: Do vortices preview from panel settings
    st.markdown("**Panel Settings**")
    left_col, right_col = st.columns(2, gap=MAIN_GAP)
    with left_col:
        panel_distribution = list_vartype(
            tixi=tixi,
            name="Panel distribution",
            key="panel_distribution",
            default_value=["cosine", "sine", "equal"],
            help="Select the type of distribution.",
            xpath=AVL_DISTR_XPATH,
        )

        left_col, right_col = st.columns(2)
        with left_col:
            chordwise_vertices = int_vartype(
                tixi=tixi,
                name="Chordwise vortices",
                key="pyavl_chordwise_vortices_nb",
                default_value=20,
                help="Select the number of chordwise vortices.",
                xpath=AVL_NCHORDWISE_XPATH,
            )

        with right_col:
            spanwise_vertices = int_vartype(
                tixi=tixi,
                name="Spanwise vortices",
                key="pyavl_spanwise_vortices_nb",
                default_value=30,
                help="Select the number of spanwise vortices.",
                xpath=AVL_NSPANWISE_XPATH,
            )
    with right_col:
        _display_panel_representation(
            cpacs=cpacs,
            spanwise_vertices=spanwise_vertices,
            chordwise_vertices=chordwise_vertices,
            panel_distribution=panel_distribution,
        )

    st.markdown("---")
    st.markdown("**Specific Settings**")

    left_col, _ = st.columns(2, gap=MAIN_GAP)

    with left_col:
        dataframe_vartype(
            name="Rotation rates",
            key="rates",
            default_value=[0.0],
            tixi=tixi,
            xpath=AVL_ROTRATES_XPATH,
            help="List of p, q, r rates.",
        )

        dataframe_vartype(
            name="Control surface angles",
            key="ctrl_surf_angles",
            default_value=[0.0],
            tixi=tixi,
            xpath=AVL_CTRLSURF_ANGLES_XPATH,
            help="List of Aileron, Elevator, Rudder angles.",
        )

    # float_vartype(
    #     tixi=tixi,
    #     name="Default freestream Mach",
    #     key="default_freestream_mach",
    #     default_value=0.6,
    #     help="Usually 0.2 < default value < 0.8",
    #     xpath=AVL_FREESTREAM_MACH_XPATH,
    # )

    # bool_vartype(
    #     tixi=tixi,
    #     name="Integrate fuselage",
    #     key="integrate_fuselage",
    #     default_value=False,
    #     help="Integrate the fuselage in the AVL model.",
    #     xpath=AVL_FUSELAGE_XPATH,
    # )

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
#     gui=True,
#     gui_name="Values Expansion",
#     gui_group="Values Expansion",
#     expanded=False,
# )
