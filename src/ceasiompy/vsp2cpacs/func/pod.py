"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOMpy.
The geometry is built in OpenVSP, saved as a .vsp3 file, and then selected in the GUI.
It is subsequently processed by this module to generate a CPACS file.

| Author: Nicolo' Perasso
| Creation: 23/12/2025
"""

# Imports
import numpy as np
import openvsp as vsp  # type: ignore

from ceasiompy.vsp2cpacs.func.wing import Extract_transformation


# Functions
def Import_POD(POD):
    # Some inizializations
    Sections_information = {}

    # ---- Transformation information ----
    # Inside Extract_transformation
    # there are the global informations that characterize the component

    Sections_information["Transformation"] = Extract_transformation(POD)
    Sections_information["Transformation"]["Length"] = vsp.GetParmVal(
        POD, "Length", "Design"
    )
    Sections_information["Transformation"]["FineRatio"] = vsp.GetParmVal(
        POD, "FineRatio", "Design"
    )

    # Tessellation parameters
    Tess_W = vsp.GetParmVal(POD, "Tess_W", "Shape")

    # ---- section informations ----
    # Save the parameters required to define sections.

    # Create a nested dictionary so each section maps expected keys to values.
    Output_inf = [
        "x_scal",
        "y_scal",
        "z_scal",
        "x_rot",
        "y_rot",
        "z_rot",
        "x_loc",
        "y_trasl",
        "z_trasl",
        "spin",
    ]

    # shape of the pod.
    X_pos, r_distr = POD_shape_func(
        Sections_information["Transformation"]["Length"],
        Sections_information["Transformation"]["FineRatio"],
    )

    # For the engine
    Sections_information["Transformation"]["curveProfile"] = [(X_pos), -(r_distr) / 2]

    for i, x_elem in enumerate(X_pos):
        # ---- section ----
        Section_VSP = POD_Section(x_elem, r_distr[i])
        Sections_information[f"Section{i}"] = dict(zip(Output_inf, Section_VSP))

        # ---- default profile of the POD. It is a circle ----
        Name = "Circle" if r_distr[i] != 0 else "Point"
        coord = POD_profile(Tess_W)
        Scaling = [r_distr[i]]
        Sections_information[f"Section{i}"]["Airfoil"] = Name
        Sections_information[f"Section{i}"]["Airfoil_coordinates"] = coord
        if Name == "Point":
            Sections_information[f"Section{i}"]["x_scal"] = 0
            Sections_information[f"Section{i}"]["y_scal"] = 0
            Sections_information[f"Section{i}"]["z_scal"] = 0
        else:
            Sections_information[f"Section{i}"]["x_scal"] = 0
            Sections_information[f"Section{i}"]["y_scal"] = Scaling[0]
            Sections_information[f"Section{i}"]["z_scal"] = Scaling[0]
    return Sections_information


def POD_shape_func(L, F_ratio):
    # The POD is modeled as a fuselage with a circular profile,
    # since the exact surface shape is unknown.
    # The shape is composed of three parts:
    # - a quarter-ellipse from 0 to 20% of the length,
    # - a constant-radius region up to 50% of the length,
    # - a rear section tapering toward the tail.
    # This is a simplified superellipse whose coefficients
    # are chosen to closely match the OpenVSP geometry.

    r_max = L / F_ratio
    s1 = 0.3
    s2 = 0.6
    x = np.concatenate(
        (
            np.linspace(0, L * s1, 5, endpoint=False),
            np.linspace(L * s1, L * s2, 2, endpoint=False)[1:],
            np.linspace(L * s2, L, 5),
        )
    )
    s = x / L
    R = np.zeros_like(s)
    for i, si in enumerate(s):
        if si <= s1:
            a = s1
            b = r_max
            R[i] = b * np.sqrt(1 - (1 - si / a) ** 1.5)
        elif si <= s2:
            R[i] = r_max
        else:
            a = 1 - s2
            t = (si - s2) / a
            R[i] = r_max * np.sqrt(1 - t ** 1)
    return x, np.trunc(R * 100) / 100


def POD_Section(x_pos, r_section):
    # translations - rotations - spin - scaling
    x_loc = x_pos
    y_trasl = 0
    z_trasl = 0
    x_rot = 0
    y_rot = 0
    z_rot = 0
    spin = 0
    if r_section == 0:
        x_scal, y_scal, z_scal = 1, 0, 0
    else:
        x_scal, y_scal, z_scal = 1, r_section + 1, r_section + 1

    return [
        x_scal, y_scal, z_scal,
        x_rot, y_rot, z_rot,
        x_loc, y_trasl, z_trasl, spin,
    ]


def POD_profile(n):
    # Circle profile.
    # d: diameter
    # n: number of points
    # The first and last points correspond to the nose and tail of the pod.
    # Since CPACS does not accept a single point as a profile, a default radius
    # is assigned and later scaled to zero.

    d = 2
    theta = np.linspace(0, np.pi, int(n / 2))
    x = d / 2 * np.cos(theta)
    y = d / 2 * np.sin(theta)

    x_full = np.concatenate((x, -x), axis=0)
    y_full = np.concatenate((-y, y), axis=0)

    # close profile
    y_full[0] = y_full[-1]
    x_full[0] = x_full[-1]

    return x_full, y_full
