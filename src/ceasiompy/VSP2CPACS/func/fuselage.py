"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOmpy. Built the geometry in openVSP, save as .svp3 and
after select it inside the GUI. After it will pass through this module to have a CPACS
file.

| Author: Nicolo' Perasso
| Creation: ?????
"""

# Imports
import copy

import numpy as np
import openvsp as vsp

from ceasiompy.VSP2CPACS.func.wing import Extract_transformation, get_profile_section


# Functions
def Import_Fuse(Fuselage):
    """Build a CPACS-ready dictionary describing the fuselage sections."""

    Sections_information = {}
    n_section_idx = 0

    Sections_information["Transformation"] = Extract_transformation(Fuselage)
    Sections_information["Transformation"]["Length"] = vsp.GetParmVal(
        Fuselage, "Length", "Design"
    )
    Sections_information["Transformation"]["idx_engine"] = None

    Output_inf = ["x_rot", "y_rot", "z_rot", "x_loc", "y_trasl", "z_trasl", "spin"]
    xsec_surf_id = vsp.GetXSecSurf(Fuselage, 0)
    num_xsecs = vsp.GetNumXSec(xsec_surf_id)

    for i in range(num_xsecs):
        xsec_id = vsp.GetXSec(xsec_surf_id, i)

        Section_VSP = Fuse_Section(
            Fuselage, i, Sections_information["Transformation"]["Length"]
        )
        Sections_information[f"Section{n_section_idx}"] = dict(
            zip(Output_inf, Section_VSP)
        )
        coord, Name, Scaling, shift = get_profile_section(
            Fuselage,
            xsec_id,
            i,
            Twist_val=0,
            Twist_loc=0,
            Rel=0,
            Twist_list=0,
        )

        if shift is not None:
            Sections_information[f"Section{n_section_idx}"]["z_trasl"] += 0.5 - np.abs(
                shift
            )

        coord -= np.mean(coord, axis=1, keepdims=True)
        coord = reorder_fuselage_profile(coord[0, :], coord[1, :])

        Sections_information[f"Section{n_section_idx}"]["Airfoil"] = Name
        Sections_information[f"Section{n_section_idx}"]["Airfoil_coordinates"] = coord

        if len(Scaling) == 2:
            Sections_information[f"Section{n_section_idx}"]["x_scal"] = 1
            Sections_information[f"Section{n_section_idx}"]["y_scal"] = Scaling[0]
            Sections_information[f"Section{n_section_idx}"]["z_scal"] = Scaling[1]
            Sections_information["Transformation"]["reference_length"] = Scaling[0]
        else:
            Sections_information[f"Section{n_section_idx}"]["x_scal"] = 1
            Sections_information[f"Section{n_section_idx}"]["y_scal"] = Scaling[0]
            Sections_information[f"Section{n_section_idx}"]["z_scal"] = Scaling[0]

        if Name == "Point":
            Sections_information[f"Section{n_section_idx}"]["x_scal"] = 0
            Sections_information[f"Section{n_section_idx}"]["y_scal"] = 0
            Sections_information[f"Section{n_section_idx}"]["z_scal"] = 0

        if Sections_information[f"Section{n_section_idx}"]["spin"] != 0:
            mid_length = (
                Sections_information[f"Section{n_section_idx}"]["x_loc"]
                - Sections_information[f"Section{n_section_idx - 1}"]["x_loc"]
            ) / 2

            Sections_information[
                f"Section{n_section_idx + 1}"
            ] = copy.deepcopy(Sections_information[f"Section{n_section_idx}"])

            Sections_information[f"Section{n_section_idx}"] = Spin_func(
                Sections_information[f"Section{n_section_idx + 1}"]["spin"],
                Sections_information[f"Section{n_section_idx + 1}"],
                Sections_information[f"Section{n_section_idx + 1}"]["x_loc"] - mid_length,
                Sections_information[f"Section{n_section_idx + 1}"]["x_rot"],
            )

            Sections_information[f"Section{n_section_idx + 2}"] = Spin_func(
                Sections_information[f"Section{n_section_idx + 1}"]["spin"],
                Sections_information[f"Section{n_section_idx + 1}"],
                Sections_information[f"Section{n_section_idx + 1}"]["x_loc"] + mid_length,
                Sections_information[f"Section{n_section_idx + 1}"]["x_rot"],
            )

            n_section_idx += 3
        else:
            n_section_idx += 1

    return Sections_information


def reorder_fuselage_profile(x, y):
    """
    Reorder CPACS fuselage profile points so they start at the lowest negative-y point.
    """

    x = np.array(x)
    y = np.array(y)
    if x.shape != y.shape:
        raise ValueError("x e y devono avere la stessa dimensione")

    neg_idx = np.where(y < 0)[0]
    if len(neg_idx) == 0:
        raise ValueError("Nessun punto con y negativa trovato")

    central_idx = neg_idx[np.argmin(np.abs(x[neg_idx]))]
    candidate_idxs = neg_idx[np.abs(x[neg_idx] - x[central_idx]) < 1e-12]
    start_idx = candidate_idxs[np.argmin(y[candidate_idxs])]

    lower_points_idx = np.arange(start_idx, len(x))
    upper_points_idx = np.arange(0, start_idx + 1)
    final_idx = np.concatenate([lower_points_idx, upper_points_idx])
    coord = np.vstack((x[final_idx], y[final_idx]))

    mask = np.ones(coord.shape[1], dtype=bool)
    for i in range(1, coord.shape[1]):
        if np.allclose(coord[:, i], coord[:, i - 1]):
            mask[i] = False
    coord = coord[:, mask]

    if not np.allclose(coord[:, 0], coord[:, -1]):
        coord = np.hstack([coord, coord[:, 0:1]])

    return coord


def Fuse_Section(Fuselage, idx, length):
    """Collect translation/rotation parameters for a fuselage section."""

    x_loc = vsp.GetParmVal(Fuselage, "XLocPercent", f"XSec_{idx}") * length
    y_trasl = vsp.GetParmVal(Fuselage, "YLocPercent", f"XSec_{idx}") * length
    z_trasl = vsp.GetParmVal(Fuselage, "ZLocPercent", f"XSec_{idx}") * length
    x_rot = vsp.GetParmVal(Fuselage, "XRotate", f"XSec_{idx}")
    y_rot = vsp.GetParmVal(Fuselage, "YRotate", f"XSec_{idx}")
    z_rot = vsp.GetParmVal(Fuselage, "ZRotate", f"XSec_{idx}")
    spin = vsp.GetParmVal(Fuselage, "Spin", f"XSec_{idx}")

    return [x_rot, y_rot, z_rot, x_loc, y_trasl, z_trasl, spin]


def Spin_func(spin, Section_informations, x_loc, x_rot):
    """
    Duplicate a section and rotate it to represent pre/post-spin geometry.
    """

    Add_section = copy.deepcopy(Section_informations)
    a = abs(float(spin) - float(x_rot) * 0.25 / 90)

    Add_section["x_rot"] = float(x_rot) - ((float(spin) * 90) / 0.25)
    Add_section["y_scal"] = 2 * abs(a - 0.5)
    Add_section["z_scal"] = 2 * abs(a - 0.5)
    Add_section["x_scal"] = 1
    Add_section["x_loc"] = x_loc

    return Add_section
