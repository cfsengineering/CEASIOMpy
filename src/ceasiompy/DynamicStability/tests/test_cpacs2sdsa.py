"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import tempfile
import numpy as np

from pathlib import Path
from unittest import main
from unittest.mock import MagicMock
from ceasiompy.DynamicStability.func.cpacs2sdsa import SDSAFile

from unittest.mock import patch
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestSDSAFile(unittest.TestCase):
    def setUp(self):
        # Mock CPACS and TIXI
        self.mock_cpacs = MagicMock()
        self.mock_cpacs.tixi = MagicMock()
        self.mock_cpacs.tixi.getDoubleElement.return_value = 10.0
        self.mock_cpacs.tixi.getTextElement.return_value = "TestAircraft"
        self.mock_cpacs.tixi.getElement.return_value = "TestElement"
        self.mock_cpacs.tixi.getAttribute.return_value = "TestAttribute"
        self.mock_cpacs.tixi.getXPath.return_value = "TestXPath"
        self.mock_cpacs.tixi.getValue.return_value = "TestValue"

        # Patch open_tixi and shutil.copy
        patcher1 = patch(
            "ceasiompy.DynamicStability.func.cpacs2sdsa.open_tixi",
            return_value=MagicMock()
        )
        patcher2 = patch(
            "ceasiompy.DynamicStability.func.cpacs2sdsa.shutil.copy",
            return_value=None
        )
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.mock_open_tixi = patcher1.start()
        self.mock_shutil_copy = patcher2.start()

        # Patch get_value to return reasonable values
        patcher3 = patch(
            "ceasiompy.DynamicStability.func.cpacs2sdsa.get_value",
            side_effect=lambda *a, **k: "1"
        )
        self.addCleanup(patcher3.stop)
        self.mock_get_value = patcher3.start()

        # Patch aircraft_name
        patcher4 = patch(
            "ceasiompy.DynamicStability.func.cpacs2sdsa.aircraft_name",
            return_value="TestAircraft"
        )
        self.addCleanup(patcher4.stop)
        self.mock_aircraft_name = patcher4.start()

        # Patch Atmosphere
        patcher5 = patch(
            "ceasiompy.DynamicStability.func.cpacs2sdsa.Atmosphere",
            return_value=MagicMock(density=[1.225], grav_accel=[9.81])
        )
        self.addCleanup(patcher5.stop)
        self.mock_atmosphere = patcher5.start()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.wkdir = Path(self.temp_dir.name)
        self.sdsa = SDSAFile(self.mock_cpacs, self.wkdir)

    @patch.object(SDSAFile, "update")
    @patch.object(SDSAFile, "update_attribute")
    @patch(
        "ceasiompy.DynamicStability.func.cpacs2sdsa.get_alpha_max",
        return_value={"alpha_max": [10, 15]}
    )
    @patch("ceasiompy.DynamicStability.func.cpacs2sdsa.sdsa_format", return_value="formatted")
    def test_update_alpha_max(
        self, mock_sdsa_format, mock_get_alpha_max, mock_update_attr, mock_update
    ):
        self.sdsa.mach_list = [0.5, 0.7]
        self.sdsa.len_mach_list = 2
        self.sdsa.update_alpha_max()
        self.assertTrue(mock_update.called)
        self.assertTrue(mock_update_attr.called)

    @patch.object(SDSAFile, "update")
    @patch.object(SDSAFile, "update_attribute")
    @patch(
        "ceasiompy.DynamicStability.func.cpacs2sdsa.get_tables_values",
        return_value=(
            MagicMock(columns=["A", "B"], __len__=lambda _: 2),
            MagicMock(columns=["C", "D"], __len__=lambda _: 2))
    )
    @patch("ceasiompy.DynamicStability.func.cpacs2sdsa.sdsa_format", return_value="formatted")
    def test_update_tables(
        self, mock_sdsa_format, mock_get_tables_values, mock_update_attr, mock_update
    ):
        self.sdsa.update_tables()
        self.assertTrue(mock_update.called)
        self.assertTrue(mock_update_attr.called)

    @patch.object(SDSAFile, "update")
    @patch.object(SDSAFile, "update_attribute")
    @patch(
        "ceasiompy.DynamicStability.func.cpacs2sdsa.compute_dot_derivatives",
        return_value={"col": np.array([1, 2])}
    )
    @patch("ceasiompy.DynamicStability.func.cpacs2sdsa.sdsa_format", return_value="formatted")
    def test_update_dot_derivatives(
        self, mock_sdsa_format, mock_compute_dot, mock_update_attr, mock_update
    ):
        self.sdsa.software_data = AVL_SOFTWARE
        self.sdsa.xpaths_prim = [("/xpath", "col")]
        self.sdsa.mach_list = [0.5, 0.7]
        self.sdsa.len_mach_list = 2
        self.sdsa.update_dot_derivatives()
        self.assertTrue(mock_update.called)
        self.assertTrue(mock_update_attr.called)

    @patch.object(SDSAFile, "update")
    def test_update_delcoeff(self, mock_update):
        self.sdsa.update_delcoeff()
        self.assertEqual(mock_update.call_count, 4)

    @patch.object(SDSAFile, "update")
    @patch.object(SDSAFile, "update_attribute")
    @patch.object(SDSAFile, "update_alpha_max")
    @patch.object(SDSAFile, "update_tables")
    @patch.object(SDSAFile, "update_dot_derivatives")
    @patch.object(SDSAFile, "update_delcoeff")
    @patch.object(SDSAFile, "update_ref")
    @patch.object(SDSAFile, "update_piloteye")
    def test_generate_xml(
        self,
        mock_update_piloteye, mock_update_ref, mock_update_delcoeff,
        mock_update_dot, mock_update_tables, mock_update_alpha,
        mock_update_attr, mock_update
    ):
        self.sdsa.sdsa_file.save = MagicMock()
        self.sdsa.cgrid = "test"
        path = self.sdsa.generate_xml()
        self.assertTrue(self.sdsa.sdsa_file.save.called)
        self.assertEqual(path, str(self.sdsa.sdsa_path))


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
