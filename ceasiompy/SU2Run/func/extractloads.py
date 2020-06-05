"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
based on a script from Jan-Niclas Walther (DLR)

Small description of the script

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-09-24
| Last modifiction: 2020-06-04

TODO:

    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import pandas
import matplotlib

import vtk
import numpy as np
from scipy.sparse import csr_matrix
from six import iteritems
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name
from ceasiompy.utils.mathfunctions import euler2fix, fix2euler
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

from ceasiompy.utils.su2functions import read_config

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def compute_point_normals(coord, cells):
    """ Function the normal vectors

    Function 'compute_point_normals' computes normals at points weighted by the
    area of the surrounding cells on a triangular mesh.

    Args:
        coords (array): np.ndarray(n, k) List of n k-dimensional coordinate points
        cells (array): np.ndarray(m, 3) Triangular cell connectivity

    Returns:
        point_nvecs (array): np.ndarray(n, k) List of k-dimensional normal vector at the n points
    """

    cell_vecs = np.diff(coord[cells], axis=1)
    cell_nvecs = np.cross(-cell_vecs[:, 0, :], cell_vecs[:, 1, :]) / 2.

    cell_sp = csr_matrix((np.ones(cells.shape[0]*3),
                         cells.flat, np.arange(0, 3*cells.shape[0]+1, 3)),
                         shape=(cells.shape[0],
                         coord.shape[0]))

    return cell_sp.T.dot(cell_nvecs) / 3.


def compute_forces(vtu_file_path, force_file_path, config_dict):
    """ Function to compute force of a VTU file

    Function 'compute_forces' computes surface forces at points for SU2 result
    files.

    Args:
        vtu_file_path (str): Path of the VTU file
        force_file_path (str): Path to the results force file to write
        config_dict (dict): SU2 cfg file dictionary to dimensionalize
                            non-dimensional output

    Returns:
        mesh (vtkhelpers object instance): Python instance of SU2 result file
                                           with added force and normal vectors
    """

    # To read .vtk file
    # reader = vtk.vtkUnstructuredGridReader()
    # reader.SetFileName(vtu_file_path)
    # reader.SetReadAllNormals(1)
    # reader.SetReadAllScalars(1)
    # reader.SetReadAllTensors(1)
    # reader.SetReadAllVectors(1)

    # To read .vtu file
    reader = vtk.vtkXMLUnstructuredGridReader() #test
    reader.SetFileName(vtu_file_path)

    reader.Update()
    mesh = reader.GetOutput()

    coord = vtk_to_numpy(mesh.GetPoints().GetData())
    cells = vtk_to_numpy(mesh.GetCells().GetData()).reshape(-1, 4)[:, 1:]
    point_nvecs = compute_point_normals(coord, cells)

    press = np.ascontiguousarray(
        vtk_to_numpy(mesh.GetPointData().GetAbstractArray('Pressure'))
        ).astype(np.double)

    # TODO raine ERROR, now we need config_dict anyway
    if config_dict is not None:
        press = dimensionalize_pressure(press, config_dict)


    force = point_nvecs * press[:, None]

    #unit_norm = point_nvecs / np.linalg.norm(point_nvecs, axis=1, keepdims=True) # had to chage that with the last version of numpy
    unit_norm = point_nvecs / np.linalg.norm(point_nvecs)

    for name, values in iteritems({'n': unit_norm, 'f': force}):
        vectors = numpy_to_vtk(
            np.ascontiguousarray(values).astype(np.double),
            deep=True, array_type=vtk.VTK_FLOAT)
        vectors.SetName(name)
        mesh.GetPointData().AddArray(vectors)
        mesh.GetPointData().SetActiveVectors(name)

    # Write CSV force file
    ids = range(len(coord))

    su2_mesh_path = config_dict.get('MESH_FILENAME')

    marker_dict = get_mesh_markers_ids(su2_mesh_path)
    mesh_maker = []

    # Find which marker corespond to which ids
    for i in range(len(coord)):
        id_to_test = ids[i]

        find = False
        for marker, ids_list in marker_dict.items():
            if not find:
                if id_to_test in ids_list:
                    mesh_maker.append(marker)
                    find = True

    df = pandas.DataFrame(data={"ids": ids,
                                'x': coord[:,0],'y': coord[:,1],'z': coord[:,2],
                                'fx': force[:,0],'fy': force[:,1],'fz': force[:,2],
                                'marker': mesh_maker })

    df.to_csv(force_file_path, sep=',',index=False)

    return mesh


def dimensionalize_pressure(p, config_dict):
    """ Function to dimensionalize pressure

    Function 'dimensionalize_pressure' retrurns the pressures values
    dimensionalize accorind to data from the SU2 configuration file

    Args:
        p (list): Pressure values
        config_dict (dict): SU2 cfg file dictionary to
                            dimensionalize non-dimensional output

    Returns:
        p (list): New pressure values
    """

    ref_dim = config_dict.get('REF_DIMENSIONALIZATION', 'DIMENSIONAL')
    p_inf = float(config_dict.get('FREESTREAM_PRESSURE', 101325.0))
    gamma = float(config_dict.get('GAMMA_VALUE', 1.4))
    ma = float(config_dict.get('MACH_NUMBER', 0.78))

    if ref_dim == 'DIMENSIONAL':
        return p - p_inf
    elif ref_dim == 'FREESTREAM_PRESS_EQ_ONE':
        return (p - 1) * p_inf
    elif ref_dim == 'FREESTREAM_VEL_EQ_MACH':
        return (p * gamma - 1) * p_inf
    elif ref_dim == 'FREESTREAM_VEL_EQ_ONE':
        return (p * gamma * ma**2 - 1) * p_inf


def write_updated_mesh(mesh, new_vtu_file_path):
    """ Function to write the new VTU file

    Function 'write_updated_mesh' crete new VTU file with utdated value given
    by 'mesh' and save at 'new_vtu_file_path'

    Args:
        mesh (vtkhelpers object instance): Python instance of SU2 result file
                                           with added force and normal vectors
        new_vtu_file_path (str): New VTU file path

    """

    # To write .vtk file
    #writer = vtk.vtkUnstructuredGridWriter()
    #writer.SetFileType(0)

    # To write .vtu file
    writer = vtk.vtkXMLUnstructuredGridWriter()

    try:
        source = mesh.GetOutput()
    except AttributeError:
        source = mesh
    writer.SetInputData(source)
    writer.SetFileName(new_vtu_file_path)
    writer.Update()


# TODO: maybe create some exteral function to cope with SU2Mesh, get coord, get marker ...
def get_mesh_markers_ids(su2_mesh_path):
    """ Function to get ids corresponding to each marker

    Function 'get_mesh_markers_ids' crete dictionary which contains for each
    mesh marker (keys) a list of ids belonging to this mesh marker

    Args:
        su2_mesh_path (str): Path to the SU2 mesh file

    Return:
        marker_dict (dict): Dictionary of marker and ids

    """

    marker_dict = {}
    ids_list = []
    start_line_nb = 1e14

    with open(su2_mesh_path) as f:
        for line_nb, line in enumerate(f.readlines()):

            if 'Farfield' in line:
                start_line_nb = 1e14

            if 'NPERIODIC' in line:
                start_line_nb = 1e14

            if ('MARKER_TAG' in line and 'Farfield' not in line):
                new_marker = line.split('=')[1][:-1]  # -1 to remove "\n"
                marker_dict[new_marker] = []
                start_line_nb = line_nb
                log.info('Mesh marker ' + new_marker + ' start at line: ' + str(start_line_nb))

            if line_nb > start_line_nb+1 :
                # print(line)
                line_ids = line.split('\n')[0].split()
                # print(line_ids)
                marker_dict[new_marker].append(int(line_ids[1]))
                marker_dict[new_marker].append(int(line_ids[2]))
                marker_dict[new_marker].append(int(line_ids[3]))

    # Remove double elements and replace ids by coordinates
    for key, ids_list in marker_dict.items():
        new_ids_list = list(dict.fromkeys(ids_list))
        marker_dict[key] = new_ids_list
        log.info('Mesh marker ' + key + ' contains ' + str(len(marker_dict[key])) + ' points.')

    if not marker_dict:
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return marker_dict


def extract_loads(results_files_dir):
    """ Function to extract loads from a SU2 resuts file.

    Function 'extract_loads'

    Args:
        results_files_dir (str): Path to the directory where results from SU2
                                 are saved.

    """

    # Path definitons
    config_file_path = results_files_dir + '/ConfigCFD.cfg'
    surface_flow_file_path = results_files_dir + '/surface_flow.vtu'  # .vtu are creteted by SU2 from v7.0.1
    surface_flow_force_file_path = results_files_dir + '/surface_flow_forces.vtu'
    force_file_path = results_files_dir + '/force.csv'

    cfg = read_config(config_file_path)
    updated_mesh = compute_forces(surface_flow_file_path, force_file_path, cfg)
    write_updated_mesh(updated_mesh, surface_flow_force_file_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')

    # TODO: adapt to be use as stand alone
