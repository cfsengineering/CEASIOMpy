"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SU2Run/func/meshutils.py'

| Author : Aidan Jungo
| Creation: 2021-12-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
import unittest
import tempfile

from pytest import approx
from ceasiompy.SU2Run.func.utils import (
    get_efficiency_and_aoa,
    get_mesh_markers,
    get_su2_aerocoefs,
    get_wetted_area,
    check_one_entry,
    process_config_dir,
    get_aeromap_uid,
    check_control_surface,
    get_su2_cfg_tpl,
    get_surface_pitching_omega,
    get_su2_forces_moments,
)

from pathlib import Path
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from unittest.mock import patch

# =================================================================================================
#   CONSTANTS
# =================================================================================================


MODULE_DIR = Path(__file__).parent
FORCES_BREAKDOWN = Path(MODULE_DIR, "forces_breakdown.dat")
FORCES_BREAKDOWN_NO_VALUE = Path(MODULE_DIR, "forces_breakdown_no_value.dat")
SU2_LOGFILE = Path(MODULE_DIR, "logfile_SU2_CFD.log")
SU2_LOGFILE_NO_WETTED_AREA = Path(MODULE_DIR, "logfile_SU2_CFD_no_wetted_area.log")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_mesh_marker():
    """Test the class 'get_mesh_markers'"""

    NOT_SU2_MESH = Path(MODULE_DIR, "not_su2_mesh.txt")
    SU2_MESH_NO_MARKER = Path(MODULE_DIR, "test_mesh0.su2")
    SU2_MESH_1 = Path(MODULE_DIR, "test_mesh1.su2")

    with pytest.raises(FileNotFoundError):
        get_mesh_markers(Path("This_file_do_not_exist.su2"))

    with pytest.raises(ValueError):
        get_mesh_markers(NOT_SU2_MESH)

    with pytest.raises(ValueError):
        get_mesh_markers(SU2_MESH_NO_MARKER)

    mesh_markers = get_mesh_markers(SU2_MESH_1)
    assert mesh_markers["wall"] == [
        "D150_VAMP_SL1",
        "D150_VAMP_FL1",
        "D150_VAMP_HL1",
        "D150_VAMP_W1",
    ]
    assert mesh_markers["engine_intake"] == ["D150_ENGINE1_In"]
    assert mesh_markers["engine_exhaust"] == ["D150_ENGINE1_Ex"]
    assert mesh_markers["actuator_disk_inlet"] == ["D150_PROPELLER1_AD_Inlet"]
    assert mesh_markers["actuator_disk_outlet"] == ["D150_PROPELLER1_AD_Outlet"]
    assert mesh_markers["farfield"] == ["Farfield"]
    assert mesh_markers["symmetry"] == ["None"]


def test_get_su2_aerocoefs():
    """Test function 'get_su2_aerocoefs'"""

    with pytest.raises(FileNotFoundError):
        get_su2_aerocoefs(Path(MODULE_DIR, "This_file_do_not_exist.dat"))

    results = get_su2_aerocoefs(FORCES_BREAKDOWN)
    correct_results = [0.132688, 0.199127, 0.010327, None, -0.392577, 0.076315, 102.089]
    for r, res in enumerate(results):
        assert res == approx(correct_results[r], rel=1e-4)

    results_no_value = get_su2_aerocoefs(FORCES_BREAKDOWN_NO_VALUE)
    for res in results_no_value:
        assert res is None


def test_get_efficiency_and_aoa():
    """Test function 'get_efficiency_and_aoa'"""

    with pytest.raises(FileNotFoundError):
        get_efficiency_and_aoa(Path(MODULE_DIR, "This_file_do_not_exist.dat"))

    cl_cd, aoa = get_efficiency_and_aoa(FORCES_BREAKDOWN)
    assert cl_cd == approx(0.666351, rel=1e-4)
    assert aoa == approx(0.5, rel=1e-4)

    with pytest.raises(ValueError):
        get_efficiency_and_aoa(FORCES_BREAKDOWN_NO_VALUE)


def test_get_wetted_area():
    """Test function 'get_wetted_area'"""

    with pytest.raises(FileNotFoundError):
        get_wetted_area(Path(MODULE_DIR, "This_file_do_not_exist.log"))

    assert get_wetted_area(SU2_LOGFILE) == approx(702.04, rel=1e-4)
    assert get_wetted_area(SU2_LOGFILE_NO_WETTED_AREA) == 0

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestSU2UtilsExtra(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_check_one_entry_success(self):
        dict_dir = [
            {"mach": 0.3, "alt": 1000, "angle": "none", "dir": Path("dir1")},
            {"mach": 0.3, "alt": 2000, "angle": "none", "dir": Path("dir2")},
        ]
        result = check_one_entry(dict_dir, 0.3, 1000, "none")
        self.assertEqual(result, Path("dir1"))

    def test_check_one_entry_fail_none(self):
        dict_dir = [
            {"mach": 0.3, "alt": 1000, "angle": "none", "dir": Path("dir1")},
            {"mach": 0.3, "alt": 2000, "angle": "none", "dir": Path("dir2")},
        ]
        with self.assertRaises(ValueError):
            check_one_entry(dict_dir, 0.3, 3000, "none")

    def test_check_one_entry_fail_multiple(self):
        dict_dir = [
            {"mach": 0.3, "alt": 1000, "angle": "none", "dir": Path("dir1")},
            {"mach": 0.3, "alt": 1000, "angle": "none", "dir": Path("dir2")},
        ]
        with self.assertRaises(ValueError):
            check_one_entry(dict_dir, 0.3, 1000, "none")

    def test_process_config_dir_none(self):
        dict_dir = []
        config_dir = Path("results_alt1000_mach0.3_aoa0.0_aos0.0")
        process_config_dir(config_dir, dict_dir)
        self.assertEqual(dict_dir[0]["mach"], 0.3)
        self.assertEqual(dict_dir[0]["alt"], 1000)
        self.assertEqual(dict_dir[0]["dir"], config_dir)
        self.assertEqual(dict_dir[0]["angle"], "none")

    def test_process_config_dir_dynstab(self):
        dict_dir = []
        config_dir = Path("results_alt1000_mach0.3_angle5.0_dynstab")
        process_config_dir(config_dir, dict_dir)
        self.assertEqual(dict_dir[0]["mach"], 0.3)
        self.assertEqual(dict_dir[0]["alt"], 1000)
        self.assertEqual(dict_dir[0]["dir"], config_dir)
        self.assertEqual(dict_dir[0]["angle"], "5.0")

    def test_process_config_dir_skip(self):
        dict_dir = []
        config_dir = Path("results_alt1000_mach0.3_othercase")
        process_config_dir(config_dir, dict_dir)
        # Should not append anything
        self.assertEqual(len(dict_dir), 0)

    def test_get_aeromap_uid(self):
        aeromap_uid = get_aeromap_uid(self.test_cpacs.tixi, fixed_cl="YES")
        self.assertEqual(aeromap_uid, "aeroMap_fixedCL_SU2")

    def test_check_control_surface(self):
        ctrlsurf = check_control_surface("testtestailerontesttest")
        self.assertEqual(ctrlsurf, "aileron")
        ctrlsurf = check_control_surface("testtestelevatortesttest")
        self.assertEqual(ctrlsurf, "elevator")
        ctrlsurf = check_control_surface("testtestruddertesttest")
        self.assertEqual(ctrlsurf, "rudder")
        ctrlsurf = check_control_surface("testtesttesttest")
        self.assertEqual(ctrlsurf, "no_deformation")

    def test_get_surface_pitching_omega_alpha(self):
        result = get_surface_pitching_omega("alpha", 2.5)
        self.assertEqual(result, "0.0 2.5 0.0 ")

    def test_get_surface_pitching_omega_beta(self):
        result = get_surface_pitching_omega("beta", 3.14)
        self.assertEqual(result, "0.0 0.0 3.14 ")

    def test_get_surface_pitching_omega_invalid(self):
        with self.assertRaises(ValueError):
            get_surface_pitching_omega("gamma", 1.0)

    def test_get_su2_cfg_tpl(self):
        # Should return the correct path for euler and rans
        path_euler = get_su2_cfg_tpl("euler")
        self.assertTrue(str(path_euler).endswith("cfg_tpl_euler.cfg"))
        path_rans = get_su2_cfg_tpl("rans")
        self.assertTrue(str(path_rans).endswith("cfg_tpl_rans.cfg"))
        # Should warn and still return a path for invalid type
        with patch("ceasiompy.SU2Run.func.utils.log") as mock_log:
            path_invalid = get_su2_cfg_tpl("invalid")
            self.assertTrue(str(path_invalid).endswith("cfg_tpl_invalid.cfg"))
            assert mock_log.warning.called

    def test_get_su2_forces_moments(self):
        # Create a temporary SU2 force file with known content
        content = """
        Total CL:       0.777 |
        Total CD:       0.888 |
        Total CSF:      0.999 |
        Total CL/CD:    0.666351 |
        Total CMy:      0.111 |
        Total CMz:      0.333 |
        Total CFx:      0.123 |
        Total CFy:      0.456 |
        Total CFz:      0.789 |
        """
        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            cl, cs, cd, _, cms, cml = get_su2_forces_moments(tmp_path)
            self.assertAlmostEqual(cl, 0.123)
            self.assertAlmostEqual(cs, 0.456)
            self.assertAlmostEqual(cd, 0.789)
            self.assertAlmostEqual(cms, 0.111)
            self.assertAlmostEqual(cml, 0.333)
        finally:
            tmp_path.unlink()

    def test_get_su2_forces_moments_missing(self):
        # File missing some coefficients
        content = """
        Total CFx:      1.0 |
        Total CFz:      2.0 |
        """
        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            cl, cs, cd, cmd, cms, cml = get_su2_forces_moments(tmp_path)
            self.assertAlmostEqual(cl, 1.0)
            self.assertAlmostEqual(cd, 2.0)
            self.assertIsNone(cs)
            self.assertIsNone(cmd)
            self.assertIsNone(cms)
            self.assertIsNone(cml)
        finally:
            tmp_path.unlink()

    def test_get_su2_forces_moments_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            get_su2_forces_moments(Path("nonexistent_file.dat"))


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main(verbosity=0)
