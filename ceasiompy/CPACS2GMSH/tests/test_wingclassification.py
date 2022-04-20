"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ModuleTemplate/moduletemplate.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2019-04-19

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import sys
import pytest
from pytest import approx

from cpacspy.cpacspy import CPACS
from ceasiompy.CPACS2GMSH.func.wingclassification import (
    classify_profile,
    classify_trunc_profile,
    classify_wing_section,
    classify_special_section,
    classify_wing,
)
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import AircraftPart, generate_gmsh


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


def test_classify_profile():
    """
    Test if the profiles is correctly classified
    Test if uncorrect profile is not classified
    """

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    _, aircraft_parts = generate_gmsh(
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        mesh_size_farfield=2,
        mesh_size_fuselage=0.2,
        mesh_size_wings=0.2,
        symmetry=False,
    )
    # Erease generated file
    for file in os.listdir(TEST_OUT_PATH):
        if (".brep" in file) or (".su2" in file):
            os.remove(os.path.join(TEST_OUT_PATH, file))

    aircraft_parts
    profile_list = []
    line_comp1 = {"line_dimtag": 5, "points_tags": [8, 5]}
    line_comp2 = {"line_dimtag": 14, "points_tags": [5, 8]}
    line_comp3 = {"line_dimtag": 14, "points_tags": [8, 3]}
    # Correct profile
    assert classify_profile(profile_list, line_comp1, line_comp2) is True
    # Uncorrect profile
    assert classify_profile(profile_list, line_comp1, line_comp3) is False


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
