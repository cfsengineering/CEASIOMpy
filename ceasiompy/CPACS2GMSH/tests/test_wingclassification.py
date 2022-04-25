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
import gmsh
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


def test_classify_profile():
    """
    Test if a simple 2 bspline profile is correctly classified
    """

    gmsh.initialize()

    le_point_tag = gmsh.model.occ.addPoint(0, 0, 0, 1)
    te_point_tag = gmsh.model.occ.addPoint(1, 0, 0, 1)
    up_profile_point_tag = gmsh.model.occ.addPoint(0.2, 0.1, 0, 1)
    lo_profile_point_tag = gmsh.model.occ.addPoint(0.2, -0.1, 0, 1)

    gmsh.model.occ.synchronize()
    up_bspline = gmsh.model.occ.addBSpline([le_point_tag, up_profile_point_tag, te_point_tag])
    lo_bspline = gmsh.model.occ.addBSpline([te_point_tag, lo_profile_point_tag, le_point_tag])
    bad_bspline = gmsh.model.occ.addBSpline([le_point_tag, lo_profile_point_tag])
    gmsh.model.occ.synchronize()

    # try to classify this profile
    profiles = []
    line_comp_up = {"line_dimtag": up_bspline, "points_tags": [le_point_tag, te_point_tag]}
    line_comp_lo = {"line_dimtag": lo_bspline, "points_tags": [te_point_tag, le_point_tag]}
    bad_line_comp = {
        "line_dimtag": bad_bspline,
        "points_tags": [le_point_tag, lo_profile_point_tag],
    }
    # Test if the profile is correctly classified
    profile_found = classify_profile(profiles, line_comp_up, line_comp_lo)
    assert profile_found == True

    # Test if two line that doesn't form a profile are not classified
    profile_found = classify_profile(profiles, line_comp_up, bad_line_comp)
    assert profile_found == False
    gmsh.clear()
    gmsh.finalize()


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
        refine_factor=1.2,
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
    test_profile_1_sec1 = [22, 24, 26]
    assert profile_1_sec1 == test_profile_1_sec1

    profile_2_sec1 = wing_sec1["profiles"][1]
    test_profile_2_sec1 = [10, 11, 12]
    assert profile_2_sec1 == test_profile_2_sec1

    le_line_sec1 = wing_sec1["le_line"]
    test_le_line_sec1 = [23]
    assert le_line_sec1 == test_le_line_sec1

    te_line_sec1 = wing_sec1["te_line"]
    test_te_line_sec1 = [25, 21]
    assert te_line_sec1 == test_te_line_sec1

    # Erase generated file
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
