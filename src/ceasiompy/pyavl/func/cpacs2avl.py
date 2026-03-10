"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to convert CPACS file geometry into AVL geometry
"""

# Imports

import math
import numpy as np

from cpacspy.cpacsfunctions import (
    get_uid,
    get_value,
)
from ceasiompy.utils.mathsfunctions import (
    euler2fix,
    rotate_points,
)
from ceasiompy.pyavl.func.utils import (
    write_control,
    to_cpacs_format,
    get_points_ref,
    convert_dist_to_avl_format,
)
from ceasiompy.utils.geometryfunctions import (
    sum_points,
    prod_points,
    get_profile_coord,
    check_if_rotated,
    get_chord_span,
    elements_number,
    get_positionings,
    convert_fuselage_profiles,
    corrects_airfoil_profile,
)

from pathlib import Path
from numpy import ndarray
from tixi3.tixi3wrapper import Tixi3
from tigl3.tigl3wrapper import Tigl3
from typing import (
    List,
    Tuple,
)
from ceasiompy.utils.generalclasses import (
    Point,
    Transformation,
)

from ceasiompy import log
from ceasiompy.pyavl import (
    AVL_DISTR_XPATH,
    # AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    # AVL_FREESTREAM_MACH_XPATH,
)
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    WINGS_XPATH,
    LENGTH_XPATH,
    FUSELAGES_XPATH,
    AIRCRAFT_NAME_XPATH,
)

# Functions


def compute_fuselage_coords(
    i_sec: int,
    elem_transf: Transformation,
    sec_transf: Transformation,
    fus_transf: Transformation,
    pos_x_list: List,
    pos_z_list: List,
    prof_size_y,
    prof_size_z,
    fus_radius_vec,
    x_fuselage,
    y_fuselage_top,
    y_fuselage_bottom,
):
    # Compute coordinates of the center of section
    body_frm_center_x = (
        elem_transf.translation.x
        * sec_transf.scaling.x
        + sec_transf.translation.x
        + pos_x_list[i_sec]
    ) * fus_transf.scaling.x

    body_frm_center_z = (
        elem_transf.translation.z * sec_transf.scaling.z
        + sec_transf.translation.z
        + pos_z_list[i_sec]
    ) * fus_transf.scaling.z

    # Compute height and width of the section
    _, y, z = prod_points(elem_transf.scaling, sec_transf.scaling, fus_transf.scaling)
    body_frm_width = 2 * prof_size_y * y
    body_frm_height = 2 * prof_size_z * z

    # AVL assumes a round cross-section whose diameter equals (top - bottom).
    # For non-circular CPACS sections, use the average of half-width and
    # half-height as the equivalent round radius (matches the GUI wireframe).
    equiv_radius = 0.25 * (body_frm_width + body_frm_height)
    fus_radius_vec[i_sec] = body_frm_width / 2  # half-width for wing clipping

    x_fuselage[i_sec] = body_frm_center_x
    y_fuselage_top[i_sec] = body_frm_center_z + equiv_radius
    y_fuselage_bottom[i_sec] = body_frm_center_z - equiv_radius

    return body_frm_width, body_frm_height


def extract_fuselage_profile_tigl(
    tixi: Tixi3,
    fus_uid: str,
    n_output: int = 80,
    n_zeta: int = 12,
) -> Tuple[ndarray, ndarray, ndarray, ndarray]:
    """Extract the exact fuselage profile by slicing the TiGL geometry.

    Uses ``fuselageGetPoint`` to sample the actual lofted surface at
    multiple zeta values around the cross-section for every eta
    station along each segment.  The y/z extents are computed from
    the bounding box of the sampled points (robust to any
    cross-section orientation).

    The raw samples are then resampled to *n_output* evenly spaced
    points along the fuselage arc length.

    Returns:
        x      – streamwise coordinate of each station (sorted, *n_output* points).
        z_ctr  – vertical centre of the cross-section.
        half_w – half-width  (y-direction) at each station.
        half_h – half-height (z-direction) at each station.
        Returns four empty arrays if TiGL produces a degenerate profile.
    """
    tigl = Tigl3()
    tigl.open(tixi, "")

    fus_idx = tigl.fuselageGetIndex(fus_uid)
    seg_cnt = tigl.fuselageGetSegmentCount(fus_idx)

    # Adapt samples per segment so the total stays reasonable
    n_per_seg = max(4, min(15, 120 // max(1, seg_cnt)))

    # Zeta values around the circumference for bounding-box estimation
    zetas = np.linspace(0.0, 1.0, n_zeta, endpoint=False)

    xs, zcs, hws, hhs = [], [], [], []

    for i_seg in range(1, seg_cnt + 1):
        is_last = i_seg == seg_cnt
        etas = np.linspace(0.0, 1.0, n_per_seg, endpoint=is_last)
        if not is_last:
            etas = etas[:-1]  # avoid duplicates at segment boundaries

        for eta in etas:
            # Sample the cross-section at multiple zeta values
            pts_x, pts_y, pts_z = [], [], []
            for zeta in zetas:
                px, py, pz = tigl.fuselageGetPoint(fus_idx, i_seg, eta, zeta)
                pts_x.append(px)
                pts_y.append(py)
                pts_z.append(pz)

            # Compute bounding box of cross-section
            y_min, y_max = min(pts_y), max(pts_y)
            z_min, z_max = min(pts_z), max(pts_z)

            xs.append(np.mean(pts_x))
            zcs.append(0.5 * (z_max + z_min))
            hws.append(0.5 * (y_max - y_min))
            hhs.append(0.5 * (z_max - z_min))

    x = np.asarray(xs)
    z_ctr = np.asarray(zcs)
    half_w = np.asarray(hws)
    half_h = np.asarray(hhs)

    # If TiGL returned a degenerate profile (e.g. needle-thin body), bail out
    if np.max(half_w) + np.max(half_h) < 1e-6:
        empty = np.array([])
        return empty, empty, empty, empty

    # Sort by x
    order = np.argsort(x)
    x, z_ctr, half_w, half_h = x[order], z_ctr[order], half_w[order], half_h[order]

    # Build arc-length parameterisation and resample to n_output points
    ds = np.sqrt(np.diff(x) ** 2 + np.diff(z_ctr) ** 2)
    s = np.concatenate(([0.0], np.cumsum(ds)))
    total_len = s[-1]
    if total_len < 1e-10:
        empty = np.array([])
        return empty, empty, empty, empty

    target = np.linspace(0.0, total_len, n_output)
    x_out = np.interp(target, s, x)
    z_out = np.interp(target, s, z_ctr)
    hw_out = np.interp(target, s, half_w)
    hh_out = np.interp(target, s, half_h)

    return x_out, z_out, hw_out, hh_out


def leadingedge_coordinates(
    tixi: Tixi3,
    avl_path,
    i_wing,
    i_sec,
    x_le_rot,
    y_le_rot,
    z_le_rot,
    wg_sec_chord,
    wg_sec_rot,
    wing_xpath,
    c_ref,
    s_ref,
    foil_dat_path,
) -> None:

    # Write the leading edge coordinates and the airfoil file
    with open(avl_path, "a") as avl_file:
        avl_file.write("#---------------\nSECTION\n")
        avl_file.write("#Xle    Yle    Zle     Chord   Ainc\n")
        avl_file.write(
            f"{x_le_rot:.3f} {y_le_rot:.3f} {z_le_rot:.3f} "
            f"{(wg_sec_chord):.3f} {wg_sec_rot.y}\n"
        )

        edge_xpath = "/componentSegments/componentSegment"
        bis_xpath = "/controlSurfaces/trailingEdgeDevices"
        control_xpath_base = wing_xpath + edge_xpath + bis_xpath
        # Check if the control surfaces path exists
        if tixi.checkElement(control_xpath_base):

            num_devices = tixi.getNumberOfChilds(control_xpath_base)

            for i in range(1, num_devices + 1):
                control_xpath = f"{control_xpath_base}/trailingEdgeDevice[{i}]"
                control_uid = tixi.getTextAttribute(control_xpath, "uID")
                innerhinge_xsi_xpath = control_xpath + "/path/innerHingePoint/hingeXsi"
                outerhinge_xsi_xpath = control_xpath + "/path/outerHingePoint/hingeXsi"
                innerhinge_xsi = float(get_value(tixi, innerhinge_xsi_xpath))
                outerhinge_xsi = float(get_value(tixi, outerhinge_xsi_xpath))

                inner_eta_xpath = control_xpath + "/outerShape/innerBorder/etaTE/eta"
                outer_eta_xpath = control_xpath + "/outerShape/outerBorder/etaTE/eta"

                inner_eta = float(get_value(tixi, inner_eta_xpath))
                outer_eta = float(get_value(tixi, outer_eta_xpath))

                x_axis = (outerhinge_xsi - innerhinge_xsi) * c_ref
                y_axis = (outer_eta - inner_eta) * s_ref
                z_axis = 0.0

                control_dict = {
                    "InnerFlap": {
                        "i_sec": [0, 1],
                        "type": "flap",
                        "axis": f"{x_axis} {y_axis} {z_axis}",
                        "bool": [1.0, 1.0],
                    },
                    "OuterFlap": {
                        "i_sec": [1, 2],
                        "type": "flap",
                        "axis": f"{x_axis} {y_axis} {z_axis}",
                        "bool": [1.0, 1.0],
                    },
                    "Aileron": {
                        "i_sec": [2, 3],
                        "type": "aileron",
                        "axis": f"{x_axis} {y_axis} {z_axis}",
                        "bool": [-1.0, -1.0],
                    },
                    "Elevator": {
                        "i_sec": [0, 1],
                        "type": "elevator",
                        "axis": f"{x_axis} {y_axis} {z_axis}",
                        "bool": [1.0, 1.0],
                    },
                    "Rudder": {
                        "i_sec": [0, 1],
                        "type": "rudder",
                        "axis": f"{x_axis} {z_axis} {y_axis}",
                        "bool": [-1.0, -1.0],
                    },
                }
                control = control_dict.get(control_uid, None)
                if control is None:
                    continue
                control_type = control["type"]
                if i_sec == control["i_sec"][0]:
                    write_control(
                        avl_file,
                        control_type,
                        innerhinge_xsi,
                        control["axis"],
                        control["bool"][0],
                    )
                elif i_sec == control["i_sec"][1]:
                    write_control(
                        avl_file,
                        control_type,
                        outerhinge_xsi,
                        control["axis"],
                        control["bool"][1],
                    )
                else:
                    log.warning(
                        f"Issue with {control_uid} control surface "
                        f"at section {i_sec} of wing number {i_wing}."
                    )
        else:
            log.warning(
                f"Did not find control surfaces xpath {control_xpath_base=}."
                "Thus AVL can not deflect nor specify where are the control surfaces."
            )

        avl_file.write("AFILE\n")
        avl_file.write(foil_dat_path + "\n\n")


def write_airfoil_coords(
    foil_dat_path: Path,
    prof_uid: str,
    prof_vect_x: ndarray,
    prof_vect_z: ndarray,
) -> None:
    """
    No need to add in Avl class.
    """
    with open(foil_dat_path, "w") as dat_file:
        dat_file.write(prof_uid + "\n")

        prof_x_len = len(prof_vect_x)

        # Limit the number of points to 100 (otherwise AVL error)
        if prof_x_len >= 100:
            log.warning("Limiting the number of points.")
            step = round(prof_x_len / 100)
            prof_vect_x = prof_vect_x[0:prof_x_len:step]
            prof_vect_z = prof_vect_z[0:prof_x_len:step]

        for coord_x, coord_z in zip(prof_vect_x, prof_vect_z):
            dat_file.write(f"{coord_x}\t{coord_z}\n")


# =================================================================================================
#   CLASS
# =================================================================================================


class Avl:
    def __init__(
        self: "Avl",
        tixi: Tixi3,
        results_dir: Path,
        gain: float = 0.0,
        control_type: str = "none",
    ) -> None:
        # Store input variables
        self.tixi = tixi
        self.results_dir = results_dir

        self.gain = gain
        self.control_type = control_type

        self.vortex_dist: int = convert_dist_to_avl_format(str(get_value(tixi, AVL_DISTR_XPATH)))
        self.nchordwise: int = int(get_value(tixi, AVL_NCHORDWISE_XPATH))
        self.nspanwise: int = int(get_value(tixi, AVL_NSPANWISE_XPATH))
        self.add_fuselage: bool = True  # get_value(tixi, AVL_FUSELAGE_XPATH)
        # Keep wing geometry unchanged by default; enable only when explicit clipping is desired.
        self.clip_wing_inside_fuselage: bool = False

        self.area_ref: float = tixi.getDoubleElement(AREA_XPATH)
        self.chord_ref: float = tixi.getDoubleElement(LENGTH_XPATH)
        self.span_ref: float = self.area_ref / self.chord_ref
        self.points_ref: ndarray = get_points_ref(tixi)

        # .avl file type
        self.name_aircraft = self.tixi.getTextElement(AIRCRAFT_NAME_XPATH)
        if gain == 0.0:
            self.avl_path = (
                str(self.results_dir) + "/" + self.name_aircraft + ".avl"
            )
        else:
            self.avl_path = (
                str(self.results_dir) + "/" + self.name_aircraft
                + "gain" + str(gain)
                + "ctrl" + control_type
                + ".avl"
            )

    def initialize_avl_command_file(self) -> None:
        with open(self.avl_path, "w") as avl_file:
            avl_file.write(self.name_aircraft + "\n\n")

    def convert_cpacs_to_avl(self) -> Path:
        """
        Convert a CPACS file geometry into an AVL file geometry.

        Workflow:
            1. Initialize command file .avl
            2. Convert fuselage (if included)
            3. Convert wings

        Returns:
            (Path): Path to the AVL input file.
        """

        # 1. Initialize command file .avl
        self.initialize_avl_command_file()

        mach = 0.6  # get_value(self.tixi, AVL_FREESTREAM_MACH_XPATH)
        with open(self.avl_path, "a") as avl_file:
            # Default freestream mach number
            avl_file.write("#Mach\n")
            avl_file.write(f"{mach}\n\n")

            # No Symmetry assumed
            avl_file.write("#IYsym   IZsym   Zsym\n")
            avl_file.write("0\t0\t0\n\n")

        self.write_ref_values()

        # 2. Convert fuselage (if included)
        fus_x_coords, fus_z_profile, fus_radius_profile, body_transf = None, None, None, None
        if self.add_fuselage:
            fus_x_coords, fus_z_profile, fus_radius_profile, body_transf = self.convert_fuselage()

        # 3. Convert wings
        self.convert_wings(
            fus_x_coords,
            fus_radius_profile,
            fus_z_profile,
            body_transf,
        )

        return Path(self.avl_path)

    def convert_fuselage(
        self: "Avl",
    ) -> Tuple[ndarray, ndarray, ndarray, Transformation]:
        """
        Convert fuselages from CPACS to avl format.

        Workflow:
            For each fuselage
                1. Write fuselage settings
                For each sections
                    2. Write the fuselage coordinates

        """

        fus_cnt = elements_number(self.tixi, FUSELAGES_XPATH, "fuselage")
        # AVL's internal MAKEBODY buffer is finite (NLMAX, typically 500).
        # Count effective bodies including YDUPLICATE mirrors.
        max_total_nbody = 480
        effective_body_cnt = 0
        for i in range(fus_cnt):
            fus_xp = FUSELAGES_XPATH + "/fuselage[" + str(i + 1) + "]"
            is_symmetric = (
                self.tixi.checkAttribute(fus_xp, "symmetry")
                and self.tixi.getTextAttribute(fus_xp, "symmetry") == "x-z-plane"
            )
            effective_body_cnt += 2 if is_symmetric else 1
        nbody_per_fuselage = max(20, min(100, max_total_nbody // max(1, effective_body_cnt)))

        fus_x_coords = np.array([])
        fus_z_profile = np.array([])
        fus_radius_profile = np.array([])
        body_transf = Transformation()

        for i_fus in reversed(range(fus_cnt)):
            fus_xpath = FUSELAGES_XPATH + "/fuselage[" + str(i_fus + 1) + "]"
            fus_uid = get_uid(self.tixi, fus_xpath)

            fuselages_dir = str(self.results_dir) + "/fuselages"
            Path(fuselages_dir).mkdir(exist_ok=True)
            fus_dat_path = fuselages_dir + "/" + fus_uid + ".dat"

            fus_transf = Transformation()
            fus_transf.get_cpacs_transf(self.tixi, fus_xpath)

            body_transf = Transformation()
            body_transf.translation = fus_transf.translation
            body_transf.rotation = euler2fix(fus_transf.rotation)

            # Check with TiGL first whether this fuselage has a valid profile
            x_tigl, z_ctr_tigl, hw_tigl, hh_tigl = extract_fuselage_profile_tigl(
                self.tixi, fus_uid,
            )
            if len(x_tigl) < 2:
                log.warning(
                    f"TiGL returned a degenerate profile for fuselage '{fus_uid}'; "
                    "skipping this body entirely."
                )
                continue

            # 1. Write fuselage settings (only for valid bodies)
            # TiGL output already includes fuselage scaling, so pass identity
            # to avoid double-scaling in AVL.
            self.write_fuselage_settings(
                fus_xpath,
                Point(1.0, 1.0, 1.0),
                body_transf.translation,
                nbody=nbody_per_fuselage,
            )

            sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
                self.tixi, fus_xpath, "fuselage"
            )

            # Initialize to null array of size [sec_cnt]
            (
                x_fuselage,
                y_fuselage_top,
                y_fuselage_bottom,
                fus_radius_vec,
                body_width_vec,
                body_height_vec,
            ) = (np.zeros(sec_cnt) for _ in range(6))

            for i_sec in range(sec_cnt):
                sec_xpath = fus_xpath + "/sections/section[" + str(i_sec + 1) + "]"
                sec_uid = self.tixi.getTextAttribute(sec_xpath, "uID")
                sec_transf = Transformation()
                sec_transf.get_cpacs_transf(self.tixi, sec_xpath)
                check_if_rotated(sec_transf.rotation, sec_uid)

                elem_root_xpath = sec_xpath + "/elements"
                if not self.tixi.checkElement(elem_root_xpath):
                    continue
                elem_cnt = self.tixi.getNamedChildrenCount(elem_root_xpath, "element")

                for i_elem in range(elem_cnt):
                    elem_transf, prof_size_y, prof_size_z, _, _ = convert_fuselage_profiles(
                        self.tixi, sec_xpath, i_sec, i_elem, pos_y_list, pos_z_list
                    )

                    body_frm_width, body_frm_height = compute_fuselage_coords(
                        i_sec,
                        elem_transf,
                        sec_transf,
                        fus_transf,
                        pos_x_list,
                        pos_z_list,
                        prof_size_y,
                        prof_size_z,
                        fus_radius_vec,
                        x_fuselage,
                        y_fuselage_top,
                        y_fuselage_bottom,
                    )

                    body_width_vec[i_sec] = body_frm_width
                    body_height_vec[i_sec] = body_frm_height

            # Filter out sections with near-zero radius, but always keep first/last
            valid = fus_radius_vec > 1e-8
            if sec_cnt > 0:
                valid[0] = True
                valid[-1] = True

            x_fuselage = x_fuselage[valid]
            y_fuselage_top = y_fuselage_top[valid]
            y_fuselage_bottom = y_fuselage_bottom[valid]
            fus_radius_vec = fus_radius_vec[valid]

            body_transf_x = x_fuselage + body_transf.translation.x
            body_fus_z = y_fuselage_top - fus_radius_vec
            body_fus_radius = fus_radius_vec

            sort_idx = np.argsort(body_transf_x)
            body_transf_x_sorted = body_transf_x[sort_idx]
            body_fus_z_sorted = body_fus_z[sort_idx]
            body_fus_radius_sorted = body_fus_radius[sort_idx]
            fus_x_coords, unique_idx = np.unique(body_transf_x_sorted, return_index=True)
            fus_z_profile = body_fus_z_sorted[unique_idx]
            fus_radius_profile = body_fus_radius_sorted[unique_idx]

            # Write the BFILE using the pre-computed TiGL profile
            self.write_fuselage_coords_from_tigl(
                fus_dat_path,
                i_fus,
                x_tigl, z_ctr_tigl, hw_tigl, hh_tigl,
                body_translation=body_transf.translation,
            )

        return fus_x_coords, fus_z_profile, fus_radius_profile, body_transf

    def convert_wings(
        self: "Avl",
        fus_x_coords: ndarray,
        fus_radius_profile: ndarray,
        fus_z_profile: ndarray,
        body_transf: Transformation,
    ) -> None:
        wing_cnt = elements_number(self.tixi, WINGS_XPATH, "wing")

        for i_wing in range(wing_cnt):
            root_defined = False
            wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"

            # Retrieve chord and span length of specific wing
            c_ref, s_ref = get_chord_span(self.tixi, wing_xpath)

            wing_transf = Transformation()
            wing_transf.get_cpacs_transf(self.tixi, wing_xpath)

            # Create a class for the transformation of the WingSkeleton
            wg_sk_transf = Transformation()
            wg_sk_transf.rotation = euler2fix(wing_transf.rotation)
            wg_sk_transf.translation = wing_transf.translation

            self.write_wing_settings(
                wing_xpath,
                wing_transf.scaling,
                wg_sk_transf.translation,
            )

            sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
                self.tixi, wing_xpath, "wing"
            )

            for i_sec in range(sec_cnt):
                sec_xpath = wing_xpath + "/sections/section[" + str(i_sec + 1) + "]"
                sec_transf = Transformation()
                sec_transf.get_cpacs_transf(self.tixi, sec_xpath)

                elem_xpath = sec_xpath + "/elements/element[1]"
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(self.tixi, elem_xpath)

                # Get wing profile (airfoil)
                prof_uid, prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
                    self.tixi, elem_xpath + "/airfoilUID"
                )

                airfoil_dir = Path(self.results_dir) / "airfoils"
                airfoil_dir.mkdir(exist_ok=True)
                foil_dat_path = str(airfoil_dir / f"{prof_uid}.dat")

                write_airfoil_coords(foil_dat_path, prof_uid, prof_vect_x, prof_vect_z)

                # Apply scaling
                x, y, z = prod_points(elem_transf.scaling, sec_transf.scaling)
                prof_vect_x *= x
                prof_vect_y *= y
                prof_vect_z *= z

                wg_sec_chord = corrects_airfoil_profile(prof_vect_x, prof_vect_y, prof_vect_z)

                # Add rotation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                x, y, z = sum_points(
                    elem_transf.rotation,
                    sec_transf.rotation,
                    wg_sk_transf.rotation,
                )
                add_rotation = Point(x=x, y=y, z=z)

                # Get Section rotation
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_dihed = math.radians(wg_sec_rot.x)
                wg_sec_twist = math.radians(wg_sec_rot.y)
                wg_sec_yaw = math.radians(wg_sec_rot.z)

                if all(abs(value) < 1e-6 for value in pos_y_list):
                    # Define the leading edge position from translations
                    x_le, y_le, z_le = sum_points(sec_transf.translation, elem_transf.translation)
                    x_le_rot, y_le_rot, z_le_rot = rotate_points(
                        x_le, y_le, z_le, wg_sec_dihed, wg_sec_twist, wg_sec_yaw
                    )
                else:
                    x_le_rot, y_le_rot, z_le_rot = rotate_points(
                        pos_x_list[i_sec],
                        pos_y_list[i_sec],
                        pos_z_list[i_sec],
                        wg_sec_dihed,
                        wg_sec_twist,
                        wg_sec_yaw,
                    )

                # Compute the absolute location of the leading edge
                x_le_abs = x_le_rot + wg_sk_transf.translation.x
                y_le_abs = y_le_rot + wg_sk_transf.translation.y
                z_le_abs = z_le_rot + wg_sk_transf.translation.z

                if (
                    self.add_fuselage
                    and self.clip_wing_inside_fuselage
                    and fus_x_coords is not None
                ):
                    # Compute the radius of the fuselage and the height difference ...
                    # between fuselage center and leading edge
                    x_query = x_le_abs + wg_sec_chord / 2
                    radius_fus = np.interp(x_query, fus_x_coords, fus_radius_profile)
                    fus_z_center = np.interp(x_query, fus_x_coords, fus_z_profile)
                    delta_z = np.abs(fus_z_center + body_transf.translation.z - z_le_abs)

                    # If the root wing section is inside the fuselage, translate it to...
                    # the fuselage border
                    # To make sure there is no wing part inside the fuselage
                    if (
                        np.sqrt((y_le_abs) ** 2 + (delta_z) ** 2) < radius_fus
                        and wg_sec_dihed < math.pi / 2
                        and root_defined is False
                    ):

                        y_le_abs += np.sqrt(radius_fus**2 - delta_z**2) - y_le_abs
                        y_le_rot = y_le_abs - wg_sk_transf.translation.y
                        root_defined = True

                leadingedge_coordinates(
                    self.tixi,
                    self.avl_path,
                    i_wing,
                    i_sec,
                    x_le_rot,
                    y_le_rot,
                    z_le_rot,
                    wg_sec_chord,
                    wg_sec_rot,
                    wing_xpath,
                    c_ref,
                    s_ref,
                    foil_dat_path,
                )

    def write_wing_settings(
        self,
        wing_xpath,
        scaling,
        translation,
    ) -> None:
        # Write wing settings
        with open(self.avl_path, "a") as avl_file:
            avl_file.write("#--------------------------------------------------\n")
            avl_file.write("SURFACE\nWing\n\n")
            avl_file.write("!Nchordwise  Cspace  Nspanwise  Sspace\n")
            avl_file.write(
                f"{self.nchordwise}  {self.vortex_dist}   {self.nspanwise} {self.vortex_dist}\n\n"
            )
            avl_file.write("COMPONENT\n1\n\n")

            # Symmetry
            if (
                self.tixi.checkAttribute(wing_xpath, "symmetry")
                and self.tixi.getTextAttribute(wing_xpath, "symmetry") == "x-z-plane"
            ):
                avl_file.write("YDUPLICATE\n0\n\n")

            # Angle, scaling and translation
            avl_file.write("ANGLE\n0\n\n")
            avl_file.write(f"SCALE\n{to_cpacs_format(scaling)}\n\n")
            avl_file.write(f"TRANSLATE\n{to_cpacs_format(translation)}\n\n")

    def write_ref_values(self) -> None:
        with open(self.avl_path, "a") as avl_file:
            # Reference dimensions
            avl_file.write("#Sref    Cref    Bref\n")
            avl_file.write(f"{self.area_ref:.3f}\t{self.chord_ref:.3f}\t{self.span_ref:.3f}\n\n")

            # Reference location for moments/rotations
            avl_file.write("#Xref    Yref    Zref\n")
            for i_points in range(3):
                avl_file.write(f"{self.points_ref[i_points]:.3f}\t")
            avl_file.write("\n\n")

    def write_fuselage_coords_from_tigl(
        self: "Avl",
        fus_dat_path: str,
        i_fus: int,
        x: ndarray,
        z_ctr: ndarray,
        half_w: ndarray,
        half_h: ndarray,
        body_translation: Point = None,
    ) -> None:
        """Write the fuselage side-view profile (BFILE) from TiGL data.

        TiGL returns global coordinates, but AVL applies its own TRANSLATE
        on top of the BFILE data, so we subtract the body translation to
        avoid double-counting.
        """
        # TiGL returns global coords; subtract body translation so AVL's
        # TRANSLATE doesn't apply it twice.
        if body_translation is not None:
            x = x - body_translation.x
            z_ctr = z_ctr - body_translation.z

        # AVL assumes a round body; use the equivalent radius
        equiv_r = 0.5 * (half_w + half_h)
        y_top = z_ctr + equiv_r
        y_bot = z_ctr - equiv_r

        with open(fus_dat_path, "w") as fus_file:
            fus_file.write("fuselage" + str(i_fus + 1) + "\n")

            # Top surface from tail to nose (skip the nose point)
            for xf, yf in reversed(list(zip(x[1:], y_top[1:]))):
                fus_file.write(f"{xf:.4f}\t{yf:.4f}\n")

            # Nose point
            y_nose = 0.5 * (y_top[0] + y_bot[0])
            fus_file.write(f"{x[0]:.4f}\t{y_nose:.4f}\n")

            # Bottom surface from nose to tail
            for xf, yf in zip(x[1:], y_bot[1:]):
                fus_file.write(f"{xf:.4f}\t{yf:.4f}\n")

        with open(self.avl_path, "a") as avl_file:
            avl_file.write("BFILE\n")
            avl_file.write(fus_dat_path + "\n\n")

    def write_fuselage_settings(
        self,
        fus_xpath: str,
        scaling: Point,
        translation: Point,
        nbody: int = 100,
    ) -> None:
        with open(self.avl_path, "a") as avl_file:
            avl_file.write("#--------------------------------------------------\n")
            avl_file.write("BODY\nFuselage\n\n")
            avl_file.write(f"!Nbody  Bspace\n{int(nbody)}\t1.0\n\n")

            # Symmetry
            if (
                self.tixi.checkAttribute(fus_xpath, "symmetry")
                and self.tixi.getTextAttribute(fus_xpath, "symmetry") == "x-z-plane"
            ):
                avl_file.write("YDUPLICATE\n0\n\n")

            avl_file.write(f"SCALE\n{to_cpacs_format(scaling)}\n\n")
            avl_file.write(f"TRANSLATE\n{to_cpacs_format(translation)}\n\n")
