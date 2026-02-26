"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.
"""

# Imports
import pyvista as pv
import streamlit as st
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.commonpaths import get_wkdir
from ceasiompy.cpacs2gmsh.utility.farfield import box_edges
from ceasiompy.utils.ceasiompyutils import (
    safe_remove,
    get_selected_aeromap,
)
from ceasiompy.cpacs2gmsh.utility.mesh_sizing import (
    get_wing_ref_chord,
    get_fuselage_mean_circumference,
)
from ceasiompy.utils.guiobjects import (
    int_vartype,
    bool_vartype,
    float_vartype,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from numpy import sqrt
from ceasiompy import log
from ceasiompy.to3d import MODULE_NAME as TO3D
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.cpacs2gmsh import (
    MODULE_NAME as CPACS2GMSH,
    HAS_PENTAGROW,
    GMSH_XZ_SYMMETRY_XPATH,
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
    GMSH_UPSTREAM_LENGTH_XPATH,
    GMSH_WAKE_LENGTH_XPATH,
    GMSH_Y_LENGTH_XPATH,
    GMSH_Z_LENGTH_XPATH,
)


# Methods
def _get_aircraft_preview_surface(
    cpacs: CPACS,
    symmetry: bool,
    force_regenerate: bool = False,
) -> None:
    """Export/load aircraft preview as VTK and optionally clip to y >= 0 for symmetry."""

    suffix = "_symmetry" if symmetry else ""
    vtp_file = Path(get_wkdir(), f"{cpacs.ac_name.lower()}{suffix}.vtp")

    if force_regenerate or not vtp_file.exists():
        try:
            with st.spinner("Meshing geometry (preview export)..."):
                cpacs.aircraft.tigl.exportMeshedGeometryVTK(str(vtp_file), 0.01)
        except Exception as e:
            st.warning(f"Cannot generate CPACS VTK mesh preview: {e}")
            return None

    try:
        pv_mesh = pv.read(str(vtp_file))
        surface = pv_mesh.extract_surface(algorithm="dataset_surface").triangulate().clean()
        if symmetry:
            # Keep only the positive-y half-space for XZ-symmetry previews/bounds.
            surface = surface.clip(normal=(0, 1, 0), origin=(0, 0, 0), invert=False)
        if surface.n_cells == 0:
            st.warning("No mesh cells available for CPACS 3D preview.")
            return None
        # Keep displayed geometry in positive axes for intuitive bounds/labels.
        sx_min, sx_max, sy_min, sy_max, sz_min, sz_max = surface.bounds
        _ = (sx_max, sy_max, sz_max)
        surface.points[:, 0] -= sx_min
        surface.points[:, 1] -= sy_min
        surface.points[:, 2] -= sz_min
        return surface
    except Exception as e:
        st.warning(f"Cannot load CPACS VTK preview mesh: {e}")
        return None


def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi
    aircraft = cpacs.aircraft
    aircraft_config = aircraft.configuration

    # Sanity Check
    if get_value(tixi, GEOMETRY_MODE_XPATH) != "3D":
        if TO3D in st.session_state.get("workflow_modules", None):
            log.info("gmsh will be called on 3D variant.")
        else:
            raise ValueError(f"You can not call {CPACS2GMSH} on a 2D geometry.")

    left_col, right_col = st.columns([3, 1])
    with right_col:
        has_sideslip = False
        for beta in get_selected_aeromap(cpacs).get(list_of="angleOfSideslip").tolist():
            if beta != 0.0:
                has_sideslip = True
        symmetry = bool_vartype(
            tixi=tixi,
            xpath=GMSH_XZ_SYMMETRY_XPATH,
            default_value=not has_sideslip,
            name="XZ-Symmetry",
            help=f"""Mesh half or the entire domain.
                {
                    " Found non-zero sidelip angle, disabling xz-symmetry."
                    if has_sideslip
                    else ""
                }""",
            key=f"cpacs2gmsh_xz_symmetry_{has_sideslip}",
            disabled=has_sideslip,
        )

    with left_col:
        # Bounding Box for General Aircraft Settings
        x_min, y_min, z_min, x_max, y_max, z_max = aircraft.tigl.configurationGetBoundingBox()
        surface = _get_aircraft_preview_surface(
            cpacs=cpacs,
            symmetry=symmetry,
        )
        if surface is not None:
            x_min, x_max, y_min, y_max, z_min, z_max = surface.bounds
        if symmetry:
            y_min = max(0.0, y_min)
        vec = {
            "x": abs(x_max - x_min),
            "y": abs(y_max - y_min),
            "z": abs(z_max - z_min),
        }
        # Keep displayed aircraft bounding box in [0, max] on each axis.
        x_min, y_min, z_min = 0.0, 0.0, 0.0
        x_max, y_max, z_max = vec["x"], vec["y"], vec["z"]
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
        surface=surface,
    )

    st.markdown("---")
    # TODO: Make a preview of the farfield meshing with the farfield mesh size
    float_vartype(
        tixi=tixi,
        xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
        default_value=round(radius / 4.0, 3),
        name="Farfield mesh size",
        key="farfield_size",
        help=f"""Farfield mesh size, for reference
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
                        default_value=ref_chord / 40.0,
                        min_value=0.0,
                        max_value=ref_chord,
                        name=f"Wing: {wing_uid} mesh size",
                        key=f"cpacs2gmsh_wing_mesh_size_{wing_uid}",
                        help=f"""
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
                        default_value=fus_mean_circumference / 60.0,
                        min_value=0.0,
                        max_value=fus_mean_circumference,
                        name=f"Fuselage: {fus_uid} mesh size",
                        key=f"cpacs2gmsh_fuselage_mesh_size_{fus_uid}",
                        help=f"""Cell size on the fuselage
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
                        help=f"""Cell size on the pylon
                            {pylon_uid}.""",
                    )

    disabled = False if HAS_PENTAGROW else True
    add_boundary_layer = bool_vartype(
        tixi=tixi,
        xpath=GMSH_ADD_BOUNDARY_LAYER_XPATH,
        default_value=False,
        name="Add Boundary Layer",
        key="cpacs2gmsh_add_boundary_layer",
        help="Boundary Layer made with Pentagrow.",
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
                    default_value=3,
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
                    default_value=100.0,
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
            xpath=GMSH_REFINE_TRUNCATED_XPATH,
            default_value=False,
            name="Refine truncated TE",
            key="refine_truncated",
            help="Enable the refinement of truncated trailing edge.",
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
    #                 help="""
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
    #                 help="""Position of the exhaust surface boundary
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
    #         help="List of Aileron, Elevator, Rudder angles.",
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
    surface=None,
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
            help="Length from upstream farfield to the aircraft's nose.",
            key="cpacs2gmsh_upstream_length",
            xpath=GMSH_UPSTREAM_LENGTH_XPATH,
            default_value=round(vec["x"], ndigits=3),
            min_value=(delta_x := vec["x"] / 10.0),
            step=delta_x,
            max_value=5.0 * vec["x"],
        )

    with right_col:
        wake_length = float_vartype(
            tixi=tixi,
            name="Wake Length",
            help="Downstream length: distance from farfield to the aircraft's tail.",
            key="cpacs2gmsh_wake_length",
            xpath=GMSH_WAKE_LENGTH_XPATH,
            default_value=round(1.5 * vec["x"], ndigits=3),
            min_value=(delta_x := vec["x"] / 10.0),
            step=delta_x,
            max_value=5.0 * vec["x"],
        )

    left_col, right_col = st.columns(2)
    with left_col:
        y_length = float_vartype(
            tixi=tixi,
            name="Y-length",
            help="Length to add in the y-direction.",
            xpath=GMSH_Y_LENGTH_XPATH,
            key="cpacs2gmsh_y_length",
            default_value=round(vec["y"], ndigits=3),
            min_value=(delta_y := vec["y"] / 10.0),
            step=delta_y,
            max_value=2 * vec["y"],
        )
    with right_col:
        z_length = float_vartype(
            tixi=tixi,
            name="Z-length",
            help="Length to add in the z-direction.",
            xpath=GMSH_Z_LENGTH_XPATH,
            key="cpacs2gmsh_z_length",
            default_value=round(3.0 * vec["z"], ndigits=3),
            min_value=(delta_z := vec["z"] / 10.0),
            step=delta_z,
            max_value=vec["z"] * 10.0,
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
        y_min=0.0 if symmetry else y_min - y_length,
        z_min=z_min - z_length,
        x_max=x_max + wake_length,
        y_max=y_max + y_length,
        z_max=z_max + z_length,
        symmetry=symmetry,
    )
    outer_x_min = x_min - upstream_length
    outer_x_max = x_max + wake_length
    outer_y_min = 0.0 if symmetry else y_min - y_length
    outer_y_max = y_max + y_length
    outer_z_min = z_min - z_length
    outer_z_max = z_max + z_length

    fig = go.Figure()
    try:
        if surface is None:
            surface = _get_aircraft_preview_surface(
                cpacs=cpacs,
                symmetry=symmetry,
            )

        if surface is None:
            st.warning(f"Can not display {cpacs.ac_name=}. Could not retrieve VTK mesh data.")
            return None

        faces = surface.faces.reshape(-1, 4)
        if faces.size == 0:
            st.warning("No mesh faces available for CPACS 3D preview.")
            return None

        fig.add_trace(
            go.Mesh3d(
                x=surface.points[:, 0],
                y=surface.points[:, 1],
                z=surface.points[:, 2],
                i=faces[:, 1],
                j=faces[:, 2],
                k=faces[:, 3],
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
        st.warning(f"Cannot generate CPACS VTK preview: {e}")

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

    def _axis_values(vmin: float, vmax: float, count: int) -> list[float]:
        if count <= 0:
            return []
        if count == 1:
            return [(vmin + vmax) * 0.5]
        step = (vmax - vmin) / (count - 1)
        return [vmin + i * step for i in range(count)]

    x_ticks = _axis_values(outer_x_min, outer_x_max, 3)
    y_ticks = _axis_values(outer_y_min, outer_y_max, 3)
    z_ticks = _axis_values(outer_z_min, outer_z_max, 2)

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        font=dict(color="black"),
        scene=dict(
            aspectmode="data",
            xaxis=dict(
                title="X",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[outer_x_min, outer_x_max],
                tickmode="array",
                tickvals=x_ticks,
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
            yaxis=dict(
                title="Y",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[outer_y_min, outer_y_max],
                tickmode="array",
                tickvals=y_ticks,
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
            zaxis=dict(
                title="Z",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[outer_z_min, outer_z_max],
                tickmode="array",
                tickvals=z_ticks,
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
            camera=dict(
                eye=dict(x=2.2, y=2.2, z=1.8),
                up=dict(x=0.0, y=0.0, z=1.0),
                center=dict(x=0.0, y=0.0, z=0.0),
            ),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )
    domain_preview_placeholder.plotly_chart(
        fig,
        width="stretch",
        key="cpacs2gmsh_domain_preview",
    )
