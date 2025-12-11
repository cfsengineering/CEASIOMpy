"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/ceasiompyutils.py'

| Author : Aidan Jungo
| Creation: 2022-02-10

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import shutil
import pytest
import tempfile
import numpy as np
import pandas as pd

from cpacspy.cpacsfunctions import open_tixi
from ceasiompy.utils.ceasiompyutils import (
    aircraft_name,
    write_inouts,
    change_working_dir,
    get_aeromap_list_from_xpath,
    get_install_path,
    get_part_type,
    get_results_directory,
    remove_file_type_in_dir,
    run_software,
    check_version,
    get_version,
)

from pathlib import Path
from unittest import main
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from unittest.mock import patch
from ceasiompy import UTILS_PATH
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestCeasiompyUtils(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TMP_DIR = Path(UTILS_PATH, "tests", "tests_ceasiompyutils", "tmp")
        cls.LOGFILE = Path(cls.TMP_DIR, "logfile_python.log")

    def test_check_version_true(self):
        """Test check_version returns True when version is sufficient."""
        with patch("ceasiompy.utils.ceasiompyutils.get_version", return_value="3.2.1"):
            result, version = check_version("python", "3.1.0")
            assert result is True
            assert version == "3.2.1"

    def test_check_version_false(self):
        """Test check_version returns False when version is insufficient."""
        with patch("ceasiompy.utils.ceasiompyutils.get_version", return_value="2.7.15"):
            result, version = check_version("python", "3.0.0")
            assert result is False
            assert version == "2.7.15"

    def test_check_version_none(self):
        """Test check_version returns False and empty string if version is None."""
        with patch("ceasiompy.utils.ceasiompyutils.get_version", return_value=None):
            result, version = check_version("python", "3.0.0")
            assert result is False
            assert version == ""

    def test_get_version_found(self):
        """Test get_version returns version string if found in path."""
        with patch("ceasiompy.utils.ceasiompyutils.get_install_path") as mock_get_install_path:
            mock_path = Path("/usr/bin/python3.8.10")
            mock_get_install_path.return_value = mock_path
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version("python")
                assert version == "3.8.10"

    def test_get_version_not_found(self):
        """Test get_version returns empty string if version not found in path."""
        with patch("ceasiompy.utils.ceasiompyutils.get_install_path") as mock_get_install_path:
            mock_path = Path("/usr/bin/python")
            mock_get_install_path.return_value = mock_path
            with patch("pathlib.Path.exists", return_value=True):
                with patch("ceasiompy.utils.ceasiompyutils.log.warning") as mock_warn:
                    version = get_version("python")
                    assert version == ""
                    mock_warn.assert_called_once()

    def test_get_version_file_missing(self):
        """Test get_version returns empty string if install path does not exist."""
        with patch("ceasiompy.utils.ceasiompyutils.get_install_path") as mock_get_install_path:
            fake_path = Path("/not/exist/python3.8.10")
            mock_get_install_path.return_value = fake_path
            with patch("pathlib.Path.exists", return_value=False):
                with patch("ceasiompy.utils.ceasiompyutils.log.warning") as mock_warn:
                    version = get_version("python")
                    assert version == ""
                    mock_warn.assert_called_once()

    def test_write_inouts_setcmd(self):
        """Test write_inouts writes values using setcmd."""
        tixi = MagicMock()
        df = pd.DataFrame(
            {
                "setcmd": ["/cpacs/path/to/value1"],
                "getcmd": ["-"],
            },
            index=["var1"],
        )
        inout = np.array([[42.0]])
        with patch("ceasiompy.utils.ceasiompyutils.create_branch") as mock_create_branch:
            write_inouts(tixi, df, inout)
            mock_create_branch.assert_called_once_with(tixi, "/cpacs/path/to/value1")
            tixi.updateDoubleElement.assert_called_once_with("/cpacs/path/to/value1", 42.0, "%g")

    def test_write_inouts_getcmd(self):
        """Test write_inouts writes values using getcmd if setcmd is '-'."""
        tixi = MagicMock()
        df = pd.DataFrame(
            {
                "setcmd": ["-"],
                "getcmd": ["/cpacs/path/to/value2"],
            },
            index=["var2"],
        )
        inout = np.array([[3.14]])
        with patch("ceasiompy.utils.ceasiompyutils.create_branch") as mock_create_branch:
            write_inouts(tixi, df, inout)
            mock_create_branch.assert_called_once_with(tixi, "/cpacs/path/to/value2")
            tixi.updateDoubleElement.assert_called_once_with("/cpacs/path/to/value2", 3.14, "%g")

    def test_write_inouts_skip_if_both_dash(self):
        """Test write_inouts does nothing if both setcmd and getcmd are '-'."""
        tixi = MagicMock()
        df = pd.DataFrame(
            {
                "setcmd": ["-"],
                "getcmd": ["-"],
            },
            index=["var3"],
        )
        inout = np.array([[7.77]])
        with patch("ceasiompy.utils.ceasiompyutils.create_branch") as mock_create_branch:
            write_inouts(tixi, df, inout)
            mock_create_branch.assert_not_called()
            tixi.updateDoubleElement.assert_not_called()

    def test_change_working_dir(self):
        """Test the function (context manager) change_working_dir."""

        default_cwd = Path.cwd()

        os.chdir(str(UTILS_PATH))

        with change_working_dir(self.TMP_DIR):
            assert Path.cwd() == self.TMP_DIR

        assert Path.cwd() == UTILS_PATH

        os.chdir(str(default_cwd))

    def test_get_aeromap_list_from_xpath(self):

        not_define_xpath = "/cpacs/toolspecific/CEASIOMpy/newListOfAeromap"
        aeromap_list = get_aeromap_list_from_xpath(self.test_cpacs, not_define_xpath)
        assert aeromap_list == ["aeromap_empty", "test_apm"]

        not_define_xpath_2 = "/cpacs/toolspecific/CEASIOMpy/newListOfAeromap2"
        aeromap_list = get_aeromap_list_from_xpath(
            self.test_cpacs, not_define_xpath_2, empty_if_not_found=True)
        assert aeromap_list == []

        self.test_cpacs.tixi.updateTextElement(not_define_xpath, "test_apm")
        aeromap_list = get_aeromap_list_from_xpath(self.test_cpacs, not_define_xpath)
        assert aeromap_list == ["test_apm"]

    def test_get_results_directory(self):

        with change_working_dir(self.TMP_DIR):
            test_module_1 = "ExportCSV"
            results_dir = get_results_directory(test_module_1)
            assert results_dir == Path(Path.cwd(), "Results", test_module_1)

            test_module_2 = "PyAVL"
            results_dir = get_results_directory(test_module_2)
            assert results_dir == Path(Path.cwd(), "Results", test_module_2)

            if results_dir.parent.exists():
                shutil.rmtree(results_dir.parent)

        with pytest.raises(ValueError):
            results_dir = get_results_directory("NotExistingModule")

    @pytest.mark.skip(reason="Not implemented yet")
    def test_run_module(self):
        """Test the function run_module."""

        # TODO: how to test this function?

    def test_get_install_path(self):
        """Test the function 'get_install_path'."""

        assert isinstance(get_install_path("python"), Path)

        assert get_install_path("NotExistingSoftware") is None

        # with pytest.raises(SoftwareNotInstalled):
        #    get_install_path("NotExistingSoftware", raise_error=True)

    def test_run_software(self):
        """Test the function 'run_software'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_software("python", ["-c", "print('Hello World!')"], Path(tmpdir))
            logfile = Path(tmpdir) / "logfile_python.log"
            assert logfile.exists()
            with open(logfile, "r") as f:
                assert "Hello World!" in f.read()

    def test_aircraft_name(self):
        """Test the function aircraft_name."""

        # Get name form the CPACS file path
        assert aircraft_name(self.test_cpacs.tixi) == "D150"

        # Get name form TIXI handle
        tixi = open_tixi(self.test_cpacs.cpacs_file)
        assert aircraft_name(tixi) == "D150"

    def test_get_part_type(self):
        """Test the function get_part_type on the D150"""

        cpacs_in = Path(CPACS_FILES_PATH, "simple_engine.xml")
        cpacs = CPACS(cpacs_in)
        tixi = cpacs.tixi

        assert get_part_type(tixi, "Wing") == "wing"
        assert get_part_type(tixi, "Wing_mirrored") == "wing"
        assert get_part_type(tixi, "SimpleFuselage") == "fuselage"
        assert get_part_type(tixi, "SimpleEngine") == "engine"
        assert get_part_type(tixi, "SimpleEngine_mirrored") == "engine"
        assert get_part_type(tixi, "Pylon") == "pylon"
        assert get_part_type(tixi, "Pylon_mirrored") == "pylon"

    def test_remove_file_type_in_dir(self):
        """Test the function 'remove_file_type_in_dir'"""

        with pytest.raises(FileNotFoundError):
            remove_file_type_in_dir(Path("ThisDirectoryDoesNotExist"), ".txt")

        test_file_1 = Path(self.TMP_DIR, "test_file.txt")
        test_file_1.touch()

        test_file_2 = Path(self.TMP_DIR, "test_file.brep")
        test_file_2.touch()

        # Create the logfile before calling the function
        self.LOGFILE.touch()

        remove_file_type_in_dir(self.TMP_DIR, [".txt", ".brep"])

        assert not test_file_1.exists()
        assert not test_file_2.exists()
        assert self.LOGFILE.exists()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
