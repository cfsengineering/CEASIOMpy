"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.
"""

# ====================================================================================================================
#   IMPORTS
# ====================================================================================================================

import shutil
import pytest
import streamlit as st

from pathlib import Path
from unittest.mock import MagicMock

from bin.ceasiompy_exec import run_modules_list
from ceasiompy.utils.ceasiompyutils import change_working_dir

from ceasiompy.SMUse import MODULE_NAME as SMUSE
from ceasiompy.PyAVL import MODULE_NAME as PYAVL
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN
from ceasiompy.SMTrain import MODULE_NAME as SMTRAIN
from ceasiompy.Database import MODULE_NAME as DATABASE
from ceasiompy.ExportCSV import MODULE_NAME as EXPORTCSV
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH
from ceasiompy.AeroFrame import MODULE_NAME as AEROFRAMENEW
from ceasiompy.SaveAeroCoefficients import MODULE_NAME as SAVEAEROCOEF

# =================================================================================================
#   CONSTANTS
# =================================================================================================

MODULE_DIR = Path(__file__).parent
WORKFLOW_TEST_DIR = Path(MODULE_DIR, "workflow_tests")
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_RANS = Path(CPACS_FILES_PATH, "labARscaled.xml")

# Remove previous workflow directory and create new one
if WORKFLOW_TEST_DIR.exists():
    shutil.rmtree(WORKFLOW_TEST_DIR)

WORKFLOW_TEST_DIR.mkdir()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_workflow_test(modules_to_run, cpacs_path=CPACS_IN_PATH):
    """Run a workflow test with the given modules and optional CPACS path."""
    st.session_state = MagicMock()
    with change_working_dir(WORKFLOW_TEST_DIR):
        run_modules_list([str(cpacs_path), *modules_to_run])

# =================================================================================================
#   TESTS
# =================================================================================================


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_integration_1():
    run_workflow_test([AEROFRAMENEW])
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("gmsh"), reason="GMSH not installed")
@pytest.mark.skipif(not shutil.which("pentagrow"), reason="Pentagrow not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_2():
    run_workflow_test([CPACS2GMSH, SU2RUN, EXPORTCSV], cpacs_path=CPACS_RANS)
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_integration_3():
    run_workflow_test([PYAVL, SAVEAEROCOEF, DATABASE])
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("gmsh"), reason="gmsh not installed")
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_integration_4():
    run_workflow_test([SMTRAIN, SMUSE, SAVEAEROCOEF])
    assert True
