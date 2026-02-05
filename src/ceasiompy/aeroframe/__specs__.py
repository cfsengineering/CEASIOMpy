"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of Aeroframe.
"""

# Imports
import streamlit as st

from cpacspy.cpacspy import CPACS

from ceasiompy.pyavl.__specs__ import gui_settings as avl_settings
from ceasiompy.utils.guiobjects import (
    int_vartype,
    float_vartype,
)

from ceasiompy.aeroframe import (
    FRAMAT_IX_XPATH,
    FRAMAT_IY_XPATH,
    FRAMAT_AREA_XPATH,
    FRAMAT_DENSITY_XPATH,
    FRAMAT_NB_NODES_XPATH,
    FRAMAT_SHEARMODULUS_XPATH,
    FRAMAT_YOUNGMODULUS_XPATH,
    AEROFRAME_TOLERANCE_XPATH,
    AEROFRAME_MAXNB_ITERATIONS_XPATH,
)


# Functions

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.expander(
        label="**Convergence Settings**",
        expanded=True,
    ):
        left_col, right_col = st.columns(2)
        with left_col:
            int_vartype(
                tixi=tixi,
                xpath=AEROFRAME_MAXNB_ITERATIONS_XPATH,
                default_value=8,
                description="Maximum number of iterations of the aeroelastic-loop.",
                name="Maximum number of iterations",
                key="aeroframe_n_iter_max",
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=AEROFRAME_TOLERANCE_XPATH,
                default_value=1e-3,
                name="Convergence Criterion (Tolerance)",
                description="Tolerance for convergence of the wing deformation.",
                key="aeroframe_conv_criterion",
            )

    with st.expander(
        label="**AVL Settings**",
        expanded=False,
    ):
        avl_settings(cpacs)

    with st.expander(
        label="**FramAT Settings**",
        expanded=True,
    ):
        st.markdown("**Modulus Settings**")
        left_col, right_col = st.columns(2)
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_YOUNGMODULUS_XPATH,
                description="Enter the Young modulus of the wing material in GPa.",
                name="Young modulus [GPa]",
                default_value=70.0,
                key="aeroframe_young_modulus",
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_SHEARMODULUS_XPATH,
                name="Shear modulus [GPa]",
                description="Enter the shear modulus of the wing material in GPa.",
                default_value=26.0,
                key="aeroframe_shearmodulus",
            )

        st.markdown("**Cross-Section settings**")
        left_col, mid_col, right_col = st.columns(3)
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_AREA_XPATH,
                name="Cross-section area",
                description="Area of the cross-section in m².",
                default_value=1.0,
                key="aeroframe_cross_section_area",
            )

        with mid_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_IX_XPATH,
                name="Second moment of area Ix",
                description="""Second moment of area of the cross-section
                    about the horizontal axis, in m⁴.
                """,
                default_value=1.0,
                key="cross_section_ix",
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_IY_XPATH,
                name="Second moment of area Iy",
                description="""Second moment of area of the cross-section
                    about the vertical axis, in m⁴.
                """,
                default_value=1.0,
                key="cross_section_iy",
            )

        st.markdown("**Other**")
        left_col, right_col = st.columns(2)
        with left_col:
            int_vartype(
                tixi=tixi,
                xpath=FRAMAT_NB_NODES_XPATH,
                default_value=15,
                description="Enter number of nodes for the beam mesh.",
                name="Number of beam nodes",
                key="aeroframe_beam_nodes",
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=FRAMAT_DENSITY_XPATH,
                default_value=1960.0,
                description="Density of the wing material in kg/m³.",
                key="aeroframe_material_density",
                name="Material density",
            )
