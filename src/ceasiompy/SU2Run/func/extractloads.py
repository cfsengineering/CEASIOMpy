"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
based on a script from Jan-Niclas Walther (DLR)

| Author: Aidan Jungo
| Creation: 2019-09-24

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import vtk
import numpy as np
import pandas as pd

from six import iteritems
from vtkmodules.util.numpy_support import (
    numpy_to_vtk,
    vtk_to_numpy,
)

from pathlib import Path
from numpy import ndarray
from scipy.sparse import csr_matrix
from ceasiompy.utils.configfiles import ConfigFile
from typing import (
    Dict,
    List,
)

from ceasiompy import log
from ceasiompy.utils.commonnames import (
    CONFIG_CFD_NAME,
    FORCE_FILE_NAME,
    SURFACE_FLOW_FILE_NAME,
    SURFACE_FLOW_FORCE_FILE_NAME,
)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def compute_point_normals(coord: ndarray, cells: ndarray) -> ndarray:
    """
    Computes normals at points weighted by the area of the surrounding cells on a triangular mesh.

    Args:
        coords (ndarray): (n, k)-dimensional coordinate points.
        cells (ndarray): (m, 3) triangular cell connectivity.

    Returns:
        point_nvecs (ndarray): (n, k)-dimensional normal vector at the n points.

    """

    cell_vecs = np.diff(coord[cells], axis=1)
    cell_nvecs = np.cross(-cell_vecs[:, 0, :], cell_vecs[:, 1, :]) / 2.0

    cell_sp = csr_matrix(
        (
            np.ones(cells.shape[0] * 3),
            cells.flat,
            np.arange(0, 3 * cells.shape[0] + 1, 3),
        ),
        shape=(cells.shape[0], coord.shape[0]),
    )

    return cell_sp.T.dot(cell_nvecs) / 3.0


def compute_forces(
    vtu_file_path: str,
    force_file_path: str,
    config_dict: Dict,
) -> vtk.vtkXMLUnstructuredGridReader:
    """
    Computes surface forces at points for SU2 result files.
    Saves forces dataframe at force_file_path.

    Args:
        vtu_file_path (str): Path of the VTU file.
        force_file_path (str): Path to the results force file to write.
        config_dict (dict): SU2 cfg file dictionary to dimensionalize non-dimensional output.

    Returns:
        mesh (vtk.vtkXMLUnstructuredGridReader): SU2 result file with force and normal vectors.

    """

    # To read .vtu file
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(vtu_file_path)

    reader.Update()
    mesh = reader.GetOutput()

    coord = vtk_to_numpy(mesh.GetPoints().GetData())
    cells = vtk_to_numpy(mesh.GetCells().GetData()).reshape(-1, 4)[:, 1:]
    point_nvecs = compute_point_normals(coord, cells)

    # Access pressure at each PointData
    pressure = np.ascontiguousarray(
        vtk_to_numpy(mesh.GetPointData().GetAbstractArray("Pressure"))
    ).astype(np.double)

    # TODO raise ERROR, now we need config_dict anyway
    if config_dict is not None:
        pressure = dimensionalize_pressure(pressure, config_dict)

    force = point_nvecs * pressure[:, None]

    unit_norm = point_nvecs / np.linalg.norm(point_nvecs)

    for name, values in iteritems({"n": unit_norm, "f": force}):
        vectors = numpy_to_vtk(
            np.ascontiguousarray(values).astype(np.double),
            deep=True,
            array_type=vtk.VTK_FLOAT,
        )
        vectors.SetName(name)
        mesh.GetPointData().AddArray(vectors)
        mesh.GetPointData().SetActiveVectors(name)

    # Write CSV force file
    ids = range(len(coord))

    su2_mesh_path = config_dict.get("MESH_FILENAME")
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

    df = pd.DataFrame(
        data={
            "ids": ids,
            "x": coord[:, 0],
            "y": coord[:, 1],
            "z": coord[:, 2],
            "fx": force[:, 0],
            "fy": force[:, 1],
            "fz": force[:, 2],
            "marker": mesh_maker,
        }
    )

    df.to_csv(force_file_path, sep=",", index=False)

    return mesh


def dimensionalize_pressure(p: List, config_dict: Dict) -> List:
    """
    Returns the pressures values dimensionalized
    accoring to data from the SU2 configuration file.

    Args:
        p (list): Pressure values.
        config_dict (dict): SU2 cfg file dictionary to dimensionalize non-dimensional output.

    Returns:
        p (list): Dimensionalized pressure values.

    """

    ref_dim = config_dict.get("REF_DIMENSIONALIZATION", "DIMENSIONAL")
    p_inf = float(config_dict.get("FREESTREAM_PRESSURE", 101325.0))
    gamma = float(config_dict.get("GAMMA_VALUE", 1.4))
    ma = float(config_dict.get("MACH_NUMBER", 0.78))

    if ref_dim == "DIMENSIONAL":
        return p - p_inf
    elif ref_dim == "FREESTREAM_PRESS_EQ_ONE":
        return (p - 1) * p_inf
    elif ref_dim == "FREESTREAM_VEL_EQ_MACH":
        return (p * gamma - 1) * p_inf
    elif ref_dim == "FREESTREAM_VEL_EQ_ONE":
        return (p * gamma * ma**2 - 1) * p_inf


def write_updated_mesh(mesh: vtk.vtkXMLUnstructuredGridWriter, new_vtu_file_path: str) -> None:
    """
    Create new VTU file with updated value given by mesh
    and save at new_vtu_file_path.

    Args:
        mesh (vtk.vtkXMLUnstructuredGridWriter):
            Python instance of SU2 result file with added force and normal vectors.
        new_vtu_file_path (str): New VTU file path.

    """

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


def get_mesh_markers_ids(su2_mesh_path: str) -> Dict:
    """
    Create dictionary which contains for each mesh marker (keys)
    a list of ids belonging to this mesh marker.

    Args:
        su2_mesh_path (str): Path to the SU2 mesh file.

    Returns:
        marker_dict (dict): Dictionary of marker and ids.

    """

    marker_dict = {}
    ids_list = []
    start_line_nb = 1e14

    with open(su2_mesh_path) as f:
        for line_nb, line in enumerate(f.readlines()):

            if "Farfield" in line:
                start_line_nb = 1e14

            if "NPERIODIC" in line:
                start_line_nb = 1e14

            if "MARKER_TAG" in line and "Farfield" not in line:
                new_marker = line.split("=")[1][:-1]  # -1 to remove "\n"
                marker_dict[new_marker] = []
                start_line_nb = line_nb
                log.info("Mesh marker " + new_marker + " start at line: " + str(start_line_nb))

            if line_nb > start_line_nb + 1:
                line_ids = line.split("\n")[0].split()
                marker_dict[new_marker].append(int(line_ids[1]))
                marker_dict[new_marker].append(int(line_ids[2]))
                marker_dict[new_marker].append(int(line_ids[3]))

    # Remove double elements and replace ids by coordinates
    for key, ids_list in marker_dict.items():
        new_ids_list = list(dict.fromkeys(ids_list))
        marker_dict[key] = new_ids_list
        log.info("Mesh marker " + key + " contains " + str(len(marker_dict[key])) + " points.")

    if not marker_dict:
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return marker_dict


def extract_loads(results_files_dir: Path) -> None:
    """
    Extract loads from a SU2 resuts file.

    Args:
        results_files_dir (Path): Path to the directory where results from SU2 are saved.

    """

    # Path definitions
    config_file_path = Path(results_files_dir, CONFIG_CFD_NAME)
    surface_flow_file_path = Path(results_files_dir, SURFACE_FLOW_FILE_NAME)
    surface_flow_force_file_path = Path(results_files_dir, SURFACE_FLOW_FORCE_FILE_NAME)
    force_file_path = Path(results_files_dir, FORCE_FILE_NAME)

    # Update mesh
    config_dict = ConfigFile(config_file_path).data
    updated_mesh = compute_forces(surface_flow_file_path, force_file_path, config_dict)
    write_updated_mesh(updated_mesh, surface_flow_force_file_path)
