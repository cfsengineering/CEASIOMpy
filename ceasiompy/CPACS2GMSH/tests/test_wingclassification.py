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


def test_classify_wing():
    """
    Test if one of the wing of the simple test model is correctly classified
    """

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    _, aircraft_parts = generate_gmsh(
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        symmetry=False,
        advance_mesh=True,
        refine_factor=1,
    )

    for part in aircraft_parts:
        if "wing1_m" in part.name:
            test_wingsection = part.wing_sections

    # Test if the wing1_m is correctly classified
    nb_wing_section = len(test_wingsection)
    test_nb_section = 2
    assert nb_wing_section == test_nb_section

    # Test if the first wing section is correctly classified

    wing_sec1 = test_wingsection[0]
    truncated = wing_sec1["truncated"]
    test_truncated = True
    assert truncated == test_truncated

    profile_1_sec1 = wing_sec1["profiles"][0]
    test_profile_1_sec1 = [19, 20, 21]
    assert profile_1_sec1 == test_profile_1_sec1

    profile_2_sec1 = wing_sec1["profiles"][1]
    test_profile_2_sec1 = [28, 30, 32]
    assert profile_2_sec1 == test_profile_2_sec1

    le_line_sec1 = wing_sec1["le_line"]
    test_le_line_sec1 = [27]
    assert le_line_sec1 == test_le_line_sec1

    te_line_sec1 = wing_sec1["te_line"]
    test_te_line_sec1 = [29, 31]
    assert te_line_sec1 == test_te_line_sec1
    
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
