"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/ceasiompyutils.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-02-10

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import shutil
from pathlib import Path

import pytest
from ceasiompy.utils.ceasiompyutils import (
    SoftwareNotInstalled,
    aircraft_name,
    change_working_dir,
    get_install_path,
    get_results_directory,
    get_part_type,
)
from cpacspy.cpacsfunctions import open_tixi

from ceasiompy.utils.paths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_change_working_dir():
    """Test the function (context manager) change_working_dir."""

    default_cwd = Path.cwd()

    os.chdir(str(MODULE_DIR))

    with change_working_dir(Path(MODULE_DIR, "tmp")):
        assert Path.cwd() == Path(MODULE_DIR, "tmp")

    assert Path.cwd() == MODULE_DIR

    os.chdir(str(default_cwd))


def test_get_results_directory():

    with change_working_dir(Path(MODULE_DIR, "tmp")):

        results_dir = get_results_directory("ExportCSV")
        assert results_dir == Path(Path.cwd(), "Results", "Aeromaps")

        results_dir = get_results_directory("CPACS2SUMO")
        assert results_dir == Path(Path.cwd(), "Results", "SUMO")

        # Remove the results directory
        if results_dir.parent.exists():
            shutil.rmtree(results_dir.parent)

    with pytest.raises(ValueError):
        results_dir = get_results_directory("NotExistingModule")


@pytest.mark.skip(reason="Not implemented yet")
def test_run_module():
    """Test the function run_module."""

    # TODO: how to test this function?


def test_get_install_path():
    """Test the function 'get_install_path'."""

    assert isinstance(get_install_path("python"), Path)

    assert get_install_path("NotExistingSoftware") is None

    with pytest.raises(SoftwareNotInstalled):
        get_install_path("NotExistingSoftware", raise_error=True)


def test_aircraft_name():
    """Test the function aircraft_name."""

    # Get name form the CPACS file path
    cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml")
    assert aircraft_name(cpacs_in) == "D150"

    # Get name form TIXI handle
    tixi = open_tixi(str(cpacs_in))
    assert aircraft_name(tixi) == "D150"


def test_get_part_type():
    """Test the function get_part_type on the D150"""

    # CPACS file path
    cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml")

    assert get_part_type(cpacs_in, "Wing1") == "wing"
    assert get_part_type(cpacs_in, "Wing1_mirrored") == "wing"
    assert get_part_type(cpacs_in, "Wing2H") == "wing"
    assert get_part_type(cpacs_in, "Wing2H_mirrored") == "wing"
    assert get_part_type(cpacs_in, "Wing3V") == "wing"
    assert get_part_type(cpacs_in, "Fuselage1") == "fuselage"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
