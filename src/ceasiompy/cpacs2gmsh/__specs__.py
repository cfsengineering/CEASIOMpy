"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.
"""

# Imports
import streamlit as st
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.plot import get_aircraft_mesh_data
from ceasiompy.cpacs2gmsh.utility.farfield import box_edges
from ceasiompy.utils.ceasiompyutils import (
    safe_remove,
    is_symmetric,
)
from ceasiompy.cpacs2gmsh.utility.mesh_sizing import (
    get_wing_ref_chord,
    get_fuselage_mean_circumference,
)
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
)

from cpacspy.cpacspy import CPACS

from numpy import sqrt
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.cpacs2gmsh import (
    HAS_PENTAGROW,
    GMSH_FARFIELD_RADIUS_XPATH,
    GMSH_ADD_BOUNDARY_LAYER_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_WING_XPATH,
    GMSH_MESH_SIZE_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_PYLON_XPATH,
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
    GMSH_UPSTREAM_LENGTH_XPATH,
    GMSH_WAKE_LENGTH_XPATH,
    GMSH_Y_LENGTH_XPATH,
    GMSH_Z_LENGTH_XPATH,
)


# Methods
def _load_3d_gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi
    aircraft_config = cpacs.aircraft.configuration
    symmetry = is_symmetric(cpacs)

    # Bounding Box for General Aircraft Settings
    x_min, y_min, z_min, x_max, y_max, z_max = cpacs.aircraft.tigl.configurationGetBoundingBox()
    if symmetry:
        y_min = 0.0
    vec = {
        "x": abs(x_max - x_min),
        "y": abs(y_max - y_min),
        "z": abs(z_max - z_min),
    }
    x_minyz = min(vec["x"], vec["y"], vec["z"])
    radius = sqrt(vec["x"]**2 + vec["y"]**2 + vec["z"]**2)

    st.markdown(f"""**{"Symmetric " if symmetry else ""}Domain Settings**""")
    st.markdown(
        f"<p style='margin-top:-8px; color:#6b7280; font-size:0.85rem;'>"
        f"Bounding Box size: ({vec['x']:.3f}, {vec['y']:.3f}, {vec['z']:.3f})</p>",
        unsafe_allow_html=True,
    )

    _domain_settings(
        x_min=x_min, 
        y_min=y_min, 
        z_min=z_min,
        x_max=x_max, 
        y_max=y_max,
        z_max=z_max,        
        cpacs=cpacs,
        symmetry=symmetry,
    )

    st.markdown("---")
    # TODO: Make a preview of the farfield meshing with the farfield mesh size
    float_vartype(
        tixi=tixi,
        xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
        default_value=round(radius/4.0, 3),
        name="Farfield mesh size",
        key="farfield_size",
        description=f"""Farfield mesh size, for reference
            the size of the smallest dimension is {x_minyz}.""",
        min_value=0.0,
        max_value=radius,
    )

    with st.expander(
        label="**Mesh Sizes**",
        expanded=True,
    ):
        wing_cnt = aircraft_config.get_wing_count()

        if wing_cnt == 0:
            st.warning(f"No wing found in aircraft {cpacs.ac_name}.")
        else:
            for k in range(1, wing_cnt + 1):
                wing = aircraft_config.get_wing(k)
                wing_uid = str(wing.get_uid())

                ref_chord = get_wing_ref_chord(
                    tixi=tixi,
                    wing_uid=wing_uid,
                )

                left_col, right_col = st.columns(2)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_MESH_SIZE_WING_XPATH + f"/{wing_uid}",
                        default_value=ref_chord/10.0,
                        min_value=0.0,
                        max_value=ref_chord,
                        name=f"Wing: {wing_uid} mesh size",
                        key=f"cpacs2gmsh_wing_mesh_size_{wing_uid}",
                        description=f"""
                            Cell size on the wing {wing_uid}.
                        """,
                    )
                with right_col:
                    st.number_input(
                        label=f"Reference Chord of wing {wing_uid}",
                        value=ref_chord,
                        disabled=True,
                    )

        fuselage_cnt = aircraft_config.get_fuselage_count()
        if fuselage_cnt == 0:
            st.warning(f"No fuselage found in aircraft {cpacs.ac_name}.")
        else:
            for k in range(1, fuselage_cnt + 1):
                fuselage = aircraft_config.get_fuselage(k)
                fus_uid = fuselage.get_uid()
                fus_mean_circumference = get_fuselage_mean_circumference(
                    tixi=tixi,
                    fus_uid=fus_uid,
                )
                left_col, right_col = st.columns(2)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_MESH_SIZE_FUSELAGE_XPATH + f"/{fus_uid}",
                        default_value=fus_mean_circumference/10.0,
                        min_value=0.0,
                        max_value=fus_mean_circumference,
                        name=f"Fuselage: {fus_uid} mesh size",
                        key=f"cpacs2gmsh_fuselage_mesh_size_{fus_uid}",
                        description=f"""Cell size on the fuselage
                            {fus_uid}.""",
                    )
                with right_col:
                    st.number_input(
                        label="Mean Circumference",
                        disabled=True,
                        value=fus_mean_circumference,
                    )

        pylons_config = aircraft_config.get_engine_pylons()
        if not pylons_config:
            st.info("Did not find any engine pylons.")
        else:
            pylon_cnt = pylons_config.get_pylon_count()
            for k in range(1, pylon_cnt + 1):
                pylon = pylons_config.get_engine_pylon(k)
                pylon_uid = pylon.get_uid()
                left_col, _ = st.columns(2)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=GMSH_MESH_SIZE_PYLON_XPATH + f"/{pylon_uid}",
                        default_value=0.0,
                        min_value=0.0,
                        name=f"Pylon {pylon_uid} mesh size",
                        key=f"cpacs2gmsh_pylon_mesh_size_{pylon_uid}",
                        description=f"""Cell size on the pylon
                            {pylon_uid}.""",
                    )

    disabled = False if HAS_PENTAGROW else True
    add_boundary_layer = bool_vartype(
        tixi=tixi,
        xpath=GMSH_ADD_BOUNDARY_LAYER_XPATH,
        default_value=False,
        name="Add Boundary Layer",
        key="cpacs2gmsh_add_boundary_layer",
        description="Boundary Layer made with Pentagrow.",
        disabled=disabled,
    )

    # RANS Options
    if add_boundary_layer:
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
                    description="""
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
                    description="""Larger angles are treated as resulting
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
                    description="""The largest allowed ratio between
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
                    description="""Desired growth factor between
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
                    description="Number of prismatic element layers.",
                )
            with mid_col:
                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_H_FIRST_LAYER_XPATH,
                    default_value=3,
                    key="h_first_layer",
                    name="Height of first layer",
                    description="""
                        Height of the first prismatic cell,
                        touching the wall, in mesh length units.
                    """,
                )
            with right_col:
                float_vartype(
                    tixi=tixi,
                    xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
                    default_value=100.0,
                    key="max_layer_thickness",
                    name="Max layer thickness",
                    description="""
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
                description="Power of the power law of the refinement on LE and TE."
            )

        with mid_col:
            float_vartype(
                tixi=tixi,
                xpath=GMSH_N_POWER_FIELD_XPATH,
                default_value=0.9,
                name="n power field",
                key="n_power_field",
                description="Value that changes the measure of fist cells near aircraft parts.",
            )

        with right_col:
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
            xpath=GMSH_REFINE_TRUNCATED_XPATH,
            default_value=False,
            name="Refine truncated TE",
            key="refine_truncated",
            description="Enable the refinement of truncated trailing edge.",
        )

    # engines_config = aircraft_config.get_engines()
    # if engines_config:
    #     with st.expander(
    #         label="**Engine(s) Settings**",
    #         expanded=False,
    #     ):
    #         left_col, right_col = st.columns(2)

    #         with left_col:
    #             float_vartype(
    #                 tixi=tixi,
    #                 xpath=GMSH_INTAKE_PERCENT_XPATH,
    #                 default_value=20.0,
    #                 name="Engine intake position",
    #                 key="intake_percent",
    #                 description="""
    #                     Position of the intake surface boundary condition
    #                     in percentage of the engine length from the
    #                     beginning of the engine.
    #                 """,
    #             )

    #         with right_col:
    #             float_vartype(
    #                 tixi=tixi,
    #                 xpath=GMSH_EXHAUST_PERCENT_XPATH,
    #                 default_value=20.0,
    #                 name="Engine exhaust position",
    #                 key="exhaust_percent",
    #                 description="""Position of the exhaust surface boundary
    #                     condition in percentage of the engine length from
    #                     the end of the engine.
    #                 """,
    #             )

    # with st.expander(
    #     label="**Control Surfaces Settings**",
    #     expanded=True,
    # ):
    #     dataframe_vartype(
    #         tixi=tixi,
    #         default_value=[0.0],
    #         name="Ail., Elev., Rudder Angles",
    #         key="ctrl_surf_angle",
    #         xpath=GMSH_CTRLSURF_ANGLE_XPATH,
    #         description="List of Aileron, Elevator, Rudder angles.",
    #     )


def _domain_settings(
    x_min: float,
    y_min: float,
    z_min: float,
    x_max: float,
    y_max: float,
    z_max: float,
    cpacs: CPACS,
    symmetry: bool,
) -> None:
    tixi = cpacs.tixi

    vec = {
        "x": abs(x_max - x_min),
        "y": abs(y_max - y_min),
        "z": abs(z_max - z_min),
    }

    domain_preview_placeholder = st.empty()

    left_col, right_col = st.columns(2)
    with left_col:
        upstream_length = float_vartype(
            tixi=tixi,
            name="Upstream Length",
            description="Length from upstream farfield to the aircraft's nose.",
            key="cpacs2gmsh_upstream_length",
            xpath=GMSH_UPSTREAM_LENGTH_XPATH,
            default_value=round(vec["x"]*2.0/3.0, ndigits=3),
            min_value=(delta_x:=vec["x"]/10.0),
            step=delta_x,
            max_value=5*vec["x"],
        )

    with right_col:
        wake_length = float_vartype(
            tixi=tixi,
            name="Wake Length",
            description="Downstream length: distance from farfield to the aircraft's tail.",
            key="cpacs2gmsh_wake_length",
            xpath=GMSH_WAKE_LENGTH_XPATH,
            default_value=round(vec["x"], ndigits=3),
            min_value=(delta_x:=vec["x"]/10.0),
            step=delta_x,
            max_value=5*vec["x"],
        )

    left_col, right_col = st.columns(2)
    with left_col:
        y_length = float_vartype(
            tixi=tixi,
            name="Y-length",
            description="Length to add in the y-direction.",
            xpath=GMSH_Y_LENGTH_XPATH,
            key="cpacs2gmsh_y_length",
            default_value=round(vec["y"]/6.0, ndigits=3),
            min_value=(delta_y:=vec["y"]/20.0),
            step=delta_y,
            max_value=2*vec["y"],
        )
    with right_col:
        z_length = float_vartype(
            tixi=tixi,
            name="Z-length",
            description="Length to add in the z-direction.",
            xpath=GMSH_Z_LENGTH_XPATH,
            key="cpacs2gmsh_z_length",
            default_value=round(vec["z"], ndigits=3),
            min_value=(delta_z:=vec["z"]/10.0),
            step=delta_z,
            max_value=vec["z"]*10.0,
        )

    inner_x, inner_y, inner_z = box_edges(
        x_min=x_min,
        y_min=y_min,
        z_min=z_min,
        x_max=x_max,
        y_max=y_max,
        z_max=z_max,
        symmetry=symmetry,
    )
    outer_x, outer_y, outer_z = box_edges(
        x_min=x_min - upstream_length,
        y_min=y_min - y_length,
        z_min=z_min - z_length,
        x_max=x_max + wake_length,
        y_max=y_max + y_length,
        z_max=z_max + z_length,
        symmetry=symmetry,
    )
    outer_x_min = x_min - upstream_length
    outer_x_max = x_max + wake_length
    outer_y_min = y_min - y_length
    outer_y_max = y_max + y_length
    outer_z_min = z_min - z_length
    outer_z_max = z_max + z_length

    center_x = 0.5 * (outer_x_min + outer_x_max)
    center_y = 0.5 * (outer_y_min + outer_y_max)
    center_z = 0.5 * (outer_z_min + outer_z_max)
    max_range = 0.5 * max(
        outer_x_max - outer_x_min,
        outer_y_max - outer_y_min,
        outer_z_max - outer_z_min,
    )

    fig = go.Figure()
    try:
        x, y, z, i, j, k = get_aircraft_mesh_data(
            cpacs=cpacs,
            symmetry=symmetry,
        )
        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                opacity=0.9,
                color="lightgrey",
                flatshading=False,
                lighting=dict(
                    ambient=0.5,
                    diffuse=0.2,
                    specular=0.3,
                    roughness=0.2,
                ),
                lightposition=dict(x=0, y=100, z=0),
                name="CPACS geometry",
                showscale=False,
            )
        )
    except Exception as e:
        st.warning(f"Cannot generate CPACS mesh preview: {e}")

    fig.add_trace(
        go.Scatter3d(
            x=inner_x,
            y=inner_y,
            z=inner_z,
            mode="lines",
            name="CPACS bounding box",
            line=dict(color="#1f77b4", width=6),
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=outer_x,
            y=outer_y,
            z=outer_z,
            mode="lines",
            name="Farfield box",
            line=dict(color="#d62728", width=4),
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        height=420,
        scene=dict(
            xaxis=dict(range=[center_x - max_range, center_x + max_range]),
            yaxis=dict(range=[center_y - max_range, center_y + max_range]),
            zaxis=dict(range=[center_z - max_range, center_z + max_range]),
            aspectmode="cube",
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )
    domain_preview_placeholder.plotly_chart(
        fig,
        width="stretch",
        key="cpacs2gmsh_domain_preview",
    )


def _load_2d_gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    # Mesh sizes
    with st.container(
        border=True,
    ):
        st.markdown("#### Mesh Settings")

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

        list_vartype(
            tixi=tixi,
            xpath=GMSH_2D_MESH_FORMAT_XPATH,
            default_value=["su2", "msh", "vtk", "wrl", "stl", "mesh", "cgns", "dat"],
            name="Mesh Format",
            key="mesh_format_2d",
            description="""
                Output format for 2D mesh file (su2, msh, vtk, wrl, stl, mesh, cgns, dat).
            """,
        )

    # Boundary Layer
    with st.container(
        border=True,
    ):
        no_boundary_layer = bool_vartype(
            tixi=tixi,
            xpath=GMSH_2D_NO_BL_XPATH,
            default_value=True,
            name="No Boundary Layer",
            key="no_boundary_layer",
            description="Disable boundary layer (unstructured mesh with triangles only).",
        )

        if not no_boundary_layer:
            with st.container(
                border=True,
            ):

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
        else:
            safe_remove(tixi, xpath=GMSH_2D_RATIO_XPATH)
            safe_remove(tixi, xpath=GMSH_2D_NB_LAYERS_XPATH)
            safe_remove(tixi, xpath=GMSH_2D_FIRST_LAYER_HEIGHT_XPATH)

    # Structured Mesh
    with st.container(
        border=True,
    ):
        st.markdown("#### Mesh Settings")

        structured_mesh = list_vartype(
            tixi=tixi,
            xpath=GMSH_2D_STRUCTURED_MESH_XPATH,
            default_value=["Structured", "Hybrid"],
            name="Structured or Hybrid Mesh",
            key="structured_mesh",
            description="Choose if you want a structured mesh or a hybrid one."
        )

        default_value = (
            ["CType"]
            if structured_mesh == "Structured"
            else ["Rectangular", "Circular", "CType"]
        )

        farfield_type = list_vartype(
            tixi=tixi,
            xpath=GMSH_2D_FARFIELD_TYPE_XPATH,
            default_value=default_value,
            name="Farfield Type",
            key="farfield_type",
            description="""
                Choose farfield shape (automatically set to CType for structured mesh).
            """,
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
        else:
            safe_remove(tixi, xpath=GMSH_2D_FARFIELD_RADIUS_XPATH)

        if farfield_type == "CType":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_WAKE_LENGTH_XPATH,
                default_value=6.0,
                name="Wake Length",
                key="wake_length",
                description="""
                    Wake length downstream of the airfoil for C-type farfield.
                """,
            )
        else:
            safe_remove(tixi, xpath=GMSH_2D_WAKE_LENGTH_XPATH)

        if farfield_type == "Rectangular":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_LENGTH_XPATH,
                default_value=5.0,
                name="Length",
                key="length",
                description="Length of domain for rectangular farfield.",
            )
        else:
            safe_remove(tixi, xpath=GMSH_2D_LENGTH_XPATH)

        if farfield_type == "CType" or farfield_type == "Rectangular":
            float_vartype(
                tixi=tixi,
                xpath=GMSH_2D_HEIGHT_LENGTH_XPATH,
                default_value=5.0,
                name="Height Length",
                key="height_length",
                description="Height of domain for C-type farfield.",
            )
        else:
            safe_remove(tixi, xpath=GMSH_2D_HEIGHT_LENGTH_XPATH)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    """CPACS2Gmsh GUI Settings."""

    if get_value(cpacs.tixi, GEOMETRY_MODE_XPATH) == "3D":
        _load_3d_gui_settings(cpacs)
    else:
        _load_2d_gui_settings(cpacs)
