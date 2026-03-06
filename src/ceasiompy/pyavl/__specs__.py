"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of PyAVL.
"""

# Imports
import math
from typing import Literal

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    # bool_vartype,
    dataframe_vartype,
)

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
from ceasiompy.utils.commonxpaths import FUSELAGES_XPATH, WINGS_XPATH
from ceasiompy.utils.generalclasses import Point, Transformation
from ceasiompy.utils.geometryfunctions import (
    convert_fuselage_profiles,
    corrects_airfoil_profile,
    elements_number,
    get_positionings,
    get_profile_coord,
    prod_points,
    sum_points,
)
from ceasiompy.utils.mathsfunctions import euler2fix, rotate_points


# Methods
def _distribution_nodes(
    panel_distribution: Literal["cosine", "sine", "equal"],
    panel_count: int,
) -> np.ndarray:
    panel_count = max(1, int(panel_count))
    u = np.linspace(0.0, 1.0, panel_count + 1)

    if panel_distribution == "cosine":
        return 0.5 * (1.0 - np.cos(np.pi * u))
    if panel_distribution == "sine":
        return 1.0 - np.cos(0.5 * np.pi * u)
    return u


def _append_wing_panel_grid_lines(
    le_points: np.ndarray,
    te_points: np.ndarray,
    span_nodes: np.ndarray,
    chord_nodes: np.ndarray,
    x_lines: list,
    y_lines: list,
    z_lines: list,
) -> None:
    section_step = np.linalg.norm(le_points[1:] - le_points[:-1], axis=1)
    section_pos = np.concatenate(([0.0], np.cumsum(section_step)))
    total_span = section_pos[-1]

    if total_span <= 1e-10:
        span_le = np.repeat(le_points[:1], len(span_nodes), axis=0)
        span_te = np.repeat(te_points[:1], len(span_nodes), axis=0)
    else:
        span_target = span_nodes * total_span
        sec_id = np.searchsorted(section_pos, span_target, side="right") - 1
        sec_id = np.clip(sec_id, 0, len(section_step) - 1)
        step = section_step[sec_id]
        local_span = np.divide(
            span_target - section_pos[sec_id],
            step,
            out=np.zeros_like(span_target),
            where=step > 1e-10,
        )
        local_span = local_span[:, np.newaxis]

        span_le = le_points[sec_id] + local_span * (le_points[sec_id + 1] - le_points[sec_id])
        span_te = te_points[sec_id] + local_span * (te_points[sec_id + 1] - te_points[sec_id])

    span_delta = span_te - span_le
    panel_grid = span_le[np.newaxis, :, :] + chord_nodes[:, np.newaxis, np.newaxis] * span_delta

    for i_chord in range(panel_grid.shape[0]):
        x_lines.extend(panel_grid[i_chord, :, 0].tolist() + [None])
        y_lines.extend(panel_grid[i_chord, :, 1].tolist() + [None])
        z_lines.extend(panel_grid[i_chord, :, 2].tolist() + [None])

    for i_span in range(panel_grid.shape[1]):
        x_lines.extend(panel_grid[:, i_span, 0].tolist() + [None])
        y_lines.extend(panel_grid[:, i_span, 1].tolist() + [None])
        z_lines.extend(panel_grid[:, i_span, 2].tolist() + [None])


def _append_fuselage_wireframe(
    cpacs: CPACS,
    span_nodes: np.ndarray,
    chord_nodes: np.ndarray,
    x_lines: list,
    y_lines: list,
    z_lines: list,
) -> None:
    tixi = cpacs.tixi
    fuselage_count = elements_number(tixi, FUSELAGES_XPATH, "fuselage", logg=False)
    if fuselage_count == 0:
        return

    theta_count = max(12, min(48, int(span_nodes.size)))
    theta = np.linspace(0.0, 2.0 * np.pi, theta_count, endpoint=False)
    theta_closed = np.append(theta, theta[0])

    for i_fus in range(fuselage_count):
        fus_xpath = f"{FUSELAGES_XPATH}/fuselage[{i_fus + 1}]"
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath)

        body_transf = Transformation()
        body_transf.translation = fus_transf.translation
        body_transf.rotation = euler2fix(fus_transf.rotation)

        sec_count, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, fus_xpath, "fuselage")
        if sec_count < 2:
            continue

        x_fuselage = np.zeros(sec_count)
        y_fuselage_top = np.zeros(sec_count)
        y_fuselage_bottom = np.zeros(sec_count)

        for i_sec in range(sec_count):
            sec_xpath = f"{fus_xpath}/sections/section[{i_sec + 1}]"
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            elem_root_xpath = sec_xpath + "/elements"
            if not tixi.checkElement(elem_root_xpath):
                continue
            elem_cnt = tixi.getNamedChildrenCount(elem_root_xpath, "element")
            for i_elem in range(elem_cnt):
                elem_transf, prof_size_y, prof_size_z, _, _ = convert_fuselage_profiles(
                    tixi, sec_xpath, i_sec, i_elem, pos_y_list, pos_z_list
                )

                x_center = (
                    elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
                ) * fus_transf.scaling.x
                z_center = (
                    elem_transf.translation.z * sec_transf.scaling.z
                    + sec_transf.translation.z
                    + pos_z_list[i_sec]
                ) * fus_transf.scaling.z

                _, scale_y, scale_z = prod_points(
                    elem_transf.scaling, sec_transf.scaling, fus_transf.scaling
                )
                width = 2.0 * prof_size_y * scale_y
                height = 2.0 * prof_size_z * scale_z
                radius = 0.25 * (width + height)

                x_fuselage[i_sec] = x_center
                y_fuselage_top[i_sec] = z_center + radius
                y_fuselage_bottom[i_sec] = z_center - radius

        radius_sec = 0.5 * (y_fuselage_top - y_fuselage_bottom)
        z_center_sec = 0.5 * (y_fuselage_top + y_fuselage_bottom)
        valid = radius_sec > 1e-8
        if np.count_nonzero(valid) < 2:
            continue

        x_sec = x_fuselage[valid] + body_transf.translation.x
        z_sec = z_center_sec[valid] + body_transf.translation.z
        r_sec = radius_sec[valid]

        sec_step = np.sqrt((x_sec[1:] - x_sec[:-1]) ** 2 + (z_sec[1:] - z_sec[:-1]) ** 2)
        sec_pos = np.concatenate(([0.0], np.cumsum(sec_step)))
        length = sec_pos[-1]
        if length <= 1e-10:
            continue

        target_pos = chord_nodes * length
        x_axis = np.interp(target_pos, sec_pos, x_sec)
        z_axis = np.interp(target_pos, sec_pos, z_sec)
        r_axis = np.interp(target_pos, sec_pos, r_sec)
        y_center = body_transf.translation.y

        for i_sta in range(len(x_axis)):
            ring_x = np.full_like(theta_closed, x_axis[i_sta], dtype=float)
            ring_y = y_center + r_axis[i_sta] * np.cos(theta_closed)
            ring_z = z_axis[i_sta] + r_axis[i_sta] * np.sin(theta_closed)
            x_lines.extend(ring_x.tolist() + [None])
            y_lines.extend(ring_y.tolist() + [None])
            z_lines.extend(ring_z.tolist() + [None])

        meridian_count = min(12, theta_count)
        meridian_idx = np.linspace(0, theta_count - 1, meridian_count, dtype=int)
        for idx in meridian_idx:
            mer_x = x_axis
            mer_y = y_center + r_axis * np.cos(theta[idx])
            mer_z = z_axis + r_axis * np.sin(theta[idx])
            x_lines.extend(mer_x.tolist() + [None])
            y_lines.extend(mer_y.tolist() + [None])
            z_lines.extend(mer_z.tolist() + [None])


def _display_panel_representation(
    cpacs: CPACS,
    spanwise_vertices: int,
    chordwise_vertices: int,
    panel_distribution: Literal["cosine", "sine", "equal"],
) -> None:
    tixi = cpacs.tixi
    wing_count = elements_number(tixi, WINGS_XPATH, "wing", logg=False)
    fuselage_count = elements_number(tixi, FUSELAGES_XPATH, "fuselage", logg=False)
    if wing_count == 0 and fuselage_count == 0:
        st.info("No wing or fuselage geometry found for AVL panel preview.")
        return

    span_nodes = _distribution_nodes(panel_distribution, spanwise_vertices)
    chord_nodes = _distribution_nodes(panel_distribution, chordwise_vertices)

    x_lines = []
    y_lines = []
    z_lines = []

    _append_fuselage_wireframe(
        cpacs=cpacs,
        span_nodes=span_nodes,
        chord_nodes=chord_nodes,
        x_lines=x_lines,
        y_lines=y_lines,
        z_lines=z_lines,
    )

    for i_wing in range(wing_count):
        wing_xpath = f"{WINGS_XPATH}/wing[{i_wing + 1}]"

        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)
        wg_sk_transf = Transformation()
        wg_sk_transf.rotation = euler2fix(wing_transf.rotation)
        wg_sk_transf.translation = wing_transf.translation

        sec_count, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, wing_xpath, "wing")
        if sec_count < 2:
            continue

        all_pos_y_zero = all(abs(value) < 1e-6 for value in pos_y_list)
        le_points = []
        te_points = []

        for i_sec in range(sec_count):
            sec_xpath = f"{wing_xpath}/sections/section[{i_sec + 1}]"
            elem_xpath = f"{sec_xpath}/elements/element[1]"
            if not tixi.checkElement(elem_xpath):
                continue

            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)
            elem_transf = Transformation()
            elem_transf.get_cpacs_transf(tixi, elem_xpath)

            _, prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
                tixi, elem_xpath + "/airfoilUID"
            )
            scale_x, scale_y, scale_z = prod_points(elem_transf.scaling, sec_transf.scaling)
            prof_vect_x *= scale_x
            prof_vect_y *= scale_y
            prof_vect_z *= scale_z
            chord = float(corrects_airfoil_profile(prof_vect_x, prof_vect_y, prof_vect_z))

            rot_x, rot_y, rot_z = sum_points(
                elem_transf.rotation,
                sec_transf.rotation,
                wg_sk_transf.rotation,
            )
            sec_rot = euler2fix(Point(x=rot_x, y=rot_y, z=rot_z))
            sec_dihed = math.radians(sec_rot.x)
            sec_twist = math.radians(sec_rot.y)
            sec_yaw = math.radians(sec_rot.z)

            if all_pos_y_zero:
                x_le, y_le, z_le = sum_points(sec_transf.translation, elem_transf.translation)
                x_le_rot, y_le_rot, z_le_rot = rotate_points(
                    x_le,
                    y_le,
                    z_le,
                    sec_dihed,
                    sec_twist,
                    sec_yaw,
                )
            else:
                x_le_rot, y_le_rot, z_le_rot = rotate_points(
                    pos_x_list[i_sec],
                    pos_y_list[i_sec],
                    pos_z_list[i_sec],
                    sec_dihed,
                    sec_twist,
                    sec_yaw,
                )

            ainc = math.radians(sec_rot.y)
            x_te_rot = x_le_rot + chord * math.cos(ainc)
            y_te_rot = y_le_rot
            z_te_rot = z_le_rot - chord * math.sin(ainc)

            le_points.append(
                [
                    x_le_rot * wing_transf.scaling.x + wg_sk_transf.translation.x,
                    y_le_rot * wing_transf.scaling.y + wg_sk_transf.translation.y,
                    z_le_rot * wing_transf.scaling.z + wg_sk_transf.translation.z,
                ]
            )
            te_points.append(
                [
                    x_te_rot * wing_transf.scaling.x + wg_sk_transf.translation.x,
                    y_te_rot * wing_transf.scaling.y + wg_sk_transf.translation.y,
                    z_te_rot * wing_transf.scaling.z + wg_sk_transf.translation.z,
                ]
            )

        if len(le_points) < 2:
            continue

        le_arr = np.array(le_points)
        te_arr = np.array(te_points)
        _append_wing_panel_grid_lines(
            le_points=le_arr,
            te_points=te_arr,
            span_nodes=span_nodes,
            chord_nodes=chord_nodes,
            x_lines=x_lines,
            y_lines=y_lines,
            z_lines=z_lines,
        )

        if tixi.checkAttribute(wing_xpath, "symmetry") and tixi.getTextAttribute(
            wing_xpath, "symmetry"
        ) == "x-z-plane":
            le_arr_mirror = le_arr.copy()
            te_arr_mirror = te_arr.copy()
            le_arr_mirror[:, 1] *= -1.0
            te_arr_mirror[:, 1] *= -1.0
            _append_wing_panel_grid_lines(
                le_points=le_arr_mirror,
                te_points=te_arr_mirror,
                span_nodes=span_nodes,
                chord_nodes=chord_nodes,
                x_lines=x_lines,
                y_lines=y_lines,
                z_lines=z_lines,
            )

    if not x_lines:
        st.info("Not enough wing sections to build an AVL panel preview.")
        return

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x_lines,
                y=y_lines,
                z=z_lines,
                mode="lines",
                line={"color": "#1f77b4", "width": 2},
                hoverinfo="skip",
                name="AVL panel grid",
            )
        ]
    )
    fig.update_layout(
        height=300,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        scene={
            "xaxis_title": "X [m]",
            "yaxis_title": "Y [m]",
            "zaxis_title": "Z [m]",
            "aspectmode": "data",
        },
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch", key="pyavl_panel_geometry_preview")


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

        vortices_left_col, vortices_right_col = st.columns(2)
        with vortices_left_col:
            chordwise_vertices = int_vartype(
                tixi=tixi,
                name="Chordwise vortices",
                key="pyavl_chordwise_vortices_nb",
                default_value=20,
                help="Select the number of chordwise vortices.",
                xpath=AVL_NCHORDWISE_XPATH,
            )

        with vortices_right_col:
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
