"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ModuleTemplate/moduletemplate.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2022-03-22

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import pytest

from pytest import approx
from cpacspy.cpacspy import CPACS

from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep


# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
TEST_OUT_PATH = os.path.join(MODULE_DIR, "ToolOutput")


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_export_brep():
    """Test function for 'export_brep'"""

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    file_count = 0
    for file in os.listdir(TEST_OUT_PATH):
        if ".brep" in file:
            file_count += 1

    assert file_count == 3  # simpletest_cpacs.xml containt only 3 parts

    # Erease generated file
    for file in os.listdir(TEST_OUT_PATH):
        if ".brep" in file:
            os.remove(os.path.join(TEST_OUT_PATH, file))


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
