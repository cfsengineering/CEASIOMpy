"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to extract panel forces of a surface,
from AVL 'fe.txt' element force file

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-06-17

TODO:

    * Things to improve...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================
import re
import numpy as np
import matplotlib.pyplot as plt
import math
from pathlib import Path
from framat import Model
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.commonxpath import (
    FRAMAT_MATERIAL_XPATH,
    WINGS_XPATH
)
from cpacspy.cpacsfunctions import open_tixi
import pandas as pd
from scipy.spatial.distance import cdist
from scipy import interpolate
from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.generalclasses import SimpleNamespace, Transformation
from ceasiompy.utils.mathfunctions import euler2fix
from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord
from ceasiompy.AeroFrame_new.func.aeroframe_utils import (
    PolyArea,
    second_moments_of_area
)

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def parse_AVL_surface(string):
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

    i_newline = [i for i, char in enumerate(string) if char == '\n']

    surface_name = string[12:i_newline[0] - 1].replace(' ', '')

    str_tmp = string[i_newline[0] + 1:i_newline[1]]
    i_span = str_tmp.find("# Spanwise =")

    nspanwise = int(str_tmp[i_span + 12:i_span + 17])
    i_chordwise = [m.start() for m in re.finditer(
        "# Chordwise =", string[i_newline[1]:])]
    i_incidence = [m.start() for m in re.finditer(
        "Incidence  =", string[i_newline[1]:])]
    i_strip_width = [m.start() for m in re.finditer(
        "Strip Width  =", string[i_newline[1]:])]
    i_strip_dihed = [m.start() for m in re.finditer(
        "Strip Dihed. =", string[i_newline[1]:])]
    i_IbX = [m.start() for m in re.finditer(
        "I        X", string[i_newline[1]:])]
    nchord_strip = [0] * nspanwise
    incidence_strip = [0] * nspanwise
    width_strip = [0] * nspanwise
    dihed_strip = [0] * nspanwise
    jj = -1
    slope_list = []

    nchordwise = int(string[slice(
        i_newline[1] + i_chordwise[0] + 13, i_newline[1] + i_chordwise[0] + 16)])
    p_xyz = np.zeros((nspanwise * nchordwise, 3))
    xyz = np.zeros((nspanwise * nchordwise, 3))

    nn_vec = []
    for k in range(nspanwise):
        i0 = slice(i_newline[1] + i_chordwise[k] + 13,
                   i_newline[1] + i_chordwise[k] + 16)
        nchord_strip[k] = float(string[i0])

        i0 = slice(i_newline[1] + i_incidence[k] - 1 + 13,
                   i_newline[1] + i_incidence[k] - 1 + 24)
        incidence_strip[k] = float(string[i0])

        i0 = slice(i_newline[1] + i_strip_width[k] - 1 + 13 + 2,
                   i_newline[1] + i_strip_width[k] - 1 + 24 + 1)
        width_strip[k] = float(string[i0])

        i0 = slice(i_newline[1] + i_strip_dihed[k] - 1 + 13 + 2,
                   i_newline[1] + i_strip_dihed[k] - 1 + 24 + 1)
        dihed_strip[k] = float(string[i0])

        idd = [i for i in range(len(i_newline) - 1) if (i_IbX[k] + i_newline[1] - 1 - i_newline[i])
               * (i_IbX[k] + i_newline[1] - 1 - i_newline[i + 1]) < 0]

        sa = np.sin(np.deg2rad(incidence_strip[k]))
        ca = np.cos(np.deg2rad(incidence_strip[k]))
        sd = np.sin(np.deg2rad(dihed_strip[k]))
        cd = np.cos(np.deg2rad(dihed_strip[k]))

        nn = np.array([sa * cd, -ca * sd, ca * cd])
        nn = nn / np.linalg.norm(nn)

        ah = np.array([0, cd, sd])
        T = np.array([[0, -ah[2], ah[1]],
                      [ah[2], 0, -ah[0]],
                      [-ah[1], ah[0], 0]])

        sdx = 0
        x0 = np.zeros(int(nchord_strip[k]))
        z0 = np.zeros(int(nchord_strip[k]))

        for j in range(int(nchord_strip[k])):
            jj += 1
            line_data = string[i_newline[idd[0] + j + 1]:i_newline[idd[0] + j + 2]]
            data_list = [float(match.group()) for match in re.finditer(
                r"-?\b\d+\.\d+\b", line_data[9:])]
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
            nn1 = np.cos(phi) * nn + (1 - np.cos(phi)) * ah * \
                (ah.dot(np.transpose(nn))) + \
                np.sin(phi) * nn.dot(np.transpose(T))
            p_xyz0 = strip_area * dCp * nn1
            # cp_xyz0 = dCp * nn1
            p_xyz[jj, :] = p_xyz0
            xyz[jj, :] = xyz0
            slope_list.append(slope)

        nn_vec.append(nn1)

    return surface_name, nspanwise, nchord_strip, xyz, p_xyz, slope_list


def read_AVL_fe_file(FE_PATH, plot=False):
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
        with open(FE_PATH, 'r') as file:
            file_content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error reading {FE_PATH}")

    i_surface = [m.start() for m in re.finditer("Surface #", file_content)]
    number_surfaces = len(i_surface)
    string_surface = []

    for k in range(number_surfaces):
        if k + 1 == number_surfaces:
            ie = len(file_content)
        else:
            ie = i_surface[k + 1]

        string_surface.append(file_content[i_surface[k]:ie])

    fsclf = 10
    xyz_list = []
    p_xyz_list = []
    surface_name_list = []
    nspanwise_list = []
    nchordwise_list = []
    slope_list = []

    for k in range(number_surfaces):
        string_tmp = string_surface[k]
        surface_name, nspanwise, nchord_strip, xyz, cp_xyz, slope = parse_AVL_surface(
            string_tmp)
        surface_name_list.append(surface_name)
        nspanwise_list.append(nspanwise)
        nchordwise_list.append(nchord_strip)
        xyz_list.append(xyz)
        p_xyz_list.append(cp_xyz)
        slope_list.append(slope)

        if plot:
            plt.figure(figsize=(10, 8))
            fig = plt.figure(k + 1)
            ax = fig.add_subplot(111, projection='3d')
            ax.set_xlabel('Chord')
            ax.set_ylabel('Span')
            ax.set_title("Figure " + str(k + 1))
            xyzpf = xyz + fsclf * cp_xyz
            xpl = []
            ypl = []
            zpl = []
            for kk in range(xyzpf.shape[0]):
                xpl.extend([xyz[kk, 0], xyzpf[kk, 0], float('nan')])
                ypl.extend([xyz[kk, 1], xyzpf[kk, 1], float('nan')])
                zpl.extend([xyz[kk, 2], xyzpf[kk, 2], float('nan')])

            ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2],
                    marker='o', linestyle='', color='black')
            ax.plot(xpl, ypl, zpl, color='red')
            ax.axis('equal')

    plt.show()

    return surface_name_list, nspanwise_list, nchordwise_list, xyz_list, p_xyz_list, slope_list


def create_framat_model(young_modulus, shear_modulus, material_density,
                        centerline_df, internal_load_df):
    model = Model()

    # Material
    mat = model.add_feature('material', uid='material')
    mat.set('E', young_modulus * 1e9)
    mat.set('G', shear_modulus * 1e9)
    mat.set('rho', material_density)

    # Initialize boundary condition
    bc = model.set_feature('bc')

    # Add a single beam
    beam = model.add_feature('beam')

    # Loop through each node and add them to the beam
    for i_node in range(len(centerline_df)):
        beam.add('node', [centerline_df.iloc[i_node]["x"],
                          centerline_df.iloc[i_node]["y"],
                          centerline_df.iloc[i_node]["z"]],
                 uid=centerline_df.iloc[i_node]['node_uid'])

    # Set the number of elements for the beam
    beam.set('nelem', len(centerline_df) - 1)

    # Add orientation property to the beam
    beam.add('orientation', {'from': centerline_df.iloc[0]['node_uid'],
                             'to': centerline_df.iloc[-1]['node_uid'],
                             'up': [0, 0, 1]})
    beam.add('material', {'from': centerline_df.iloc[0]['node_uid'],
                          'to': centerline_df.iloc[-1]['node_uid'],
                          'uid': 'material'})

    # Add cross-section properties
    for i_node in range(len(centerline_df) - 1):
        cs = model.add_feature('cross_section',
                               uid=centerline_df.iloc[i_node]['cross_section_uid'])
        cs.set('A', centerline_df.iloc[i_node]["cross_section_area"])
        cs.set('Iy', centerline_df.iloc[i_node]["cross_section_Ix"])
        cs.set('Iz', centerline_df.iloc[i_node]["cross_section_Iy"])
        cs.set('J', centerline_df.iloc[i_node]["cross_section_J"])
        beam.add('cross_section',
                 {'from': centerline_df.iloc[i_node]['node_uid'],
                  'to': centerline_df.iloc[i_node + 1]['node_uid'],
                  'uid': centerline_df.iloc[i_node]['cross_section_uid']})

    # Add line loads [N/m] and point loads [N]
    for i_node in range(len(centerline_df)):
        node_uid = centerline_df.iloc[i_node]['node_uid']
        load = [centerline_df.iloc[i_node][force] - internal_load_df.iloc[i_node][force]
                for force in ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]]
        beam.add('point_load', {'at': node_uid, 'load': load})

    # ===== BOUNDARY CONDITIONS =====
    idx_to_fix = centerline_df.apply(lambda row: row['x']**2 + row['z']**2, axis=1).idxmin()
    bc.add('fix', {'node': "wing1_node" + str(idx_to_fix + 1), 'fix': ['all']})

    # ===== POST-PROCESSING =====
    pp = model.set_feature('post_proc')
    pp.set('plot_settings', {'show': False,
                             'scale_forces': 5,
                             'scale_moments': 1,
                             'scale_deformation': 10})
    pp.add('plot', ['undeformed', 'deformed', 'bc', 'global_axes'])

    return model


def get_material_properties(cpacs_path):
    """Function reads the material properties for structural
    calculations.

    Function 'get_material_properties' reads the material properties
    of the wing from the graphical user interface of CEASIOMpy, in
    order to make structural computations

    Args:
        cpacs_path (Path) : path to the cpacs input file

    Returns:

    """
    cpacs = CPACS(cpacs_path)

    young_modulus = get_value_or_default(cpacs.tixi,
                                         FRAMAT_MATERIAL_XPATH + "/YoungModulus", 70)

    shear_modulus = get_value_or_default(cpacs.tixi,
                                         FRAMAT_MATERIAL_XPATH + "/ShearModulus", 27)

    material_density = get_value_or_default(cpacs.tixi, FRAMAT_MATERIAL_XPATH + "/Density", 1960)

    return young_modulus, shear_modulus, material_density


def create_wing_centerline(wing_df, centerline_df, xyz_tot, fxyz_tot, iter, xyz_tip, tip_def,
                           aera_profile, Ix_profile, Iy_profile, chord_profile, twist_profile,
                           CASE_PATH, AVL_UNDEFORMED_PATH):

    # if iter == 1:
    #     wing_df = pd.DataFrame({'x': [row[0] for row in xyz_tot],
    #                             'y': [row[1] for row in xyz_tot],
    #                             'z': [row[2] for row in xyz_tot],
    #                             'Fx': [row[0] for row in fxyz_tot],
    #                             'Fy': [row[1] for row in fxyz_tot],
    #                             'Fz': [row[2] for row in fxyz_tot]})

    #     tip_row = pd.DataFrame([{
    #         "x": xyz_tip[0],
    #         "y": xyz_tip[1],
    #         "z": xyz_tip[2],
    #         "Fx": 0,
    #         "Fy": 0,
    #         "Fz": 0
    #     }])

    #     wing_df = pd.concat([wing_df, tip_row], ignore_index=True)

    #     Xle, Yle, Zle = interpolate_leading_edge(
    #         AVL_UNDEFORMED_PATH, CASE_PATH, iter, y_query=wing_df["y"].unique())
    #     leading_edge = []
    #     trailing_edge = []

    #     Xte = Xle + chord_profile(Yle)
    #     Yte = Yle
    #     Zte = Zle

    #     for i in range(len(Xle)):
    #         leading_edge.append({
    #             "x": Xle[i],
    #             "y": Yle[i],
    #             "z": Zle[i],
    #             "Fx": 0.0,
    #             "Fy": 0.0,
    #             "Fz": 0.0
    #         })

    #     for i in range(len(Xte)):
    #         trailing_edge.append({
    #             "x": Xte[i],
    #             "y": Yte[i],
    #             "z": Zte[i],
    #             "Fx": 0.0,
    #             "Fy": 0.0,
    #             "Fz": 0.0
    #         })

    #     leading_edge_df = pd.DataFrame(leading_edge)
    #     trailing_edge_df = pd.DataFrame(trailing_edge)

    #     wing_df = pd.concat([wing_df, leading_edge_df, trailing_edge_df], ignore_index=True)
    #     log.info(xyz_tip)

    #     wing_df.sort_values(by="y", inplace=True)
    #     wing_df.reset_index(drop=True, inplace=True)
    #     wing_df["chord_length"] = chord_profile(wing_df["y"])
    #     wing_df["AoA"] = twist_profile(wing_df["y"])

    #     centerline_df = (wing_df.groupby("y")[["x", "z"]].max(
    #     ) + wing_df.groupby("y")[["x", "z"]].min()) / 2
    #     centerline_df = centerline_df.reset_index().reindex(columns=["x", "y", "z"])
    #     centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0
    #     centerline_df["x_new"] = centerline_df["x"]
    #     centerline_df["y_new"] = centerline_df["y"]
    #     centerline_df["z_new"] = centerline_df["z"]
    #     internal_load_df = centerline_df.copy(deep=True)

    #     centerline_df['node_uid'] = centerline_df.apply(
    #         lambda row: "wing1_node" + str(row.name + 1), axis=1)
    #     centerline_df['cross_section_uid'] = centerline_df.apply(
    #         lambda row: "wing1_cross-sec" + str(row.name + 1), axis=1)

    #     centerline_df["cross_section_area"] = aera_profile(centerline_df["y"])
    #     centerline_df["cross_section_Ix"] = Ix_profile(centerline_df["y"])
    #     centerline_df["cross_section_Iy"] = Iy_profile(centerline_df["y"])
    #     centerline_df["cross_section_J"] = centerline_df["cross_section_Ix"] + \
    #         centerline_df["cross_section_Iy"]

    #     distances = cdist(wing_df[['x', 'y', 'z']], centerline_df[['x', 'y', 'z']])
    #     closest_centerline_indices = distances.argmin(axis=1)

    #     for coord in ['x', 'y', 'z']:
    #         wing_df['closest_centerline_'
    #                 + coord] = centerline_df.loc[closest_centerline_indices, coord].values

    #     wing_df['closest_centerline_index'] = closest_centerline_indices

    # else:
    #     Xle, Yle, Zle = interpolate_leading_edge(
    #         AVL_UNDEFORMED_PATH, CASE_PATH, iter, y_query=wing_df["y"].unique())
    #     leading_edge = []
    #     trailing_edge = []

    #     log.info(Xle)
    #     log.info(Yle)
    #     log.info(Zle)

    #     Xte = Xle + chord_profile(Yle)
    #     Yte = Yle
    #     Zte = Zle

    #     leading = np.column_stack((Xle, Yle, Zle))
    #     trailing = np.column_stack((Xte, Yte, Zte))

    #     log.info(tip_def[1])

    #     wing_df["x"] = [row[0]
    #                     for row in np.vstack((xyz_tot, tip_def[1], leading, trailing))]
    #     wing_df["y"] = [row[1]
    #                     for row in np.vstack((xyz_tot, tip_def[1], leading, trailing))]
    #     wing_df["z"] = [row[2]
    #                     for row in np.vstack((xyz_tot, tip_def[1], leading, trailing))]
    #     wing_df["Fx"] = [row[0]
    #                      for row in np.vstack((fxyz_tot, np.zeros((2 * len(leading) + 1, 3))))]
    #     wing_df["Fy"] = [row[1]
    #                      for row in np.vstack((fxyz_tot, np.zeros((2 * len(leading) + 1, 3))))]
    #     wing_df["Fz"] = [row[2]
    #                      for row in np.vstack((fxyz_tot, np.zeros((2 * len(leading) + 1, 3))))]
    #     internal_load_df = centerline_df.copy(deep=True)
    #     centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0
    #     centerline_df["x"] = centerline_df["x_new"]
    #     centerline_df["y"] = centerline_df["y_new"]
    #     centerline_df["z"] = centerline_df["z_new"]

    wing_df = pd.DataFrame({'x': [row[0] for row in xyz_tot],
                            'y': [row[1] for row in xyz_tot],
                            'z': [row[2] for row in xyz_tot],
                            'Fx': [row[0] for row in fxyz_tot],
                            'Fy': [row[1] for row in fxyz_tot],
                            'Fz': [row[2] for row in fxyz_tot]})

    tip_row = pd.DataFrame([{
        "x": xyz_tip[0],
        "y": xyz_tip[1],
        "z": xyz_tip[2],
        "Fx": 0,
        "Fy": 0,
        "Fz": 0
    }])

    wing_df = pd.concat([wing_df, tip_row], ignore_index=True)

    Xle, Yle, Zle = interpolate_leading_edge(AVL_UNDEFORMED_PATH,
                                             CASE_PATH, iter,
                                             y_query=wing_df["y"].unique())
    leading_edge = []
    trailing_edge = []

    Xte = Xle + chord_profile(Yle)
    Yte = Yle
    Zte = Zle

    for i in range(len(Xle)):
        leading_edge.append({
            "x": Xle[i],
            "y": Yle[i],
            "z": Zle[i],
            "Fx": 0.0,
            "Fy": 0.0,
            "Fz": 0.0
        })

    for i in range(len(Xte)):
        trailing_edge.append({
            "x": Xte[i],
            "y": Yte[i],
            "z": Zte[i],
            "Fx": 0.0,
            "Fy": 0.0,
            "Fz": 0.0
        })

    leading_edge_df = pd.DataFrame(leading_edge)
    trailing_edge_df = pd.DataFrame(trailing_edge)

    wing_df = pd.concat([wing_df, leading_edge_df, trailing_edge_df], ignore_index=True)

    wing_df.sort_values(by="y", inplace=True)
    wing_df.reset_index(drop=True, inplace=True)
    wing_df["chord_length"] = chord_profile(wing_df["y"])
    wing_df["AoA"] = twist_profile(wing_df["y"])

    if iter == 1:
        centerline_df = (wing_df.groupby("y")[["x", "z"]].max(
        ) + wing_df.groupby("y")[["x", "z"]].min()) / 2
        centerline_df = centerline_df.reset_index().reindex(columns=["x", "y", "z"])
        centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0
        centerline_df["x_new"] = centerline_df["x"]
        centerline_df["y_new"] = centerline_df["y"]
        centerline_df["z_new"] = centerline_df["z"]
        internal_load_df = centerline_df.copy(deep=True)

        centerline_df['node_uid'] = centerline_df.apply(
            lambda row: "wing1_node" + str(row.name + 1), axis=1)
        centerline_df['cross_section_uid'] = centerline_df.apply(
            lambda row: "wing1_cross-sec" + str(row.name + 1), axis=1)

        centerline_df["cross_section_area"] = aera_profile(centerline_df["y"])
        centerline_df["cross_section_Ix"] = Ix_profile(centerline_df["y"])
        centerline_df["cross_section_Iy"] = Iy_profile(centerline_df["y"])
        centerline_df["cross_section_J"] = centerline_df["cross_section_Ix"] + \
            centerline_df["cross_section_Iy"]

    else:
        internal_load_df = centerline_df.copy(deep=True)
        centerline_df[["Fx", "Fy", "Fz", "Mx", "My", "Mz"]] = 0
        centerline_df["x"] = centerline_df["x_new"]
        centerline_df["y"] = centerline_df["y_new"]
        centerline_df["z"] = centerline_df["z_new"]

    distances = cdist(wing_df[['x', 'y', 'z']], centerline_df[['x', 'y', 'z']])
    closest_centerline_indices = distances.argmin(axis=1)

    for coord in ['x', 'y', 'z']:
        wing_df['closest_centerline_'
                + coord] = centerline_df.loc[closest_centerline_indices, coord].values

    wing_df['closest_centerline_index'] = closest_centerline_indices

    def compute_distance_and_moment(row):
        point_xyz = np.array([row['x'], row['y'], row['z']])
        centerline_xyz = np.array([centerline_df.at[row['closest_centerline_index'], 'x'],
                                   centerline_df.at[row['closest_centerline_index'], 'y'],
                                   centerline_df.at[row['closest_centerline_index'], 'z']])

        distance_vector = point_xyz - centerline_xyz
        force_vector = np.array([row['Fx'], row['Fy'], row['Fz']])
        moment_vector = np.cross(distance_vector, force_vector)

        return pd.Series({
            'moment_x': moment_vector[0],
            'moment_y': moment_vector[1],
            'moment_z': moment_vector[2],
            'distance_vector': distance_vector
        })

    wing_df[['Mx', 'My', 'Mz', 'distance_vector']] = wing_df.apply(
        compute_distance_and_moment, axis=1)

    for i, centerline_index in enumerate(wing_df['closest_centerline_index']):
        for force in ['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz']:
            centerline_df.at[centerline_index, force] += wing_df.at[i, force]

    return wing_df, centerline_df, internal_load_df


def compute_cross_section(cpacs_path):
    """Function to...
    """
    tixi = open_tixi(cpacs_path)

    # Wing(s) ------------------------------------------------------------------
    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")
        log.info(str(wing_cnt) + " wings has been found.")
    else:
        wing_cnt = 0
        log.warning("No wings has been found in this CPACS file!")

    wg_origin_list = []
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

        # Positionings
        if tixi.checkElement(wing_xpath + "/positionings"):
            pos_cnt = tixi.getNamedChildrenCount(wing_xpath + "/positionings", "positioning")
            log.info(str(pos_cnt) + ' "positioning" has been found : ')

            pos_x_list = []
            pos_y_list = []
            pos_z_list = []
            from_sec_list = []
            to_sec_list = []

            for i_pos in range(pos_cnt):
                pos_xpath = wing_xpath + "/positionings/positioning[" + str(i_pos + 1) + "]"

                length = tixi.getDoubleElement(pos_xpath + "/length")
                sweep_deg = tixi.getDoubleElement(pos_xpath + "/sweepAngle")
                sweep = math.radians(sweep_deg)
                dihedral_deg = tixi.getDoubleElement(pos_xpath + "/dihedralAngle")
                dihedral = math.radians(dihedral_deg)

                # Get the corresponding translation of each positioning
                pos_x_list.append(length * math.sin(sweep))
                pos_y_list.append(length * math.cos(dihedral) * math.cos(sweep))
                pos_z_list.append(length * math.sin(dihedral) * math.cos(sweep))

                # Get which section are connected by the positioning
                if tixi.checkElement(pos_xpath + "/fromSectionUID"):
                    from_sec = tixi.getTextElement(pos_xpath + "/fromSectionUID")
                else:
                    from_sec = ""
                from_sec_list.append(from_sec)

                if tixi.checkElement(pos_xpath + "/toSectionUID"):
                    to_sec = tixi.getTextElement(pos_xpath + "/toSectionUID")
                else:
                    to_sec = ""
                to_sec_list.append(to_sec)

            # Re-loop though the positioning to re-order them
            for j_pos in range(pos_cnt):
                if from_sec_list[j_pos] == "":
                    prev_pos_x = 0
                    prev_pos_y = 0
                    prev_pos_z = 0
                elif from_sec_list[j_pos] == to_sec_list[j_pos - 1]:
                    prev_pos_x = pos_x_list[j_pos - 1]
                    prev_pos_y = pos_y_list[j_pos - 1]
                    prev_pos_z = pos_z_list[j_pos - 1]
                else:
                    index_prev = to_sec_list.index(from_sec_list[j_pos])
                    prev_pos_x = pos_x_list[index_prev]
                    prev_pos_y = pos_y_list[index_prev]
                    prev_pos_z = pos_z_list[index_prev]

                pos_x_list[j_pos] += prev_pos_x
                pos_y_list[j_pos] += prev_pos_y
                pos_z_list[j_pos] += prev_pos_z

        else:
            log.warning('No "positionings" have been found!')
            pos_cnt = 0

        # Sections
        sec_cnt = tixi.getNamedChildrenCount(wing_xpath + "/sections", "section")
        log.info("    -" + str(sec_cnt) + " wing sections have been found")

        if pos_cnt == 0:
            pos_x_list = [0.0] * sec_cnt
            pos_y_list = [0.0] * sec_cnt
            pos_z_list = [0.0] * sec_cnt

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

                # Apply scaling
                for i, item in enumerate(prof_vect_x):
                    prof_vect_x[i] = (
                        item * elem_transf.scaling.x * sec_transf.scaling.x * wing_transf.scaling.x
                    )
                for i, item in enumerate(prof_vect_y):
                    prof_vect_y[i] = (
                        item * elem_transf.scaling.y * sec_transf.scaling.y * wing_transf.scaling.y
                    )
                for i, item in enumerate(prof_vect_z):
                    prof_vect_z[i] = (
                        item * elem_transf.scaling.z * sec_transf.scaling.z * wing_transf.scaling.z
                    )

                prof_size_x = max(prof_vect_x) - min(prof_vect_x)
                prof_size_y = max(prof_vect_y) - min(prof_vect_y)

                if prof_size_y == 0:
                    prof_vect_x[:] = [x / prof_size_x for x in prof_vect_x]
                    prof_vect_z[:] = [z / prof_size_x for z in prof_vect_z]

                    wg_sec_chord = prof_size_x
                else:
                    log.error("An airfoil profile is not define correctly")

                # Add rotation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                add_rotation = SimpleNamespace()
                add_rotation.x = elem_transf.rotation.x + \
                    sec_transf.rotation.x + wg_sk_transf.rotation.x
                add_rotation.y = elem_transf.rotation.y + \
                    sec_transf.rotation.y + wg_sk_transf.rotation.y
                add_rotation.z = elem_transf.rotation.z + \
                    sec_transf.rotation.z + wg_sk_transf.rotation.z

                # Get Section rotation
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_twist = math.radians(wg_sec_rot.y)

                wg_sec_center_x = (
                    elem_transf.translation.x
                    + sec_transf.translation.x + pos_x_list[i_sec]
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

                wg_origin = [round(wg_sk_transf.translation.x + wg_sec_chord / 2, 3),
                             round(wg_sk_transf.translation.y, 3),
                             round(wg_sk_transf.translation.z, 3)]

                wg_origin_list.append(wg_origin)
                wg_twist_list.append(wg_sec_twist)
                area_list.append(PolyArea(prof_vect_x, prof_vect_z))
                Ix, Iy = second_moments_of_area(x=prof_vect_x, y=prof_vect_z)
                Ix_list.append(Ix)
                Iy_list.append(Iy)
                wg_center_x_list.append(wg_sec_center_x)
                wg_center_y_list.append(wg_sec_center_y)
                wg_center_z_list.append(wg_sec_center_z)
                wg_chord_list.append(wg_sec_chord)

    return (
        wg_origin_list, wg_twist_list, area_list, Ix_list, Iy_list,
        wg_center_x_list, wg_center_y_list, wg_center_z_list, wg_chord_list
    )


def write_deformed_geometry(UNDEFORMED_PATH, DEFORMED_PATH, deformed_df):
    deformed_df.sort_values(by="y_leading", inplace=True)
    deformed_df.reset_index(drop=True, inplace=True)
    log.info(deformed_df)
    with open(UNDEFORMED_PATH, "r") as file_undeformed:
        with open(DEFORMED_PATH, "w") as file_deformed:
            for line in file_undeformed:
                if "TRANSLATE" in line:
                    break
                file_deformed.write(line)

            file_deformed.writelines(
                ["TRANSLATE\n",
                 "0.0\t0.0\t0.0\n\n",
                 "#---------------\n"])
            step = 3
            for i_node in range(0, len(deformed_df), step):
                # for i_node in range(len(deformed_df)):
                x_new = deformed_df.iloc[i_node]["x_leading"]
                y_new = deformed_df.iloc[i_node]["y_leading"]
                z_new = deformed_df.iloc[i_node]["z_leading"]
                chord = deformed_df.iloc[i_node]["chord"]
                AoA = deformed_df.iloc[i_node]["AoA"]
                file_deformed.writelines(
                    ["SECTION\n",
                     "#Xle    Yle    Zle     Chord   Ainc\n",
                     f"{x_new:.3f} {y_new:.3f} {z_new:.3e} {chord:.3f} {AoA:.3e}\n",
                     "#---------------\n"])
            if (len(deformed_df) - 1) % step:
                x_new = deformed_df.iloc[-1]["x_leading"]
                y_new = deformed_df.iloc[-1]["y_leading"]
                z_new = deformed_df.iloc[-1]["z_leading"]
                chord = deformed_df.iloc[-1]["chord"]
                AoA = deformed_df.iloc[-1]["AoA"]
                file_deformed.writelines(
                    ["SECTION\n",
                        "#Xle    Yle    Zle     Chord   Ainc\n",
                        f"{x_new:.3f} {y_new:.3f} {z_new:.3e} {chord} {AoA:.3e}\n",
                        "#---------------\n"])


def write_deformed_command(UNDEFORMED_COMMAND, DEFORMED_COMMAND):
    with open(UNDEFORMED_COMMAND, "r") as undeformed:
        with open(DEFORMED_COMMAND, "w") as deformed:
            deformed.write("load deformed.avl\n")
            for line in undeformed:
                if "load" not in line:
                    deformed.write(line)


def interpolate_leading_edge(AVL_UNDEFORMED_PATH, CASE_PATH, iter, y_query):
    Xle_list = []
    Yle_list = []
    Zle_list = []
    # Chord_list = []

    if iter == 1:
        path_to_read = AVL_UNDEFORMED_PATH
    else:
        path_to_read = Path(CASE_PATH, f"Iteration_{iter}", "AVL", "deformed.avl")

    with open(path_to_read, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "Xle" in line:
                next_line = lines[i + 1].strip()
                parts = next_line.split()
                if iter == 1:
                    Xle_list.append(float(parts[0]) + 0.102)
                else:
                    Xle_list.append(float(parts[0]))

                Yle_list.append(float(parts[1]))
                Zle_list.append(float(parts[2]))
                # Chord_list.append(float(parts[3]))

    Xle_array = np.array(Xle_list)
    Yle_array = np.array(Yle_list)
    Zle_array = np.array(Zle_list)
    # Chord_array = np.array(Chord_list)

    def linear_interpolation(x1, y1, z1, x2, y2, z2, y_query):
        t = (y_query - y1) / (y2 - y1)
        interpolated_x = x1 + t * (x2 - x1)
        interpolated_z = z1 + t * (z2 - z1)
        return interpolated_x, y_query, interpolated_z

    interpolated_Xle, interpolated_Yle, interpolated_Zle = linear_interpolation(
        Xle_array[0], Yle_array[0], Zle_array[0],
        Xle_array[1], Yle_array[1], Zle_array[1],
        y_query
    )

    return interpolated_Xle, interpolated_Yle, interpolated_Zle,

    # =================================================================================================
    #    MAIN
    # =================================================================================================


if __name__ == "__main__":

    log.info("Nothing to execute!")
