"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/wingclassification.py'

| Author : Tony Govoni
| Creation: 2022-04-19

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import gmsh
from ceasiompy.CPACS2GMSH.func.wingclassification import (
    detect_normal_profile,
    detect_truncated_profile,
)
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
