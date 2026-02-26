"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.
"""

# Imports
import shutil
import pytest

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonpaths import (
    CPACS_FILES_PATH,
)

from ceasiompy.to3d import MODULE_NAME as TO3D
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.su2run import MODULE_NAME as SU2RUN
from ceasiompy.smtrain import MODULE_NAME as SMTRAIN
from ceasiompy.aeroframe import MODULE_NAME as AEROFRAME
from ceasiompy.cpacs2gmsh import MODULE_NAME as CPACS2GMSH
from ceasiompy.airfoil2gmsh import MODULE_NAME as AIRFOIL2GMSH


# Methods

def _run_workflow_test(
    modules_to_run: list[str],
    cpacs_path: Path = Path(CPACS_FILES_PATH, "onera_m6.xml"),
) -> None:
    """Run a workflow test with the given modules and optional CPACS path."""
    workflow = Workflow()
    workflow.cpacs_in = cpacs_path
    workflow.modules_list = modules_to_run
    workflow.module_optim = ["NO"] * len(modules_to_run)
    workflow.write_config_file()
    workflow.set_workflow()
    workflow.run_workflow(test=True)


# Tests

@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_aeroframe_workflow() -> None:
    WORKFLOW_1 = [AEROFRAME]
    _run_workflow_test(
        modules_to_run=WORKFLOW_1,
    )
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("pentagrow"), reason="pentagrow not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_cpacs2gmsh_su2run_workflow() -> None:
    WORKFLOW_2 = [CPACS2GMSH, SU2RUN]
    _run_workflow_test(
        modules_to_run=WORKFLOW_2,
    )
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_pyavl_workflow() -> None:
    WORKFLOW_3 = [PYAVL]
    _run_workflow_test(
        modules_to_run=WORKFLOW_3,
    )
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_smtrain_workflow() -> None:
    WORKFLOW_4 = [SMTRAIN]
    _run_workflow_test(
        modules_to_run=WORKFLOW_4,
    )
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_airfoil_workflow() -> None:
    WORKFLOW_5 = [AIRFOIL2GMSH, SU2RUN]
    _run_workflow_test(
        cpacs_path=Path(CPACS_FILES_PATH, "airfoil.xml"),
        modules_to_run=WORKFLOW_5,
    )
    assert True


@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("SU2_CFD"), reason="SU2_CFD not installed")
def test_to3d_workflow() -> None:
    WORKFLOW_6 = [TO3D, CPACS2GMSH, SU2RUN]
    _run_workflow_test(
        cpacs_path=Path(CPACS_FILES_PATH, "airfoil.xml"),
        modules_to_run=WORKFLOW_6,
    )
    assert True


if __name__ == "__main__":
    test_aeroframe_workflow()
    test_cpacs2gmsh_su2run_workflow()
    test_pyavl_workflow()
    test_smtrain_workflow()
    test_airfoil_workflow()
    test_to3d_workflow()
