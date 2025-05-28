"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/SU2Run/func/extractloads.py'
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import numpy as np

from unittest.mock import mock_open
from ceasiompy.SU2Run.func.extractloads import (
    compute_point_normals,
    compute_forces,
    dimensionalize_pressure,
    write_updated_mesh,
    get_mesh_markers_ids,
    extract_loads,
)

from unittest import main
from unittest.mock import MagicMock

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestSU2ExtractLoads(unittest.TestCase):

    def test_compute_point_normals(self):
        coords = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        cells = np.array([[0, 1, 2]])
        normals = compute_point_normals(coords, cells)
        self.assertEqual(normals.shape, (3, 3))

    @patch("ceasiompy.SU2Run.func.extractloads.compute_point_normals")
    @patch("ceasiompy.SU2Run.func.extractloads.vtk_to_numpy")
    @patch("ceasiompy.SU2Run.func.extractloads.get_mesh_markers_ids")
    @patch("ceasiompy.SU2Run.func.extractloads.pd.DataFrame")
    @patch("ceasiompy.SU2Run.func.extractloads.vtk.vtkXMLUnstructuredGridReader")
    def test_compute_forces(
        self, mock_reader, mock_df, mock_get_markers, mock_vtk_to_numpy, mock_compute_normals
    ):
        # Setup mocks
        mock_mesh = MagicMock()
        mock_reader.return_value.GetOutput.return_value = mock_mesh
        mock_vtk_to_numpy.side_effect = [
            np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),  # coords
            np.array([3, 0, 1, 2]),                       # cells (VTK triangle cell)
            np.array([1.0, 2.0, 3.0]),                    # pressure
        ]
        mock_compute_normals.return_value = np.ones((3, 3))
        mock_get_markers.return_value = {"marker": [0, 1, 2]}
        mock_df.return_value.to_csv = MagicMock()
        config_dict = {"MESH_FILENAME": "dummy.su2"}
        _ = compute_forces("dummy.vtu", "dummy_force.csv", config_dict)
        self.assertTrue(mock_df.called)
        self.assertTrue(mock_get_markers.called)

    def test_dimensionalize_pressure_dimensional(self):
        p = np.array([101325.0, 101400.0])
        config_dict = {
            "REF_DIMENSIONALIZATION": "DIMENSIONAL",
            "FREESTREAM_PRESSURE": 101325.0
        }
        result = dimensionalize_pressure(p, config_dict)
        np.testing.assert_array_almost_equal(result, np.array([0.0, 75.0]))

    def test_dimensionalize_pressure_freestream_press_eq_one(self):
        p = np.array([1.0, 2.0])
        config_dict = {
            "REF_DIMENSIONALIZATION": "FREESTREAM_PRESS_EQ_ONE",
            "FREESTREAM_PRESSURE": 100000.0
        }
        result = dimensionalize_pressure(p, config_dict)
        np.testing.assert_array_almost_equal(result, np.array([0.0, 100000.0]))

    def test_dimensionalize_pressure_freestream_vel_eq_mach(self):
        p = np.array([1.0, 2.0])
        config_dict = {
            "REF_DIMENSIONALIZATION": "FREESTREAM_VEL_EQ_MACH",
            "FREESTREAM_PRESSURE": 100000.0,
            "GAMMA_VALUE": 1.4
        }
        result = dimensionalize_pressure(p, config_dict)
        np.testing.assert_array_almost_equal(result, np.array([40000.0, 180000.0]))

    def test_dimensionalize_pressure_freestream_vel_eq_one(self):
        p = np.array([1.0, 2.0])
        config_dict = {
            "REF_DIMENSIONALIZATION": "FREESTREAM_VEL_EQ_ONE",
            "FREESTREAM_PRESSURE": 100000.0,
            "GAMMA_VALUE": 1.4,
            "MACH_NUMBER": 2.0
        }
        result = dimensionalize_pressure(p, config_dict)
        np.testing.assert_array_almost_equal(result, np.array([460000.0, 1020000.0]))

    @patch("ceasiompy.SU2Run.func.extractloads.vtk.vtkXMLUnstructuredGridWriter")
    def test_write_updated_mesh(self, mock_writer):
        mesh = MagicMock()
        new_vtu_file_path = "dummy_out.vtu"
        write_updated_mesh(mesh, new_vtu_file_path)
        self.assertTrue(mock_writer.return_value.SetInputData.called)
        self.assertTrue(mock_writer.return_value.SetFileName.called)
        self.assertTrue(mock_writer.return_value.Update.called)

    @patch("builtins.open", new_callable=mock_open, read_data="MARKER_TAG=TestMarker\n0 1 2 3\n")
    @patch("ceasiompy.SU2Run.func.extractloads.log")
    def test_get_mesh_markers_ids(self, mock_log, _):
        result = get_mesh_markers_ids("dummy.su2")
        self.assertIn("TestMarker", result)
        self.assertIsInstance(result["TestMarker"], list)
        mock_log.info.assert_called()

    @patch("ceasiompy.SU2Run.func.extractloads.write_updated_mesh")
    @patch("ceasiompy.SU2Run.func.extractloads.compute_forces")
    @patch("ceasiompy.SU2Run.func.extractloads.ConfigFile")
    def test_extract_loads(self, mock_configfile, mock_compute_forces, mock_write_updated_mesh):
        mock_configfile.return_value.data = {"dummy": "value"}
        mock_compute_forces.return_value = MagicMock()
        extract_loads("dummy_dir")
        self.assertTrue(mock_configfile.called)
        self.assertTrue(mock_compute_forces.called)
        self.assertTrue(mock_write_updated_mesh.called)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
