"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of Aeroframe.
"""

# Imports
import streamlit as st

from cpacspy.cpacspy import CPACS

from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    float_vartype,
)

from ceasiompy.PyAVL import (
    AVL_DISTR_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
)
from ceasiompy.AeroFrame import (
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
            name="Chordwise vortices",
            key="chordwise_vortices_nb",
            default_value=20,
            description="Select the number of chordwise vortices.",
            xpath=AVL_NCHORDWISE_XPATH,
        )

        int_vartype(
            tixi=tixi,
            name="Spanwise vortices",
            key="spanwise_vortices_nb",
            default_value=30,
            description="Select the number of spanwise vortices.",
            xpath=AVL_NSPANWISE_XPATH,
        )

    with st.container(
        border=True,
    ):
        st.markdown("#### Convergence Settings")

        int_vartype(
            tixi=tixi,
            xpath=AEROFRAME_MAXNB_ITERATIONS_XPATH,
            default_value=8,
            description="Maximum number of iterations of the aeroelastic-loop.",
            name="Maximum number of iterations",
            key="aeroframe_n_iter_max",
        )

        float_vartype(
            tixi=tixi,
            xpath=AEROFRAME_TOLERANCE_XPATH,
            default_value=1e-3,
            name="Convergence Criterion (Tolerance)",
            description="Tolerance for convergence of the wing deformation.",
            key="aeroframe_conv_criterion",
        )

    with st.container(
        border=True,
    ):
        st.markdown("#### FramAT Settings")

        int_vartype(
            tixi=tixi,
            xpath=FRAMAT_NB_NODES_XPATH,
            default_value=15,
            description="Enter number of nodes for the beam mesh.",
            name="Number of beam nodes",
            key="aeroframe_beam_nodes",
        )

        float_vartype(
            tixi=tixi,
            xpath=FRAMAT_YOUNGMODULUS_XPATH,
            description="Enter the Young modulus of the wing material in GPa.",
            name="Young modulus [GPa]",
            default_value=70.0,
            key="aeroframe_young_modulus",
        )

        float_vartype(
            tixi=tixi,
            xpath=FRAMAT_SHEARMODULUS_XPATH,
            name="Shear modulus [GPa]",
            description="Enter the shear modulus of the wing material in GPa.",
            default_value=26.0,
            key="aeroframe_shearmodulus",
        )

        float_vartype(
            tixi=tixi,
            xpath=FRAMAT_DENSITY_XPATH,
            default_value=1960.0,
            description="Density of the wing material in kg/m³.",
            key="aeroframe_material_density",
            name="Material density",
        )

        float_vartype(
            tixi=tixi,
            xpath=FRAMAT_AREA_XPATH,
            name="Cross-section area",
            description="Area of the cross-section in m².",
            default_value=1.0,
            key="aeroframe_cross_section_area",
        )

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
