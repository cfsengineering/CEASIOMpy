"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2022-05-06

"""

# ====================================================================================================================
#   IMPORTS
# ====================================================================================================================

import shutil
from pathlib import Path
import pytest
from ceasiompy.utils.ceasiompyutils import change_working_dir
from ceasiompy.utils.commonpaths import LOGFILE, CPACS_FILES_PATH
from src.bin.ceasiompy_exec import run_modules_list

MODULE_DIR = Path(__file__).parent
WORKFLOW_TEST_DIR = Path(MODULE_DIR, "workflow_tests")
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")

# Remove previous workflow directory and create new one
if WORKFLOW_TEST_DIR.exists():
    shutil.rmtree(WORKFLOW_TEST_DIR)

WORKFLOW_TEST_DIR.mkdir()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def workflow_ends():
    """Check that the workflow ends correctly"""

    with open(LOGFILE, "r") as f:
        if "--- End of" in f.readlines()[-1]:
            return True

    return False


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("dwfsumo"), reason="SUMO not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_2():
    modules_to_run = ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run", "ExportCSV"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run], test=True)

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("dwfsumo"), reason="SUMO not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_3():
    modules_to_run = ["CLCalculator", "CPACS2SUMO", "SUMOAutoMesh", "SU2Run"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run], test=True)

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("gmsh"), reason="GMSH not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_4():
    modules_to_run = ["CPACS2GMSH", "SU2Run", "SaveAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run], test=True)

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_integration_5():
    modules_to_run = ["PyAVL", "SaveAeroCoefficients", "Database"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run], test=True)

    assert workflow_ends()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    test_integration_5()
    print("Integration tests")
    print("To run test use the following command:")
    print(">> pytest -v . --cov=../ceasiompy --cov-report term")
