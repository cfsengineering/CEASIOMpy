"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.
"""

# Imports
import shutil
import pytest

from utils import run_workflow_test

from ceasiompy import log
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH


# Tests
@pytest.mark.slow
@pytest.mark.skipif(not shutil.which("avl"), reason="avl not installed")
def test_pyavl_workflow() -> None:

    for cpacs_path in list(CPACS_FILES_PATH.glob(
        pattern="*.xml",
        case_sensitive=True,
    )):
        log.info(f"Starting workflow test on geometry {cpacs_path=}")
        run_workflow_test(
            cpacs_path=cpacs_path,
            modules_to_run=[PYAVL],
        )
        assert True


if __name__ == "__main__":
    test_pyavl_workflow()
