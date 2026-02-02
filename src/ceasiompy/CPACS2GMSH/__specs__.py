"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.
"""

# Imports
import streamlit as st

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    multiselect_vartype,
)

from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.CPACS2GMSH import (
    HAS_PENTAGROW,
    GMSH_OPEN_GUI_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_SYMMETRY_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_CTRLSURF_ANGLE_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
    GMSH_AUTO_REFINE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
    GMSH_EXPORT_PROP_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_SAVE_CGNS_XPATH,
    GMSH_MESH_CHECKER_XPATH,
    GMSH_2D_AIRFOIL_MESH_SIZE_XPATH,
    GMSH_2D_EXT_MESH_SIZE_XPATH,
    GMSH_2D_FARFIELD_RADIUS_XPATH,
    GMSH_2D_STRUCTURED_MESH_XPATH,
    GMSH_2D_FARFIELD_TYPE_XPATH,
    GMSH_2D_FIRST_LAYER_HEIGHT_XPATH,
    GMSH_2D_HEIGHT_LENGTH_XPATH,
    GMSH_2D_WAKE_LENGTH_XPATH,
    GMSH_2D_LENGTH_XPATH,
    GMSH_2D_NO_BL_XPATH,
    GMSH_2D_RATIO_XPATH,
    GMSH_2D_NB_LAYERS_XPATH,
    GMSH_2D_MESH_FORMAT_XPATH,
)


# Methods
def _load_3d_gui_settings(tixi: Tixi3) -> None:

    with st.expander(
        label="Domain Settings",
        expanded=True
    ):
        # Domain Group
        bool_vartype(
            tixi=tixi,
            xpath=GMSH_SYMMETRY_XPATH,
            default_value=False,
            name="Use Symmetry",
            key="symmetry",
            description="Create a symmetry condition.",
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_FARFIELD_FACTOR_XPATH,
            default_value=10.0,
            name="Farfield size factor",
            key="farfield_size_factor",
            description="Farfield size factor compare to the aircraft largest dimension.",
        )

    with st.expander(
        label="Mesh Type",
        expanded=True,
    ):

        # default is specific to Pentagrow installed or not
        default_value = ["Euler", "RANS"] if HAS_PENTAGROW else ["Euler"]
        euler_rans = list_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_TYPE_XPATH,
            default_value=default_value,
            name="Mesh type",
            key="mesh_type",
            description="Choose between Euler and RANS mesh.",
        )

        if euler_rans == "Euler":
            with st.container(
                border=True,
            ):
                st.markdown("#### Euler Mesh Options")

                # Euler Mesh options
                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
                    default_value=1.0,
                    name="Fuselage mesh size factor",
                    key="fuselage_mesh_size_factor",
                    description="""Factor proportional to the biggest cell
                    on the plane to obtain cell size on the farfield
                    """,
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
                    default_value=1.0,
                    name="Wings mesh size factor",
                    key="wing_mesh_size_factor_fuselage",
                    description="""Factor proportional to fuselage radius
                        of curvature to obtain cell size on it.
                    """,
                )

        # RANS Options
        if euler_rans == "RANS":
            with st.container(
                border=True,
            ):
                st.markdown("#### RANS Mesh Options")

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
                    default_value=1.5,
                    key="refine_factor_angled_lines",
                    name="Refinement factor of lines in between angled surfaces",
                    description="""
                        Refinement factor of edges at intersections
                        that are not flat enough.
                    """,
                )

                int_vartype(
                    tixi=tixi,
                    xpath=GMSH_NUMBER_LAYER_XPATH,
                    default_value=20,
                    key="n_layer",
                    name="Number of layer",
                    description="Number of prismatic element layers.",
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_H_FIRST_LAYER_XPATH,
                    default_value=3,
                    key="h_first_layer",
                    name="Height of first layer",
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
                    default_value=100.0,
                    key="max_layer_thickness",
                    name="Max layer thickness",
                    description="The maximum allowed absolute thickness of the prismatic layer.",
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_GROWTH_RATIO_XPATH,
                    default_value=1.2,
                    key="growth_ratio",
                    name="Growth ratio",
                    description="""The largest allowed ratio between
                        the wall-normal edge lengths of consecutive cells.
                    """,
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_GROWTH_FACTOR_XPATH,
                    default_value=1.2,
                    key="growth_factor",
                    name="Growth factor",
                    description="""The largest allowed ratio between
                        the wall-normal edge lengths of consecutive cells.
                    """
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_GROWTH_RATIO_XPATH,
                    name="Growth ratio",
                    default_value=1.2,
                    key="growth_ratio",
                    description="""The largest allowed ratio between
                        the wall-normal edge lengths of consecutive cells.
                    """,
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_GROWTH_FACTOR_XPATH,
                    name="Growth factor",
                    default_value=1.4,
                    key="growth_factor",
                    description="""Desired growth factor between
                        edge lengths of coincident tetrahedra.
                    """,
                )

                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_FEATURE_ANGLE_XPATH,
                    name="Feature Angle",
                    default_value=40.0,
                    key="feature_angle",
                    description="""Larger angles are treated as resulting
                        from approximation of curved surfaces.
                    """,
                )

    # General Mesh Options
    with st.expander(
        label="General Mesh Options",
        expanded=True,
    ):
        float_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
            default_value=1.0,
            name="Wings mesh size factor",
            key="wing_mesh_size_factor_wing",
            description="""
                Factor proportional to wing radius of curvature to obtain cell size on it.
            """,
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_SIZE_ENGINES_XPATH,
            default_value=0.23,
            name="Engine Mesh Size",
            key="engine_mesh_size",
            description="Value assigned for the engine surfaces mesh size.",
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_SIZE_PROPELLERS_XPATH,
            default_value=0.23,
            name="Propellers Mesh Size",
            key="propeller_mesh_size",
            description="Value assigned for the propeller surfaces mesh size.",
        )

    # Advanced Mesh Parameters
    with st.expander(
        label="Advanced Mesh Parameters",
        expanded=True,
    ):

        float_vartype(
            tixi=tixi,
            xpath=GMSH_N_POWER_FACTOR_XPATH,
            default_value=2.0,
            name="n power factor",
            key="n_power_factor",
            description="Power of the power law of the refinement on LE and TE."
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_N_POWER_FIELD_XPATH,
            default_value=0.9,
            name="n power field",
            key="n_power_field",
            description="Value that changes the measure of fist cells near aircraft parts.",
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_REFINE_FACTOR_XPATH,
            default_value=2.0,
            name="LE/TE refinement factor",
            key="refine_factor",
            description="Refinement factor of wing leading/trailing edge mesh.",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_REFINE_TRUNCATED_XPATH,
            default_value=False,
            name="Refine truncated TE",
            key="refine_truncated",
            description="Enable the refinement of truncated trailing edge.",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_AUTO_REFINE_XPATH,
            default_value=False,
            name="Auto refine",
            key="auto_refine",
            description="""Automatically refine the mesh on surfaces that
                are small compare to the chosen mesh size.
            """,
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_EXPORT_PROP_XPATH,
            default_value=False,
            name="Export propeller(s) to be use as disk actuator",
            key="export_propellers",
            description="Export propeller(s) to be use as disk actuator",
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_INTAKE_PERCENT_XPATH,
            default_value=20.0,
            name="Engine intake position",
            key="intake_percent",
            description="""
                Position of the intake surface boundary condition
                in percentage of the engine length from the
                beginning of the engine.
            """,
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_EXHAUST_PERCENT_XPATH,
            default_value=20.0,
            name="Engine exhaust position",
            key="exhaust_percent",
            description="""Position of the exhaust surface boundary
                condition in percentage of the engine length from
                the end of the engine.
            """,
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_SAVE_CGNS_XPATH,
            default_value=False,
            name="Save CGNS",
            key="save_cgns",
            description="Save also the geometry in the .cgns format",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_CHECKER_XPATH,
            default_value=False,
            name="Mesh Checker",
            key="mesh_checker",
            description="Check mesh quality with pyvista.",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_OPEN_GUI_XPATH,
            default_value=False,
            name="Open GMSH GUI",
            key="open_gmsh",
            description="Open GMSH GUI when the mesh is created",
        )

    with st.expander(
        label="Control Surfaces Settings",
        expanded=True,
    ):
        multiselect_vartype(
            tixi=tixi,
            default_value=[0.0],
            name="Aileron/Elevator/Rudder Angles",
            key="ctrl_surf_angle",
            xpath=GMSH_CTRLSURF_ANGLE_XPATH,
            description="List of Aileron, Elevator, Rudder angles.",
        )


def _load_2d_gui_settings(tixi: Tixi3) -> None:

    # Mesh Options
    no_boundary_layer = bool_vartype(
        tixi=tixi,
        xpath=GMSH_2D_NO_BL_XPATH,
        default_value=False,
        name="No Boundary Layer",
        key="no_boundary_layer",
        description="Disable boundary layer (unstructured mesh with triangles only).",
    )

    float_vartype(
        tixi=tixi,
        xpath=GMSH_2D_AIRFOIL_MESH_SIZE_XPATH,
        default_value=0.01,
        name="Airfoil Mesh Size",
        key="airfoil_mesh_size",
        description="Mesh size on the airfoil contour for 2D mesh generation",
    )

    float_vartype(
        tixi=tixi,
        xpath=GMSH_2D_EXT_MESH_SIZE_XPATH,
        default_value=0.2,
        name="External Mesh Size",
        key="external_mesh_size",
        description="Mesh size in the external domain for 2D mesh generation",
    )

    structured_mesh = bool_vartype(
        tixi=tixi,
        xpath=GMSH_2D_STRUCTURED_MESH_XPATH,
        default_value=False,
        name="Structured Mesh",
        key="structured_mesh",
        description="Choose if you want a structured mesh or a hybrid one."
    )

    if not no_boundary_layer:
        float_vartype(
            tixi=tixi,
            xpath=GMSH_2D_FIRST_LAYER_HEIGHT_XPATH,
            default_value=0.001,
            name="First Layer Height",
            key="first_layer_height",
            description="First layer height for 2D mesh generation",
        )

        float_vartype(
            tixi=tixi,
            xpath=GMSH_2D_RATIO_XPATH,
            default_value=1.2,
            name="Growth Factor",
            key="growth_factor",
            description="Growth factor of boundary layer cells.",
        )

        int_vartype(
            tixi=tixi,
            xpath=GMSH_2D_NB_LAYERS_XPATH,
            default_value=25,
            name="Number of Layers",
            key="nb_layers",
            description="Number of layers in the boundary layer.",
        )

    if not structured_mesh:
        farfield_type = list_vartype(
            tixi=tixi,
            xpath=GMSH_2D_FARFIELD_TYPE_XPATH,
            default_value=["Rectangular", "Circular", "CType"],
            name="Farfield Type",
            key="farfield_type",
            description="Choose farfield shape (automatically set to CType for structured mesh).",
        )

        if farfield_type == "Circular":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_FARFIELD_RADIUS_XPATH,
                default_value=10.0,
                name="Farfield Radius",
                key="farfield_radius",
                description="Farfield radius for circular farfield in 2D mesh generation.",
            )

        elif farfield_type == "CType":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_WAKE_LENGTH_XPATH,
                default_value=6.0,
                name="Wake Length",
                key="wake_length",
                description="""
                    Wake length downstream of the airfoil for rectangular/C-type farfield
                """,
            )

        elif farfield_type == "CType" or farfield_type == "Rectangular":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_HEIGHT_LENGTH_XPATH,
                default_value=5.0,
                name="Height",
                key="height",
                description="Height of domain for C-type/rectangular farfield",
            )

        elif farfield_type == "Rectangular":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_LENGTH_XPATH,
                default_value=5.0,
                name="Length",
                key="length",
                description="Length of domain for rectangular farfield",
            )

    list_vartype(
        tixi=tixi,
        xpath=GMSH_2D_MESH_FORMAT_XPATH,
        default_value=["su2", "msh", "vtk", "wrl", "stl", "mesh", "cgns", "dat"],
        name="Mesh Format",
        key="mesh_format_2d",
        description="Output format for 2D mesh file (su2, msh, vtk, wrl, stl, mesh, cgns, dat)",
    )


# Functions
def gui_settings(cpacs: CPACS) -> None:
    """CPACS2Gmsh GUI Settings."""
    tixi = cpacs.tixi

    if get_value(tixi, GEOMETRY_MODE_XPATH) == "3D":
        _load_3d_gui_settings(tixi)
    else:
        _load_2d_gui_settings(tixi)
