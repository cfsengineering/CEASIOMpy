"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.
"""

# Imports
import streamlit as st

from ceasiompy.utils.ceasiompyutils import safe_remove
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy.airfoil2gmsh import (
    AIRFOIL2GMSH_AIRFOIL_MESH_SIZE_XPATH,
    AIRFOIL2GMSH_EXT_MESH_SIZE_XPATH,
    AIRFOIL2GMSH_FARFIELD_RADIUS_XPATH,
    AIRFOIL2GMSH_STRUCTURED_MESH_XPATH,
    AIRFOIL2GMSH_FARFIELD_TYPE_XPATH,
    AIRFOIL2GMSH_FIRST_LAYER_HEIGHT_XPATH,
    AIRFOIL2GMSH_HEIGHT_LENGTH_XPATH,
    AIRFOIL2GMSH_WAKE_LENGTH_XPATH,
    AIRFOIL2GMSH_LENGTH_XPATH,
    AIRFOIL2GMSH_NO_BL_XPATH,
    AIRFOIL2GMSH_RATIO_XPATH,
    AIRFOIL2GMSH_NB_LAYERS_XPATH,
)


# Functions

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    # Mesh sizes
    left_col, right_col = st.columns(2)
    with left_col:
        float_vartype(
            tixi=tixi,
            xpath=AIRFOIL2GMSH_AIRFOIL_MESH_SIZE_XPATH,
            default_value=0.01,
            name="Airfoil Mesh Size",
            unit="m",
            help="Mesh size on the airfoil contour for 2D mesh generation",
        )

    with right_col:
        float_vartype(
            tixi=tixi,
            xpath=AIRFOIL2GMSH_EXT_MESH_SIZE_XPATH,
            default_value=0.2,
            name="External Mesh Size",
            key="external_mesh_size",
            unit="m",
            help="Mesh size in the external domain for 2D mesh generation",
        )

    st.markdown("---")
    boundary_layer = bool_vartype(
        tixi=tixi,
        xpath=AIRFOIL2GMSH_NO_BL_XPATH,
        default_value=False,
        name="Boundary Layer",
        key="boundary_layer",
        help="Disable boundary layer (unstructured mesh with triangles only).",
    )

    if boundary_layer:
        left_col, mid_col, right_col = st.columns(3)
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_FIRST_LAYER_HEIGHT_XPATH,
                default_value=0.001,
                name="First Layer Height",
                key="first_layer_height",
                unit="m",
                help="First layer height for 2D mesh generation",
            )
        with mid_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_RATIO_XPATH,
                default_value=1.2,
                name="Growth Factor",
                key="growth_factor",
                help="Growth factor of boundary layer cells.",
            )
        with right_col:
            int_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_NB_LAYERS_XPATH,
                default_value=25,
                name="Number of Layers",
                key="nb_layers",
                help="Number of layers in the boundary layer.",
            )
    else:
        safe_remove(tixi, xpath=AIRFOIL2GMSH_RATIO_XPATH)
        safe_remove(tixi, xpath=AIRFOIL2GMSH_NB_LAYERS_XPATH)
        safe_remove(tixi, xpath=AIRFOIL2GMSH_FIRST_LAYER_HEIGHT_XPATH)

    st.markdown("---")
    left_col, right_col = st.columns(2)
    with left_col:
        structured_mesh = list_vartype(
            tixi=tixi,
            xpath=AIRFOIL2GMSH_STRUCTURED_MESH_XPATH,
            default_value=["Structured", "Hybrid"],
            name="Structured or Hybrid Mesh",
            key="structured_mesh",
            help="Choose if you want a structured mesh or a hybrid one."
        )

    with right_col:
        default_value = (
            ["CType"]
            if structured_mesh == "Structured"
            else ["Rectangular", "Circular", "CType"]
        )

        farfield_type = list_vartype(
            tixi=tixi,
            xpath=AIRFOIL2GMSH_FARFIELD_TYPE_XPATH,
            default_value=default_value,
            name="Farfield Type",
            key="farfield_type",
            help="""
                Choose farfield shape (automatically set to CType for structured mesh).
            """,
        )

    left_col, right_col = st.columns(2)
    if farfield_type == "Circular":
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_FARFIELD_RADIUS_XPATH,
                default_value=10.0,
                name="Farfield Radius",
                key="farfield_radius",
                unit="m",
                help="Farfield radius for circular farfield in 2D mesh generation.",
            )
    else:
        safe_remove(tixi, xpath=AIRFOIL2GMSH_FARFIELD_RADIUS_XPATH)

    if farfield_type == "CType":
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_WAKE_LENGTH_XPATH,
                default_value=6.0,
                name="Wake Length",
                key="wake_length",
                unit="m",
                help="""
                    Wake length downstream of the airfoil for C-type farfield.
                """,
            )
    else:
        safe_remove(tixi, xpath=AIRFOIL2GMSH_WAKE_LENGTH_XPATH)

    if farfield_type == "Rectangular":
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_LENGTH_XPATH,
                default_value=5.0,
                name="Length",
                key="length",
                unit="m",
                help="Length of domain for rectangular farfield.",
            )
    else:
        safe_remove(tixi, xpath=AIRFOIL2GMSH_LENGTH_XPATH)

    if farfield_type == "CType" or farfield_type == "Rectangular":
        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=AIRFOIL2GMSH_HEIGHT_LENGTH_XPATH,
                default_value=5.0,
                name="Height Length",
                key="height_length",
                help="Height of domain for C-type farfield.",
                unit="m",
            )
    else:
        safe_remove(tixi, xpath=AIRFOIL2GMSH_HEIGHT_LENGTH_XPATH)
