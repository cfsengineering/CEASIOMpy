"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of PyAVL.
"""

# Imports
import streamlit as st

from cpacspy.cpacspy import CPACS

from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    dataframe_vartype,
)

from ceasiompy.PyAVL import (
    AVL_DISTR_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_FREESTREAM_MACH_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi
    with st.expander(
        label="Panel Settings",
        expanded=True,
    ):
        list_vartype(
            tixi=tixi,
            name="Panel distribution",
            key="panel_distribution",
            default_value=["cosine", "sine", "equal"],
            description="Select the type of distribution.",
            xpath=AVL_DISTR_XPATH,
        )

        int_vartype(
            tixi=tixi,
            name="Number of chordwise vortices",
            key="chordwise_vortices_nb",
            default_value=20,
            description="Select the number of chordwise vortices.",
            xpath=AVL_NCHORDWISE_XPATH,
        )

        int_vartype(
            tixi=tixi,
            name="Number of spanwise vortices",
            key="spanwise_vortices_nb",
            default_value=30,
            description="Select the number of spanwise vortices.",
            xpath=AVL_NSPANWISE_XPATH,
        )

    with st.expander(
        label="Specific Settings",
        expanded=True,
    ):
        dataframe_vartype(
            name="Rotation rates",
            key="rates",
            default_value=[0.0],
            tixi=tixi,
            xpath=AVL_ROTRATES_XPATH,
            description="List of p, q, r rates.",
        )

        dataframe_vartype(
            name="Control surface angles",
            key="ctrl_surf_angles",
            default_value=[0.0],
            tixi=tixi,
            xpath=AVL_CTRLSURF_ANGLES_XPATH,
            description="List of Aileron, Elevator, Rudder angles.",
        )

        float_vartype(
            tixi=tixi,
            name="Default freestream Mach",
            key="default_freestream_mach",
            default_value=0.6,
            description="Usually 0.2 < default value < 0.8",
            xpath=AVL_FREESTREAM_MACH_XPATH,
        )

    with st.container(
        border=True
    ):
        bool_vartype(
            tixi=tixi,
            name="Integrate fuselage",
            key="integrate_fuselage",
            default_value=False,
            description="Integrate the fuselage in the AVL model.",
            xpath=AVL_FUSELAGE_XPATH,
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
#     gui=True,
#     gui_name="Values Expansion",
#     gui_group="Values Expansion",
#     expanded=False,
# )
