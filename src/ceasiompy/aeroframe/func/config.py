"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to extract panel forces of a surface,
from AVL 'fe.txt' element force file

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# Imports

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.spatial.distance import cdist
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.getprofile import get_profile_coord
from ceasiompy.utils.geometryfunctions import (
    sum_points,
    prod_points,
    get_positionings,
)
from ceasiompy.utils.mathsfunctions import (
    euler2fix,
    rotate_points,
)
from ceasiompy.aeroframe.func.utils import (
    poly_area,
    second_moments_of_area,
    interpolate_leading_edge_points,
)

from framat import Model
from pathlib import Path
from scipy import interpolate
from numpy import ndarray
from cpacspy.cpacspy import CPACS
from typing import List, Tuple
from pandas import Series, DataFrame
from functools import partial
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.generalclasses import (
    Point,
    Transformation,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import WINGS_XPATH
from ceasiompy.aeroframe import (
    FRAMAT_IX_XPATH,
    FRAMAT_IY_XPATH,
    FRAMAT_AREA_XPATH,
    FRAMAT_DENSITY_XPATH,
    FRAMAT_SHEARMODULUS_XPATH,
    FRAMAT_YOUNGMODULUS_XPATH,
)


# Functions

def compute_distance_and_moment(centerline_df: DataFrame, row: Series) -> Series:
    """Transfer of forces and induced moment to the closest beam node."""
    point_xyz = np.array([row["x"], row["y"], row["z"]])
    centerline_xyz = np.array(
        [
            centerline_df.at[row["closest_centerline_index"], "x"],
            centerline_df.at[row["closest_centerline_index"], "y"],
            centerline_df.at[row["closest_centerline_index"], "z"],
        ]
    )

    distance_vector = point_xyz - centerline_xyz
    force_vector = np.array([row["Fx"], row["Fy"], row["Fz"]])
    moment_vector = np.cross(distance_vector, force_vector)

    return Series(
        {
            "moment_x": moment_vector[0],
            "moment_y": moment_vector[1],
            "moment_z": moment_vector[2],
            "distance_vector": distance_vector,
        }
    )


def parse_AVL_surface(extracted_string: str):
    """Function to extract panel forces of a surface,
    from AVL 'fe.txt' element force file.

    Args:
        string (str): string extracted from 'fe.txt' with
        the surface data.

    Returns:
        surface_name (str): name of the lifting surface.
        nspanwise (int): number of spanwise vortices.
        nchord_strip (int): number of chordwise vortices.
        xyz (numpy array): coordinates of each panel [m].
        p_xyz (numpy array): pressure at each panel,
                              projected on the axis [Pa].
        slope_list (list): slope of the local camberline.
    """

    i_newline = [i for i, char in enumerate(extracted_string) if char == "\n"]
    surface_name = extracted_string[12 : i_newline[0] - 1].replace(" ", "")

    str_tmp = extracted_string[i_newline[0] + 1 : i_newline[1]]
    i_span = str_tmp.find("# Spanwise =")
    nspanwise = int(str_tmp[i_span + 12 : i_span + 17])

    i_chordwise = [
        m.start() for m in re.finditer("# Chordwise =", extracted_string[i_newline[1] :])
    ]
    i_incidence = [
        m.start() for m in re.finditer("Incidence  =", extracted_string[i_newline[1] :])
    ]
    i_strip_width = [
        m.start() for m in re.finditer("Strip Width  =", extracted_string[i_newline[1] :])
    ]
    i_strip_dihed = [
        m.start() for m in re.finditer("Strip Dihed. =", extracted_string[i_newline[1] :])
    ]
    i_IbX = [m.start() for m in re.finditer("I        X", extracted_string[i_newline[1] :])]

    nchord_strip: List[float] = [0.0] * nspanwise
    incidence_strip: List[float] = [0.0] * nspanwise
    width_strip: List[float] = [0.0] * nspanwise
    dihed_strip: List[float] = [0.0] * nspanwise
    slope_list: List[float] = []
    jj = -1

    nchordwise = int(
        extracted_string[
            slice(i_newline[1] + i_chordwise[0] + 13, i_newline[1] + i_chordwise[0] + 16)
        ]
    )
    p_xyz = np.zeros((nspanwise * nchordwise, 3))
    xyz = np.zeros((nspanwise * nchordwise, 3))

    nn_vec = []
    for k in range(nspanwise):
        i0 = slice(i_newline[1] + i_chordwise[k] + 13, i_newline[1] + i_chordwise[k] + 16)
        nchord_strip[k] = float(extracted_string[i0])

        i0 = slice(
            i_newline[1] + i_incidence[k] - 1 + 13,
            i_newline[1] + i_incidence[k] - 1 + 24,
        )
        incidence_strip[k] = float(extracted_string[i0])

        i0 = slice(
            i_newline[1] + i_strip_width[k] - 1 + 13 + 2,
            i_newline[1] + i_strip_width[k] - 1 + 24 + 1,
        )
        width_strip[k] = float(extracted_string[i0])

        i0 = slice(
            i_newline[1] + i_strip_dihed[k] - 1 + 13 + 2,
            i_newline[1] + i_strip_dihed[k] - 1 + 24 + 1,
        )
        dihed_strip[k] = float(extracted_string[i0])

        idd = [
            i
            for i in range(len(i_newline) - 1)
            if (i_IbX[k] + i_newline[1] - 1 - i_newline[i])
            * (i_IbX[k] + i_newline[1] - 1 - i_newline[i + 1])
            < 0
        ]

        sa = np.sin(np.deg2rad(incidence_strip[k]))
        ca = np.cos(np.deg2rad(incidence_strip[k]))
        sd = np.sin(np.deg2rad(dihed_strip[k]))
        cd = np.cos(np.deg2rad(dihed_strip[k]))

        nn = np.array([sa * cd, -ca * sd, ca * cd])
        nn = nn / np.linalg.norm(nn)

        ah = np.array([0, cd, sd])
        T = np.array([[0, -ah[2], ah[1]], [ah[2], 0, -ah[0]], [-ah[1], ah[0], 0]])

        sdx = 0
        x0 = np.zeros(int(nchord_strip[k]))
        z0 = np.zeros(int(nchord_strip[k]))

        for j in range(int(nchord_strip[k])):
            jj += 1
            line_data = extracted_string[i_newline[idd[0] + j + 1] : i_newline[idd[0] + j + 2]]
            data_list = [
                float(match.group()) for match in re.finditer(r"-?\b\d+\.\d+\b", line_data[9:])
            ]
            xyz0 = data_list[0:3]
            dx = data_list[3]
            x0[j] = sdx
            sdx += dx
            slope = data_list[4]

            if j > 0:
                z0[j] = z0[j - 1] + slope * dx

            dCp = data_list[5]

            phi = -np.arctan(slope)
            strip_area = dx * width_strip[k] / np.cos(phi)
            nn1 = (
                np.cos(phi) * nn
                + (1 - np.cos(phi)) * ah * (ah.dot(np.transpose(nn)))
                + np.sin(phi) * nn.dot(np.transpose(T))
            )
            p_xyz0 = strip_area * dCp * nn1
            # cp_xyz0 = dCp * nn1
            p_xyz[jj, :] = p_xyz0
            xyz[jj, :] = xyz0
            slope_list.append(slope)

        nn_vec.append(nn1)

    return surface_name, nspanwise, nchord_strip, xyz, p_xyz, slope_list


def read_avl_fe_file(
    fe_path: Path, plot: bool = False
) -> Tuple[List, List, List, List, List, List]:
    """Function to read AVL 'fe.txt' element force file,
    and extract the aerodynamic loads calling the function
    'parse_AVL_surface'.

    Args:
        FE_PATH (path): Path to the AVL 'fe.txt' file.
        plot (bool): To display the extracted forces in a 3D vector-plot.

    Returns: surface_name_list, nspanwise_list, nchordwise_list, xyz_list, fxyz_list, slope_list
        surface_name_list (list): list of name of the lifting surfaces.
        nspanwise_list (list): list of number of spanwise vortices of the surfaces.
        nchordwise_list (list): list of number of chordwise vortices of the surfaces.
        xyz_list (list): list of coordinates of each panel [m] of the surfaces.
        p_xyz_list (list): list of pressure at each panel of the surfaces [Pa].
        slope_list (list): slope of the local camberline of the surfaces.
    """

    try:
        with open(fe_path, "r") as file:
            file_content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error reading {fe_path}")

    i_surface = [m.start() for m in re.finditer("Surface #", file_content)]
    number_surfaces = len(i_surface)
    string_surface = []

    for k in range(number_surfaces):
        if k + 1 == number_surfaces:
            ie = len(file_content)
        else:
            ie = i_surface[k + 1]

        string_surface.append(file_content[i_surface[k] : ie])

    fsclf = 10
    xyz_list = []
    p_xyz_list = []
    surface_name_list = []
    nspanwise_list = []
    nchordwise_list = []
    slope_list = []

    for k in range(number_surfaces):
        string_tmp = string_surface[k]
        surface_name, nspanwise, nchord_strip, xyz, cp_xyz, slope = parse_AVL_surface(string_tmp)
        surface_name_list.append(surface_name)
        nspanwise_list.append(nspanwise)
        nchordwise_list.append(nchord_strip)
        xyz_list.append(xyz)
        p_xyz_list.append(cp_xyz)
        slope_list.append(slope)

        if plot:
            plt.figure(figsize=(10, 8))
            fig = plt.figure(k + 1)
            ax = fig.add_subplot(111, projection="3d")
            ax.set_xlabel("Chord")
            ax.set_ylabel("Span")
            ax.set_title("Figure " + str(k + 1))
            xyzpf = xyz + fsclf * cp_xyz
            xpl = []
            ypl = []
            zpl = []
            for kk in range(xyzpf.shape[0]):
                xpl.extend([xyz[kk, 0], xyzpf[kk, 0], float("nan")])
                ypl.extend([xyz[kk, 1], xyzpf[kk, 1], float("nan")])
                zpl.extend([xyz[kk, 2], xyzpf[kk, 2], float("nan")])

            ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], marker="o", linestyle="", color="black")
            ax.plot(xpl, ypl, zpl, color="red")
            ax.axis("equal")

    plt.show()

    return (
        surface_name_list,
        nspanwise_list,
        nchordwise_list,
        xyz_list,
        p_xyz_list,
        slope_list,
    )


def create_framat_model(
    young_modulus: float,
    shear_modulus: float,
    material_density: float,
    centerline_df: DataFrame,
    internal_load_df: DataFrame,
) -> Model:
    """
    Function to create the FramAT beam model.

    Function 'create_framat_model' creates the FramAT beam model used
    for structural computations.

    Args:
        young_modulus: Young modulus of the wing material [GPa].
        shear_modulus: Shear modulus of the wing material [GPa].
        material_density: Density of the wing material [kg/m^3].
        centerline_df:
            dataframe with the beam nodes,
            the applied forces/moments,
            the sections properties.
        internal_load_df: previous version of centerline_df (iteration n-1).

    Returns:
        model: FramAT beam model, ready for FEM computations.
    """

    model = Model()

    # Material
    mat = model.add_feature("material", uid="material")
    mat.set("E", young_modulus * 1e9)
    mat.set("G", shear_modulus * 1e9)
    mat.set("rho", material_density)

    # Initialize boundary condition
    bc = model.set_feature("bc")

    # Add a single beam
    beam = model.add_feature("beam")

    # Loop through each node and add them to the beam
    for i_node in range(len(centerline_df)):
        beam.add(
            "node",
            [
                centerline_df.iloc[i_node]["x"],
                centerline_df.iloc[i_node]["y"],
                centerline_df.iloc[i_node]["z"],
            ],
            uid=centerline_df.iloc[i_node]["node_uid"],
        )

    # Set the number of elements for the beam
    beam.set("nelem", len(centerline_df) - 1)

    # Add orientation property to the beam
    for i_node in range(len(centerline_df) - 1):
        up_x, up_y, up_z = rotate_points(
            x=0,
            y=0,
            z=1,
            RaX=centerline_df.iloc[i_node]["thx_new"],
            RaY=-centerline_df.iloc[i_node]["thy_new"],
            RaZ=centerline_df.iloc[i_node]["thz_new"],
        )

        beam.add(
            "orientation",
            {
                "from": centerline_df.iloc[i_node]["node_uid"],
                "to": centerline_df.iloc[i_node + 1]["node_uid"],
                "up": [up_x, up_y, up_z],
            },
        )

    # Define material
    beam.add(
        "material",
        {
            "from": centerline_df.iloc[0]["node_uid"],
            "to": centerline_df.iloc[-1]["node_uid"],
            "uid": "material",
        },
    )

    # Add cross-section properties
    for i_node in range(len(centerline_df) - 1):
        cs = model.add_feature(
            "cross_section", uid=centerline_df.iloc[i_node]["cross_section_uid"]
        )
        cs.set("A", centerline_df.iloc[i_node]["cross_section_area"])
        cs.set("Iy", centerline_df.iloc[i_node]["cross_section_Ix"])
        cs.set("Iz", centerline_df.iloc[i_node]["cross_section_Iy"])
        cs.set("J", centerline_df.iloc[i_node]["cross_section_J"])
        beam.add(
            "cross_section",
            {
                "from": centerline_df.iloc[i_node]["node_uid"],
                "to": centerline_df.iloc[i_node + 1]["node_uid"],
                "uid": centerline_df.iloc[i_node]["cross_section_uid"],
            },
        )

    # Add increment of point loads [N] on each beam node
    for i_node in range(len(centerline_df)):
        node_uid = centerline_df.iloc[i_node]["node_uid"]
        load = [
            centerline_df.iloc[i_node][force] - internal_load_df.iloc[i_node][force]
            for force in ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
        ]
        beam.add("point_load", {"at": node_uid, "load": load})

    # ===== BOUNDARY CONDITIONS =====
    idx_to_fix = centerline_df["y"].idxmin()
    bc.add("fix", {"node": "wing1_node" + str(idx_to_fix + 1), "fix": ["all"]})

    # ===== POST-PROCESSING =====
    pp = model.set_feature("post_proc")
    pp.set(
        "plot_settings",
        {"show": False, "scale_forces": 5, "scale_moments": 1, "scale_deformation": 10},
    )
    pp.add("plot", ["undeformed", "deformed", "bc", "global_axes"])

    return model


def get_material_properties(tixi: Tixi3):
    """Function to read the material properties for structural
    calculations.

    Function 'get_material_properties' reads the material properties
    of the wing given in the graphical user interface of CEASIOMpy, in
    order to make structural computations.

    Returns:
        young_modulus (float): Young modulus of the material [GPa].
        shear_modulus (float): Shear modulus of the material [GPa].
        material_density (float): Density of the material [kg/m^3].

    """
    young_modulus = get_value(tixi, FRAMAT_YOUNGMODULUS_XPATH)
    shear_modulus = get_value(tixi, FRAMAT_SHEARMODULUS_XPATH)
    material_density = get_value(tixi, FRAMAT_DENSITY_XPATH)

    return young_modulus, shear_modulus, material_density


def get_section_properties(tixi: Tixi3):
    """Function reads the cross-section properties for structural
    calculations.

    Function 'get_section_properties' reads the cross-section properties
    of the wing from the graphical user interface of CEASIOMpy, in
    order to make structural computations.

    Returns:
        area (float): area of the cross-section [m^2].
        Ix (float): second moment of area about the x-axis [m^4].
        Iy (float): second moment of area about the x-axis [m^4].

    """
    area = get_value(tixi, FRAMAT_AREA_XPATH)
    Ix = get_value(tixi, FRAMAT_IX_XPATH)
    Iy = get_value(tixi, FRAMAT_IY_XPATH)

    return area, Ix, Iy


def create_wing_centerline(
    wing_df,
    centerline_df,
    N_beam,
    wg_origin,
    xyz_tot,
    fxyz_tot,
    n_iter,
    xyz_tip,
    tip_def,
    aera_profile,
    Ix_profile,
    Iy_profile,
    chord_profile,
    twist_profile,
    CASE_PATH,
    AVL_UNDEFORMED_PATH,
    wg_scaling,
):
    """Function to create the beam nodes along the wing centerline.

    Function 'create_wing_centerline' creates the beam nodes along
    the wing centerline, associating all the geometric properties
    and the applied forces and moments.

    Args:
        wing_df (pandas dataframe): dataframe containing all VLM points coordinates
                                    and aero forces.
        centerline_df (pandas dataframe): dataframe containing beam nodes, associated projected
                                          forces and moments, associated section properties.
        N_beam (int): number of beam nodes to use for the structural mesh.
        wg_origin (list): coordinates of the origin of the wing geometry [m].
        xyz_tot (list): coordinates of the VLM nodes, including root and tip [m].
        fxyz_tot (list): components of the VLM aero forces [N].
        n_iter (int): number of the current iteration.
        xyz_tip (list): coordinates of the mid-chord tip center of the undeformed wing [m].
        tip_def (list): coordinates of the mid-chord tip center of the deformed wing [m].
        aera_profile (scipy.interpolate): profile of area of the cross-sections along
                                          the span [m^2].
        Ix_profile (scipy.interpolate.interp1d): profile of the second moment of area about
                                                 the x-axis along the span [m^4].
        Iy_profile (scipy.interpolate.interp1d): profile of the second moment of area about
                                                 the y-axis along the span [m^4].
        chord_profile (scipy.interpolate.interp1d): profile of the chord length along
                                                    the span [m].
        twist_profile (scipy.interpolate.interp1d): profile of the twist angle along
                                                    the span [deg].
        CASE_PATH (Path): path to the flight case directory.
        AVL_UNDEFORMED_PATH (Path): path to the undeformed AVL geometry.

    Returns:
        wing_df (pandas dataframe): updated dataframe.
        centerline_df (pandas dataframe): updated dataframe.
        internal_load_df (pandas dataframe): dataframe containing the internal forces of the beam
                                             (i.e. the previous aero forces).

    """

    wing_df = DataFrame(
        {
            "x": [row[0] for row in xyz_tot],
            "y": [row[1] for row in xyz_tot],
            "z": [row[2] for row in xyz_tot],
            "Fx": [row[0] for row in fxyz_tot],
            "Fy": [row[1] for row in fxyz_tot],
            "Fz": [row[2] for row in fxyz_tot],
        }
    )

    if n_iter == 1:
        tip_row = DataFrame(
            [
                {
                    "x": xyz_tip[0],
                    "y": xyz_tip[1],
                    "z": xyz_tip[2],
                    "Fx": 0,
                    "Fy": 0,
                    "Fz": 0,
                }
            ]
        )
    else:
        tip_row = DataFrame(
            [
                {
                    "x": tip_def[0],
                    "y": tip_def[1],
                    "z": tip_def[2],
                    "Fx": 0,
                    "Fy": 0,
                    "Fz": 0,
                }
            ]
        )

    wing_df = pd.concat([wing_df, tip_row], ignore_index=True)

    _, _, _, Xle, Yle, Zle = interpolate_leading_edge(
        AVL_UNDEFORMED_PATH,
        CASE_PATH,
        wg_origin,
        wg_scaling,
        y_queries=wing_df["y"].unique(),
        n_iter=n_iter,
    )
    leading_edge = []
    trailing_edge = []

    Xte = Xle + chord_profile(Yle)
    Yte = Yle
    Zte = Zle

    for i, xle in enumerate(Xle):
        leading_edge.append({"x": xle, "y": Yle[i], "z": Zle[i], "Fx": 0.0, "Fy": 0.0, "Fz": 0.0})

    for i, xte in enumerate(Xte):
        trailing_edge.append({"x": xte, "y": Yte[i], "z": Zte[i], "Fx": 0.0, "Fy": 0.0, "Fz": 0.0})

    leading_edge_df = DataFrame(leading_edge)
    trailing_edge_df = DataFrame(trailing_edge)

    # Concatenate LE and TE points to the VLM panels points
    wing_df = pd.concat([wing_df, leading_edge_df, trailing_edge_df], ignore_index=True)

    wing_df.sort_values(by="y", inplace=True)
    wing_df.reset_index(drop=True, inplace=True)
    wing_df["chord_length"] = chord_profile(wing_df["y"])
    wing_df["AoA"] = twist_profile(wing_df["y"])

    if n_iter == 1:
        centerline_df = (
            wing_df.groupby("y")[["x", "z"]].max() + wing_df.groupby("y")[["x", "z"]].min()
        ) / 2
        centerline_df = centerline_df.reset_index().reindex(columns=["x", "y", "z"])

        # Select the good number of beam nodes
        if N_beam < len(centerline_df):
            target_y_values = np.linspace(
                centerline_df["y"].min(), centerline_df["y"].max(), int(N_beam)
            )
            selected_indices = []
            for target_y in target_y_values:
                closest_index = (centerline_df["y"] - target_y).abs().idxmin()
                selected_indices.append(closest_index)

            centerline_df = centerline_df.loc[selected_indices].sort_index().reset_index(drop=True)

        centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0.0
        centerline_df["x_new"] = centerline_df["x"]
        centerline_df["y_new"] = centerline_df["y"]
        centerline_df["z_new"] = centerline_df["z"]
        centerline_df["thx_new"] = 0.0
        centerline_df["thy_new"] = 0.0
        centerline_df["thz_new"] = 0.0
        centerline_df["AoA"] = twist_profile(centerline_df["y"])
        centerline_df["AoA_new"] = centerline_df["AoA"]
        internal_load_df = centerline_df.copy(deep=True)

        centerline_df["node_uid"] = centerline_df.apply(
            lambda row: "wing1_node" + str(row.name + 1), axis=1
        )
        centerline_df["cross_section_uid"] = centerline_df.apply(
            lambda row: "wing1_cross-sec" + str(row.name + 1), axis=1
        )

        centerline_df["cross_section_area"] = aera_profile(centerline_df["y"])
        centerline_df["cross_section_Ix"] = Ix_profile(centerline_df["y"])
        centerline_df["cross_section_Iy"] = Iy_profile(centerline_df["y"])
        centerline_df["cross_section_J"] = (
            centerline_df["cross_section_Ix"] + centerline_df["cross_section_Iy"]
        )

    else:
        internal_load_df = centerline_df.copy(deep=True)
        centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0.0
        centerline_df["x"] = centerline_df["x_new"]
        centerline_df["y"] = centerline_df["y_new"]
        centerline_df["z"] = centerline_df["z_new"]
        centerline_df["AoA"] = centerline_df["AoA_new"]

    # Nearest neighbor interpolation between VLM and structrual meshes
    distances = cdist(wing_df[["x", "y", "z"]], centerline_df[["x", "y", "z"]])
    closest_centerline_indices = distances.argmin(axis=1)

    for coord in ["x", "y", "z"]:
        wing_df["closest_centerline_" + coord] = centerline_df.loc[
            closest_centerline_indices, coord
        ].values

    wing_df["closest_centerline_index"] = closest_centerline_indices

    wing_df[["Mx", "My", "Mz", "distance_vector"]] = wing_df.apply(
        partial(compute_distance_and_moment, centerline_df), axis=1
    )

    for i, centerline_index in enumerate(wing_df["closest_centerline_index"]):
        for force in ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]:
            centerline_df.at[centerline_index, force] += wing_df.at[i, force]

    log.info(f"Total aerodynamic force: {centerline_df['Fz'].sum():.2f} N.")

    return wing_df, centerline_df, internal_load_df


# TODO: Reduce complexity
def compute_cross_section(
    cpacs: CPACS,
) -> Tuple[List, List, List, List, List, List, List, List, List, List]:
    """
    Computes the area, the second moments of area,
    and additional geometric properties
    of each cross-section of the wing.

    Returns:
        wg_origin: list of the coordinates of the origin of the wing geometry.
        wg_twist_list: list of the twist angle of each cross-section [deg].
        area_list: list of the area of each cross-section [m^2].
        Ix_list: list of the second moment of area about the x-axis for each
                        cross-section [m^4].
        Iy_list: list of the second moment of area about the y-axis for each
                        cross-section [m^4].
        wg_center_x_list: list of the x-coordinates of the center of each
                        cross-section [m].
        wg_center_y_list: list of the y-coordinates of the center of each
                                 cross-section [m].
        wg_center_z_list: list of the z-coordinates of the center of each
                                 cross-section [m].
        wg_chord_list: list of the chord length of each cross-section [m].

    """
    tixi = cpacs.tixi

    # Wing(s) ------------------------------------------------------------------
    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")
        log.info(str(wing_cnt) + " wings has been found.")
    else:
        wing_cnt = 0
        log.warning("No wings has been found in this CPACS file!")

    # Initialization of the lists
    wg_twist_list = []
    area_list = []
    wg_center_x_list = []
    wg_center_y_list = []
    wg_center_z_list = []
    wg_chord_list = []
    Ix_list = []
    Iy_list = []

    for i_wing in range(1):
        wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"
        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_transf = Transformation()

        # Convert WingSkeleton rotation
        wg_sk_transf.rotation = euler2fix(wing_transf.rotation)

        # Add WingSkeleton origin
        wg_sk_transf.translation = wing_transf.translation

        wg_origin = [
            round(wg_sk_transf.translation.x, 3),
            round(wg_sk_transf.translation.y, 3),
            round(wg_sk_transf.translation.z, 3),
        ]

        wg_scaling = [
            round(wing_transf.scaling.x, 3),
            round(wing_transf.scaling.y, 3),
            round(wing_transf.scaling.z, 3),
        ]

        # Positionings
        sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, wing_xpath, "wing")
        for i_sec in range(sec_cnt):
            sec_xpath = wing_xpath + "/sections/section[" + str(i_sec + 1) + "]"
            sec_uid = tixi.getTextAttribute(sec_xpath, "uID")
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(sec_xpath + "/elements", "element")

            if elem_cnt > 1:
                log.warning(
                    f"Sections {sec_uid} contains multiple element,"
                    " it could be an issue for the conversion to SUMO!"
                )

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + "/elements/element[" + str(i_elem + 1) + "]"
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi, elem_xpath)

                # Get wing profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath + "/airfoilUID")
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi, prof_uid)
                prof_vect_x = np.array(prof_vect_x, dtype=float)
                prof_vect_y = np.array(prof_vect_y, dtype=float)
                prof_vect_z = np.array(prof_vect_z, dtype=float)

                x, y, z = prod_points(elem_transf.scaling, sec_transf.scaling, wing_transf.scaling)
                prof_vect_x *= x
                prof_vect_y *= y
                prof_vect_z *= z

                prof_size_x = max(prof_vect_x) - min(prof_vect_x)
                prof_size_y = max(prof_vect_y) - min(prof_vect_y)

                if prof_size_y == 0:
                    # prof_vect_x[:] = [x / prof_size_x for x in prof_vect_x]
                    # prof_vect_z[:] = [z / prof_size_x for z in prof_vect_z]

                    wg_sec_chord = prof_size_x
                else:
                    log.error("An airfoil profile is not define correctly")

                # Add rotation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                x, y, z = sum_points(
                    elem_transf.rotation, sec_transf.rotation, sec_transf.rotation
                )
                add_rotation = Point(x, y, z)

                # Get Section rotation
                wg_sec_rot = euler2fix(add_rotation)
                # wg_sec_twist = math.radians(wg_sec_rot.y)

                wg_sec_center_x = (
                    elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
                ) * wing_transf.scaling.x

                wg_sec_center_y = (
                    elem_transf.translation.y * sec_transf.scaling.y
                    + sec_transf.translation.y
                    + pos_y_list[i_sec]
                ) * wing_transf.scaling.y

                wg_sec_center_z = (
                    elem_transf.translation.z * sec_transf.scaling.z
                    + sec_transf.translation.z
                    + pos_z_list[i_sec]
                ) * wing_transf.scaling.z

                wg_twist_list.append(wg_sec_rot.y)
                area_list.append(poly_area(prof_vect_x, prof_vect_z))
                Ix, Iy = second_moments_of_area(x=prof_vect_x, y=prof_vect_z)
                Ix_list.append(Ix)
                Iy_list.append(Iy)

                wg_center_x_list.append(wg_sec_center_x)
                wg_center_y_list.append(wg_sec_center_y)
                wg_center_z_list.append(wg_sec_center_z)
                wg_chord_list.append(wg_sec_chord)

                log.info(f"Section number: {i_sec}")
                log.info(
                    "Area of the sections:   "
                    f"[{', '.join([f'{area:.2e}' for area in area_list])}] m^2."
                )
                log.info(
                    "Ix of the sections:     "
                    f"[{', '.join([f'{Ix:.2e}' for Ix in Ix_list])}] m^4."
                )
                log.info(
                    "Iy of the sections:     "
                    f"[{', '.join([f'{Iy:.2e}' for Iy in Iy_list])}] m^4."
                )

    return (
        wg_origin,
        wg_twist_list,
        area_list,
        Ix_list,
        Iy_list,
        wg_center_x_list,
        wg_center_y_list,
        wg_center_z_list,
        wg_chord_list,
        wg_scaling,
    )


def write_deformed_geometry(UNDEFORMED_PATH, DEFORMED_PATH, centerline_df, deformed_df):
    """
    Function 'write_deformed_geometry' writes the AVL geometry input file of the
    deformed wing.

    Args:
        UNDEFORMED_PATH (Path): path to the undeformed AVL input file.
        DEFORMED_PATH (Path): path to the deformed AVL input file.
        centerline_df (pandas dataframe): dataframe containing the beam nodes.
        deformed_df (pandas dataframe): dataframe containing the VLM nodes.
    """

    deformed_df.sort_values(by="y_leading", inplace=True)
    deformed_df.reset_index(drop=True, inplace=True)
    twist_profile = interpolate.interp1d(
        centerline_df["y_new"], centerline_df["AoA_new"], fill_value="extrapolate"
    )

    with open(UNDEFORMED_PATH, "r") as file_undeformed:
        with open(DEFORMED_PATH, "w") as file_deformed:

            lines = file_undeformed.readlines()
            for i, line in enumerate(lines):
                if "SCALE" not in line:
                    file_deformed.write(line)
                else:
                    break
            airfoil_file = None
            for i, line in enumerate(lines):
                if "Nspanwise" in line:
                    values = lines[i + 1].strip().split()
                    Nspanwise = int(float(values[2]))

                if line.strip().upper() == "AFILE":
                    if i + 1 < len(lines):
                        airfoil_file = lines[i + 1].strip()
                        break

            if airfoil_file is None:
                raise FileNotFoundError("AFILE not found.")

            file_deformed.writelines(
                [
                    "SCALE\n",
                    "1.0\t1.0\t1.0\n\n",
                    "TRANSLATE\n",
                    "0.0\t0.0\t0.0\n\n",
                    "#---------------\n",
                ]
            )

            y_coords = deformed_df["y_leading"].values
            y_root = y_coords[0]
            y_tip = y_coords[-1]
            dy_min = (y_tip - y_root) / Nspanwise

            selected_indices = [0]
            last_y = y_coords[0]

            for i in range(1, len(y_coords)):
                if y_coords[i] - last_y >= dy_min and y_coords[i] + dy_min <= y_tip:
                    selected_indices.append(i)
                    last_y = y_coords[i]

            if selected_indices[-1] != len(y_coords) - 1:
                selected_indices.append(len(y_coords) - 1)

            for i_node in selected_indices:
                x_new = deformed_df.iloc[i_node]["x_leading"]
                y_new = deformed_df.iloc[i_node]["y_leading"]
                z_new = deformed_df.iloc[i_node]["z_leading"]
                chord = deformed_df.iloc[i_node]["chord"]
                AoA = twist_profile(y_new)

                file_deformed.writelines(
                    [
                        "SECTION\n",
                        "#Xle    Yle    Zle     Chord   Ainc\n",
                        f"{x_new:.3f} {y_new:.3f} {z_new:.3e} {chord:.3f} {AoA:.3e}\n\n",
                        "AFILE\n",
                        f"{airfoil_file}\n\n",
                        "#---------------\n",
                    ]
                )


def write_deformed_command(UNDEFORMED_COMMAND, DEFORMED_COMMAND) -> None:
    """
    Function 'write_deformed_command' writes the AVL command file to execute
    the computations for the deformed wing.

    Args:
        UNDEFORMED_COMMAND (Path): path to the command file for the undeformed wing.
        DEFORMED_COMMAND (Path): path to the command file for the deformed wing.
    """
    with open(UNDEFORMED_COMMAND, "r") as undeformed:
        with open(DEFORMED_COMMAND, "w") as deformed:
            deformed.write("load deformed.avl\n")
            for line in undeformed:
                if "load" not in line:
                    deformed.write(line)


def interpolate_leading_edge(
    avl_undeformed_path: Path,
    case_path: Path,
    wg_origin: List,
    wg_scaling: List,
    y_queries: List,
    n_iter: int,
) -> Tuple[ndarray, ndarray, ndarray, ndarray, ndarray, ndarray]:
    """Function to get the coordinates of the leading-edge points.

    Args:
        avl_undeformed_path (Path): path to the undeformed AVL geometry.
        case_path (Path): path to the flight case directory.
        wg_origin (list): coordinates of the origin of the wing geometry [m].
        wg_scaling (list): scaling factors for the wing geometry.
        y_queries (list): unique spanwise locations of the VLM panels [m].
        n_iter (int): number of the current iteration.

    Returns:
        xle_array: x-coordinates of the LE points.
        yle_array: y-coordinates of the LE points.
        zle_array: z-coordinates of the LE points.
        interpolated_xle: interpolated x-coordinates of the LE points.
        interpolated_yle: interpolated y-coordinates of the LE points.
        interpolated_zle: interpolated z-coordinates of the LE points.
    """
    xle_list, yle_list, zle_list = [], [], []
    surface_count = 0

    if n_iter == 1:
        path_to_read = avl_undeformed_path
    else:
        path_to_read = Path(case_path, f"Iteration_{n_iter}", "AVL", "deformed.avl")

    with open(path_to_read, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "SURFACE" in line:
                surface_count += 1
                if surface_count > 1:
                    break

            if "Xle" in line:
                next_line = lines[i + 1].strip()
                parts = next_line.split()
                if n_iter == 1:
                    xle_list.append(float(parts[0]) * wg_scaling[0] + wg_origin[0])
                    yle_list.append(float(parts[1]) * wg_scaling[1] + wg_origin[1])
                    zle_list.append(float(parts[2]) * wg_scaling[2] + wg_origin[2])
                else:
                    xle_list.append(float(parts[0]))
                    yle_list.append(float(parts[1]))
                    zle_list.append(float(parts[2]))

    xle_array = np.array(xle_list)
    yle_array = np.array(yle_list)
    zle_array = np.array(zle_list)

    interpolated_points = interpolate_leading_edge_points(
        xle_array, yle_array, zle_array, y_queries
    )

    interpolated_xle = interpolated_points[:, 0]
    interpolated_yle = interpolated_points[:, 1]
    interpolated_zle = interpolated_points[:, 2]

    return (
        xle_array,
        yle_array,
        zle_array,
        interpolated_xle,
        interpolated_yle,
        interpolated_zle,
    )
