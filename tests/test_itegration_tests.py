"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2022-05-06

TODO:

    -

"""


# ====================================================================================================================
#   IMPORTS
# ====================================================================================================================

import shutil
from pathlib import Path

import pytest
from ceasiompy.utils.ceasiompyutils import change_working_dir
from ceasiompy.utils.paths import LOGFILE
from src.bin.ceasiompy_exec import run_modules_list

MODULE_DIR = Path(__file__).parent
WORKFLOW_TEST_DIR = Path(MODULE_DIR, "workflow_tests")
CPACS_IN_PATH = Path(MODULE_DIR, "Test_input.xml")

# Remove previous workflow directory and create new one
if WORKFLOW_TEST_DIR.exists():
    shutil.rmtree(WORKFLOW_TEST_DIR)
WORKFLOW_TEST_DIR.mkdir()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def workflow_ends():
    """Check that the workflow ends correctly"""

    with open(LOGFILE, "r") as f:
        if "###  End of the workflow" in f.readlines()[-2]:
            return True

    return False


def test_integration_1():

    modules_to_run = ["PyTornado", "SkinFriction", "ExportCSV"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("sumo"), reason="SUMO not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_2():

    modules_to_run = ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("sumo"), reason="SUMO not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_3():

    modules_to_run = ["CLCalculator", "CPACS2SUMO", "SUMOAutoMesh", "SU2Run"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("gmsh"), reason="GMSH not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_4():

    modules_to_run = ["CPACS2GMSH", "SU2Run"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("pytornado"), reason="PyTornado not installed")
def test_integration_5():
    """Integration test for module with GUI, requiring a user interaction"""

    modules_to_run = ["CPACSCreator", "SettingsGUI", "PyTornado", "PlotAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Integration tests")
    print("To run test use the following command:")
    print('>> pytest -v . --cov=../ceasiompy --cov-report term -m "not gui"')
