"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/workflowclasses.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-02-10

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path

import pytest
from ceasiompy.utils.ceasiompyutils import aircraft_name, change_working_dir, get_results_directory
from cpacspy.cpacsfunctions import open_tixi

# =================================================================================================
#   CLASSES
# =================================================================================================


def test_change_working_dir():
    """Test the function (context manager) change_working_dir."""

    with change_working_dir("/tmp"):
        assert os.getcwd() == "/tmp"

    assert os.getcwd() != "/tmp"


def test_get_results_directory():

    results_dir = get_results_directory("ExportCSV")
    assert results_dir == Path(Path.cwd(), "Results", "Aeromaps")

    results_dir = get_results_directory("CPACS2SUMO")
    assert results_dir == Path(Path.cwd(), "Results", "SUMO")

    with pytest.raises(ValueError):
        results_dir = get_results_directory("NotExistingModule")


@pytest.mark.skip(reason="Not implemented yet")
def test_run_module():
    """Test the function run_module."""

    # TODO: how to test this function?


@pytest.mark.skip(reason="Not implemented yet")
def test_get_install_path():
    """Test the function get_install_path."""

    # TODO: how to test this function? (on different OS..)


def test_aircraft_name():
    """Test the function aircraft_name."""

    # Get name form the CPACS file path
    cpacs_in = str(Path(Path(__file__).parents[4], "test_files/CPACSfiles/D150_simple.xml"))
    assert aircraft_name(cpacs_in) == "D150"

    # Get name form TIXI handle
    tixi = open_tixi(cpacs_in)
    assert aircraft_name(tixi) == "D150"


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
