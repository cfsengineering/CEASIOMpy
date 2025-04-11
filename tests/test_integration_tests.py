"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.


| Author: Aidan Jungo
| Creation: 2022-05-06

TODO:
    Test allworking modules

"""

# ====================================================================================================================
#   IMPORTS
# ====================================================================================================================

import shutil
import pytest

import streamlit as st

from pathlib import Path
from unittest.mock import MagicMock

from src.bin.ceasiompy_exec import run_modules_list
from ceasiompy.utils.ceasiompyutils import change_working_dir

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

# =================================================================================================
#   CONSTANTS
# =================================================================================================

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


def run_workflow_test(modules_to_run):
    """Run a workflow test with the given modules."""
    st.session_state = MagicMock()
    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(CPACS_IN_PATH), *modules_to_run], test=True)

# =================================================================================================
#   TESTS
# =================================================================================================


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("gmsh"), reason="GMSH not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_1():
    run_workflow_test(["CPACSUpdater", "CPACS2GMSH", "SU2Run"])
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_integration_2():
    run_workflow_test(["PyAVL", "SaveAeroCoefficients", "Database"])
    assert True


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    test_integration_1()
    print("Integration tests")
    print("To run test use the following command:")
    print(">> pytest -v . --cov=../ceasiompy --cov-report term")
