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
        elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
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

    # Compute diameter of the section as the mean between height and width
    # AVL assumes only circular cross section for fuselage
    fus_radius = np.mean([body_frm_height, body_frm_width]) / 2
    fus_radius_vec[i_sec] = fus_radius

    # Save the coordinates of the fuselage
    x_fuselage[i_sec] = body_frm_center_x
    y_fuselage_top[i_sec] = body_frm_center_z + fus_radius
    y_fuselage_bottom[i_sec] = body_frm_center_z - fus_radius

    return body_frm_width, body_frm_height


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

            known_controls = {
                "InnerFlap": {"i_sec": [0, 1], "type": "flap", "bool": [1.0, 1.0]},
                "OuterFlap": {"i_sec": [1, 2], "type": "flap", "bool": [1.0, 1.0]},
                "Aileron": {"i_sec": [2, 3], "type": "aileron", "bool": [-1.0, -1.0]},
                "Elevator": {"i_sec": [0, 1], "type": "elevator", "bool": [1.0, 1.0]},
                "Rudder": {"i_sec": [0, 1], "type": "rudder", "bool": [-1.0, -1.0]},
            }

            for i in range(1, num_devices + 1):
                control_xpath = f"{control_xpath_base}/trailingEdgeDevice[{i}]"
                control_uid = tixi.getTextAttribute(control_xpath, "uID")

                control = known_controls.get(control_uid, None)
                if control is None:
                    continue

                # Read geometry only for known control surfaces
                innerhinge_xsi_xpath = control_xpath + "/path/innerHingePoint/hingeXsi"
                outerhinge_xsi_xpath = control_xpath + "/path/outerHingePoint/hingeXsi"
                if (
                    not tixi.checkElement(innerhinge_xsi_xpath)
                    or
                    not tixi.checkElement(outerhinge_xsi_xpath)
                ):
                    log.warning(f"Missing hinge xsi for {control_uid}, skipping.")
                    continue
                innerhinge_xsi = float(get_value(tixi, innerhinge_xsi_xpath))
                outerhinge_xsi = float(get_value(tixi, outerhinge_xsi_xpath))

                inner_eta_xpath = control_xpath + "/outerShape/innerBorder/etaTE/eta"
                outer_eta_xpath = control_xpath + "/outerShape/outerBorder/etaTE/eta"
                if (
                    not tixi.checkElement(inner_eta_xpath)
                    or
                    not tixi.checkElement(outer_eta_xpath)
                ):
                    log.warning(f"Missing eta for {control_uid}, skipping.")
                    continue
                inner_eta = float(get_value(tixi, inner_eta_xpath))
                outer_eta = float(get_value(tixi, outer_eta_xpath))

                x_axis = (outerhinge_xsi - innerhinge_xsi) * c_ref
                y_axis = (outer_eta - inner_eta) * s_ref
                z_axis = 0.0
                is_rudder = control["type"] == "rudder"
                control["axis"] = (
                    f"{x_axis} {z_axis} {y_axis}"
                    if is_rudder
                    else f"{x_axis} {y_axis} {z_axis}"
                )
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
        # AVL's internal MAKEBODY buffer is finite (NLMAX). If many fuselages are
        # present, a fixed high Nbody value can overflow that buffer.
        max_total_nbody = 480
        nbody_per_fuselage = max(20, min(100, max_total_nbody // max(1, fus_cnt)))

        fus_x_coords = np.array([0.0])
        fus_z_profile = np.array([0.0])
        fus_radius_profile = np.array([0.0])
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

            # 1. Write fuselage settings
            fus_has_symmetry = (
                self.tixi.checkAttribute(fus_xpath, "symmetry")
                and self.tixi.getTextAttribute(fus_xpath, "symmetry") == "x-z-plane"
            )
            # Scaling is already applied inside compute_fuselage_coords,
            # so pass unit scaling to avoid double-scaling by AVL's SCALE directive.
            self.write_fuselage_settings(
                Point(x=1.0, y=1.0, z=1.0),
                body_transf.translation,
                nbody=nbody_per_fuselage,
                symmetry=fus_has_symmetry,
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

            self.write_fuselage_coords(
                fus_dat_path,
                i_fus,
                x_fuselage,
                y_fuselage_bottom,
                y_fuselage_top,
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

                # Get Section rotation (combined: for twist/incidence output)
                wg_sec_rot = euler2fix(add_rotation)

                # LE position in wing-local frame: positioning + section/element translations
                x_le_local = (
                    pos_x_list[i_sec]
                    + sec_transf.translation.x
                    + sec_transf.scaling.x
                    * elem_transf.translation.x
                )
                y_le_local = (
                    pos_y_list[i_sec]
                    + sec_transf.translation.y
                    + sec_transf.scaling.y
                    * elem_transf.translation.y
                )
                z_le_local = (
                    pos_z_list[i_sec]
                    + sec_transf.translation.z
                    + sec_transf.scaling.z
                    * elem_transf.translation.z
                )

                # Rotate by wing-only rotation to world frame.
                # Section/element rotations affect chord orientation, not section position.
                wg_dihed = math.radians(wg_sk_transf.rotation.x)
                wg_twist = math.radians(wg_sk_transf.rotation.y)
                wg_yaw = math.radians(wg_sk_transf.rotation.z)

                x_le_rot, y_le_rot, z_le_rot = rotate_points(
                    x_le_local,
                    y_le_local,
                    z_le_local,
                    wg_dihed,
                    wg_twist,
                    wg_yaw,
                )

                # Compute the absolute location of the leading edge
                x_le_abs = x_le_rot + wg_sk_transf.translation.x
                y_le_abs = y_le_rot + wg_sk_transf.translation.y
                z_le_abs = z_le_rot + wg_sk_transf.translation.z

                # Check if wing section LE is inside the fuselage
                if (
                    self.add_fuselage
                    and fus_x_coords is not None
                ):
                    x_query = x_le_abs + wg_sec_chord / 2
                    radius_fus = np.interp(x_query, fus_x_coords, fus_radius_profile)
                    fus_z_center = np.interp(x_query, fus_x_coords, fus_z_profile)
                    delta_z = np.abs(fus_z_center + body_transf.translation.z - z_le_abs)
                    dist_from_axis = np.sqrt(y_le_abs**2 + delta_z**2)

                    if dist_from_axis < radius_fus:
                        log.warning(
                            f"Wing {i_wing} section {i_sec} LE is inside the fuselage "
                            f"(dist={dist_from_axis:.3f} < radius={radius_fus:.3f}). "
                            f"Dihedral may be incorrect."
                        )

                    if (
                        self.clip_wing_inside_fuselage
                        and dist_from_axis < radius_fus
                        and wg_dihed < math.pi / 2
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

    def write_fuselage_coords(
        self: "Avl",
        fus_dat_path: Path,
        i_fus: int,
        x_fuselage,
        y_fuselage_bottom,
        y_fuselage_top,
    ) -> None:
        with open(fus_dat_path, "w") as fus_file:
            fus_file.write("fuselage" + str(i_fus + 1) + "\n")

            # Write coordinates of the top surface (tail to nose)
            for x_fus, y_fus in reversed(list(zip(x_fuselage, y_fuselage_top))):
                fus_file.write(f"{x_fus:.3f}\t{y_fus:.3f}\n")

            # Write coordinates of the bottom surface (nose to tail)
            for x_fus, y_fus in zip(x_fuselage, y_fuselage_bottom):
                fus_file.write(f"{x_fus:.3f}\t{y_fus:.3f}\n")

        with open(self.avl_path, "a") as avl_file:
            avl_file.write("BFILE\n")
            avl_file.write(fus_dat_path + "\n\n")

    def write_fuselage_settings(
        self,
        scaling: Point,
        translation: Point,
        nbody: int = 100,
        symmetry: bool = False,
    ) -> None:
        with open(self.avl_path, "a") as avl_file:
            avl_file.write("#--------------------------------------------------\n")
            avl_file.write("BODY\nFuselage\n\n")
            avl_file.write(f"!Nbody  Bspace\n{int(nbody)}\t1.0\n\n")
            if symmetry:
                avl_file.write("YDUPLICATE\n0\n\n")
            avl_file.write(f"SCALE\n{to_cpacs_format(scaling)}\n\n")
            avl_file.write(f"TRANSLATE\n{to_cpacs_format(translation)}\n\n")
