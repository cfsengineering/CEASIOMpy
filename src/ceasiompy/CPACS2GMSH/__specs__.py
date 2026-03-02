"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.
"""

# Imports
import streamlit as st

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import safe_remove
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    dataframe_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.to3d import MODULE_NAME as TO3D
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.CPACS2GMSH import (
    MODULE_NAME as CPACS2GMSH,
    HAS_PENTAGROW,
    GMSH_OPEN_GUI_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_XZ_SYMMETRY_XPATH,
    GMSH_FARFIELD_SIZE_FACTOR_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_WINGS_XPATH,
    GMSH_MESH_SIZE_FUSELAGE_XPATH,
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
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    if get_value(tixi, GEOMETRY_MODE_XPATH) != "3D":
        if TO3D in st.session_state.get("workflow_modules", None):
            log.info("gmsh will be called on 3D variant.")
        else:
            raise ValueError(f"You can not call {CPACS2GMSH} on a 2D geometry.")

    with st.expander(
        label="**Domain Settings**",
        expanded=True
    ):
        left_col, right_col = st.columns(2, vertical_alignment="bottom")

        # Domain Group

        float_vartype(
            tixi=tixi,
            xpath=GMSH_FARFIELD_SIZE_FACTOR_XPATH,
            default_value=10.0,
            name="Farfield size",
            key="farfield_size",
            help="Farfield size factor compare to the aircraft largest dimension.",
        )

    with st.expander(
        label="**Mesh Type**",
        expanded=True,
    ):

        # default is specific to Pentagrow installed or not
        default_value = ["EULER", "RANS"] if HAS_PENTAGROW else ["EULER"]
        euler_rans = list_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_TYPE_XPATH,
            default_value=default_value,
            name="Mesh type",
            key="mesh_type",
            help="Choose between Euler and RANS mesh.",
        )

        if euler_rans == "EULER":
            with st.container(
                border=True,
            ):
                st.markdown("**Euler Mesh Options**")
                left_col, right_col = st.columns(
                    spec=2,
                    vertical_alignment="bottom",
                )
                with left_col:
                    bool_vartype(
                        tixi=tixi,
                        xpath=GMSH_XZ_SYMMETRY_XPATH,
                        default_value=False,
                        name="Use Symmetry",
                        key="symmetry",
                        help="Create a symmetry condition.",
                    )

                with right_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
                        default_value=30.0,
                        name="Farfield mesh size",
                        key="farfield_mesh_size",
                        help="""Cell size on the farfield.""",
                    )

        else:
            safe_remove(tixi, xpath=GMSH_XZ_SYMMETRY_XPATH)
            safe_remove(tixi, xpath=GMSH_MESH_SIZE_FARFIELD_XPATH)

        # RANS Options
        if euler_rans == "RANS":
            with st.container(
                border=True,
            ):
                st.markdown("**RANS Mesh Options**")

                left_col, right_col = st.columns(2)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
                        default_value=1.5,
                        key="refine_factor_angled_lines",
                        name="Edges Refinement factor",
                        help="""
                            Refinement factor of edges at intersections
                            that are not flat enough (between angled surfaces).
                        """,
                    )
                with right_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_FEATURE_ANGLE_XPATH,
                        name="Feature Angle",
                        default_value=40.0,
                        key="feature_angle",
                        help="""Larger angles are treated as resulting
                            from approximation of curved surfaces.
                        """,
                    )
                left_col, right_col = st.columns(2)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_GROWTH_RATIO_XPATH,
                        name="Growth ratio",
                        default_value=1.2,
                        key="growth_ratio",
                        help="""The largest allowed ratio between
                            the wall-normal edge lengths of consecutive cells.
                        """,
                    )
                with right_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_GROWTH_FACTOR_XPATH,
                        name="Growth factor",
                        default_value=1.4,
                        key="growth_factor",
                        help="""Desired growth factor between
                            edge lengths of coincident tetrahedra.
                        """,
                    )

                left_col, mid_col, right_col = st.columns(3)
                with left_col:
                    int_vartype(
                        tixi=tixi,
                        xpath=GMSH_NUMBER_LAYER_XPATH,
                        default_value=20,
                        key="n_layer",
                        name="Number of layers",
                        help="Number of prismatic element layers.",
                    )
                with mid_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_H_FIRST_LAYER_XPATH,
                        default_value=0.003,
                        key="h_first_layer",
                        name="Height of first layer",
                        help="""
                            Height of the first prismatic cell,
                            touching the wall, in mesh length units.
                        """,
                    )
                with right_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
                        default_value=10.0,
                        key="max_layer_thickness",
                        name="Max layer thickness",
                        help="""
                            The maximum allowed absolute thickness of the prismatic layer.
                        """,
                    )

        else:
            safe_remove(tixi, xpath=GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH)
            safe_remove(tixi, xpath=GMSH_NUMBER_LAYER_XPATH)
            safe_remove(tixi, xpath=GMSH_H_FIRST_LAYER_XPATH)
            safe_remove(tixi, xpath=GMSH_MAX_THICKNESS_LAYER_XPATH)
            safe_remove(tixi, xpath=GMSH_GROWTH_RATIO_XPATH)
            safe_remove(tixi, xpath=GMSH_GROWTH_FACTOR_XPATH)
            safe_remove(tixi, xpath=GMSH_FEATURE_ANGLE_XPATH)

    # General Mesh Options
    with st.expander(
        label="**General Mesh Options**",
        expanded=True,
    ):
        first_col, second_col, third_col, fourth_col = st.columns(4)
        with first_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_MESH_SIZE_FUSELAGE_XPATH,
                default_value=0.1,
                name="Fuselage mesh size",
                key="fuselage_mesh_size",
                help="""Cell size on the fuselage (if any).""",
            )

        with second_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_MESH_SIZE_WINGS_XPATH,
                default_value=0.1,
                name="Wings mesh size",
                key="wing_mesh_size",
                help="""
                    Cell size on the wings (if any).
                """,
            )

        with third_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_MESH_SIZE_ENGINES_XPATH,
                default_value=0.23,
                name="Engine Mesh Size",
                key="engine_mesh_size",
                help="Value assigned for the engine surfaces mesh size.",
            )

        with fourth_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_MESH_SIZE_PROPELLERS_XPATH,
                default_value=0.23,
                name="Propellers Mesh Size",
                key="propeller_mesh_size",
                help="Value assigned for the propeller surfaces mesh size.",
            )

    # Advanced Mesh Parameters
    with st.expander(
        label="**Advanced Mesh Parameters**",
        expanded=True,
    ):
        left_col, mid_col, right_col = st.columns(3)
        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_N_POWER_FACTOR_XPATH,
                default_value=2.0,
                name="n power factor",
                key="n_power_factor",
                help="Power of the power law of the refinement on LE and TE."
            )

        with mid_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_N_POWER_FIELD_XPATH,
                default_value=0.9,
                name="n power field",
                key="n_power_field",
                help="Value that changes the measure of fist cells near aircraft parts.",
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_REFINE_FACTOR_XPATH,
                default_value=2.0,
                name="LE/TE refinement factor",
                key="refine_factor",
                help="Refinement factor of wing leading/trailing edge mesh.",
            )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_AUTO_REFINE_XPATH,
            default_value=False,
            name="Auto refine",
            key="auto_refine",
            help="""Automatically refine the mesh on surfaces that
                are small compare to the chosen mesh size.
            """,
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_SAVE_CGNS_XPATH,
            default_value=False,
            name="Save CGNS",
            key="save_cgns",
            help="Save also the geometry in the .cgns format",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_MESH_CHECKER_XPATH,
            default_value=False,
            name="Mesh Checker",
            key="mesh_checker",
            help="Check mesh quality with pyvista.",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_OPEN_GUI_XPATH,
            default_value=False,
            name="Open GMSH GUI",
            key="open_gmsh",
            help="Open GMSH GUI when the mesh is created",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_REFINE_TRUNCATED_XPATH,
            default_value=False,
            name="Refine truncated TE",
            key="refine_truncated",
            help="Enable the refinement of truncated trailing edge.",
        )

        bool_vartype(
            tixi=tixi,
            xpath=GMSH_EXPORT_PROP_XPATH,
            default_value=False,
            name="Export propeller(s) to be use as disk actuator",
            key="export_propellers",
            help="Export propeller(s) to be use as disk actuator",
        )

    with st.expander(
        label="**Engine(s) Settings**",
        expanded=False,
    ):
        left_col, right_col = st.columns(2)

        with left_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_INTAKE_PERCENT_XPATH,
                default_value=20.0,
                name="Engine intake position",
                key="intake_percent",
                help="""
                    Position of the intake surface boundary condition
                    in percentage of the engine length from the
                    beginning of the engine.
                """,
            )

        with right_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_EXHAUST_PERCENT_XPATH,
                default_value=20.0,
                name="Engine exhaust position",
                key="exhaust_percent",
                help="""Position of the exhaust surface boundary
                    condition in percentage of the engine length from
                    the end of the engine.
                """,
            )

    with st.expander(
        label="**Control Surfaces Settings**",
        expanded=True,
    ):
        dataframe_vartype(
            tixi=tixi,
            default_value=[0.0],
            name="Ail., Elev., Rudder Angles",
            key="ctrl_surf_angle",
            xpath=GMSH_CTRLSURF_ANGLE_XPATH,
            help="List of Aileron, Elevator, Rudder angles.",
        )
