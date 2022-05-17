"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/engineconversion.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2022-05-17

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================


from pathlib import Path
import pytest
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.engineconversion import (
    engine_conversion,
    close_engine,
    reposition_engine,
)
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.paths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent
CPACS_IN_SIMPLE_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_engine.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_1():
    assert 1 == 1


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
