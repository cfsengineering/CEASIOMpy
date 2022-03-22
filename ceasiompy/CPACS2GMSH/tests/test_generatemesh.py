"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ModuleTemplate/moduletemplate.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-08-14

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import sys
import pytest
from pytest import approx

from cpacspy.cpacspy import CPACS
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh


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


def test_generate_gmsh():
    """Test function for 'export_brep'"""

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    generate_gmsh(TEST_OUT_PATH, TEST_OUT_PATH)

    with open(os.path.join(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    assert "NMARK= 2" in content
    assert "MARKER_TAG= airfoil" in content
    assert "MARKER_TAG= farfield" in content

    # Erease generated file
    for file in os.listdir(TEST_OUT_PATH):
        if (".brep" in file) or (".su2" in file):
            os.remove(os.path.join(TEST_OUT_PATH, file))


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
