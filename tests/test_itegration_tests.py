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
from ceasiompy.utils.commonpaths import LOGFILE
from src.bin.ceasiompy_exec import run_modules_list

MODULE_DIR = Path(__file__).parent
WORKFLOW_TEST_DIR = Path(MODULE_DIR, "workflow_tests")
CPACS_IN_PATH = Path(MODULE_DIR, "Test_input.xml")
CPACS_IN_2_PATH = Path(MODULE_DIR, "Test_input2.xml")

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
        if "--- End of" in f.readlines()[-1]:
            return True

    return False


@pytest.mark.skipif(not shutil.which("pytornado"), reason="PyTornado not installed")
def test_integration_1():

    modules_to_run = ["WeightConventional", "PyTornado", "SkinFriction", "ExportCSV"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("dwfsumo"), reason="SUMO not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_2():

    modules_to_run = ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run", "ExportCSV"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("dwfsumo"), reason="SUMO not installed")
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

    modules_to_run = ["CPACS2GMSH", "SU2Run", "SaveAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_2_PATH), *modules_to_run])

    assert workflow_ends()


<<<<<<< HEAD
<<<<<<< HEAD
||||||| parent of af67f93 (Replace new module name everywhere)
@pytest.mark.gui
@pytest.mark.skipif(not shutil.which("pytornado"), reason="PyTornado not installed")
def test_integration_5():
    """Integration test for module with GUI, requiring a user interaction"""

    modules_to_run = ["CPACSCreator", "SettingsGUI", "PyTornado", "PlotAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


=======
@pytest.mark.gui
@pytest.mark.skipif(not shutil.which("pytornado"), reason="PyTornado not installed")
def test_integration_5():
    """Integration test for module with GUI, requiring a user interaction"""

    modules_to_run = ["CPACSCreator", "SettingsGUI", "PyTornado", "SaveAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


>>>>>>> af67f93 (Replace new module name everywhere)
||||||| parent of a35ffa9 (Add SaveAeroCoef to the integration test)
@pytest.mark.gui
@pytest.mark.skipif(not shutil.which("pytornado"), reason="PyTornado not installed")
def test_integration_5():
    """Integration test for module with GUI, requiring a user interaction"""

    modules_to_run = ["CPACSCreator", "SettingsGUI", "PyTornado", "SaveAeroCoefficients"]

    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run])

    assert workflow_ends()


=======
>>>>>>> a35ffa9 (Add SaveAeroCoef to the integration test)
# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Integration tests")
    print("To run test use the following command:")
    print('>> pytest -v . --cov=../ceasiompy --cov-report term -m "not gui"')
