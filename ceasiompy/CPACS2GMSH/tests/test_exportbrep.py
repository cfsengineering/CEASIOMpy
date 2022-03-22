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
from pathlib import Path

import pytest
import tigl3.configuration
from ceasiompy.utils.ceasiomlogger import get_logger
from pytest import approx
from tigl3 import tigl3wrapper
from tigl3.import_export_helper import export_shapes
from tixi3 import tixi3wrapper

from ceasiompy.CPACS2GMSH.cpacs2gmsh import exportbrep

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


def test_exportbrep():
    """Test Class 'test_exportbrep'"""
    exportbrep(CPACS_IN_PATH, TEST_OUT_PATH)
    file_count = 0
    for file in os.listdir(TEST_OUT_PATH):
        if ".brep" in file:
            file_count += 1
    # erease generated file
    for file in os.listdir(TEST_OUT_PATH):
        if ".brep" in file:
            os.remove(os.path.join(TEST_OUT_PATH, file))
    assert file_count == 3  # simpletest_cpacs.xml containt only 3 airplane parts


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
