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

from cpacspy.cpacspy import CPACS
from ceasiompy.CPACS2GMSH.func.wingclassification import (
    classify_profile,
    classify_trunc_profile,
    classify_wing_section,
    classify_special_section,
)
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh, ModelPart


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

    This test create a profile in gmsh and check if it is correctly classified
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


def test_classify_trunc_profile():
    """
    Test if a simple 2 bspline truncated profile is correctly classified

    This test create a truncated profile in gmsh and check if it is correctly classified
    """

    gmsh.initialize()

    le_point_tag = gmsh.model.occ.addPoint(0, 0, 0, 1)
    up_te_point_tag = gmsh.model.occ.addPoint(1, 0, 0.01, 1)
    lo_te_point_tag = gmsh.model.occ.addPoint(1, 0, -0.01, 1)
    up_profile_point_tag = gmsh.model.occ.addPoint(0.2, 0.1, 0, 1)
    lo_profile_point_tag = gmsh.model.occ.addPoint(0.2, -0.1, 0, 1)

    gmsh.model.occ.synchronize()
    up_bspline = gmsh.model.occ.addBSpline([le_point_tag, up_profile_point_tag, up_te_point_tag])
    lo_bspline = gmsh.model.occ.addBSpline([lo_te_point_tag, lo_profile_point_tag, le_point_tag])
    gmsh.model.occ.addBSpline([up_te_point_tag, lo_te_point_tag])
    gmsh.model.occ.synchronize()

    # try to classify this profile
    profile_list = []
    profile_lines = []
    line_comp_up = {"line_dimtag": up_bspline, "points_tags": [le_point_tag, up_te_point_tag]}
    line_comp_lo = {"line_dimtag": lo_bspline, "points_tags": [lo_te_point_tag, le_point_tag]}

    # Test if the profile is correctly classified
    profile_found = classify_trunc_profile(profile_list, profile_lines, line_comp_up, line_comp_lo)
    assert profile_found == True

    # Test if the profile is not two times classified
    profile_found = classify_trunc_profile(profile_list, profile_lines, line_comp_up, line_comp_lo)
    assert profile_found == False
    gmsh.clear()
    gmsh.finalize()


def test_classify_wing_section():
    """
    Test if a simple 2 bspline  profile wing section is correctly classified

    This test create two profile in gmsh and link them with a leading edge line and
    a trailing edge line.
    Then we check if it is correctly classified
    """
    gmsh.initialize()
    # profile1
    le_pt_1 = gmsh.model.occ.addPoint(0, 0, 0, 1)
    te_pt_1 = gmsh.model.occ.addPoint(1, 0, 0, 1)
    up_pr_pt_1 = gmsh.model.occ.addPoint(0.2, 0.1, 0, 1)
    lo_pr_pt_1 = gmsh.model.occ.addPoint(0.2, -0.1, 0, 1)
    gmsh.model.occ.synchronize()
    up_bspline_1 = gmsh.model.occ.addBSpline([le_pt_1, up_pr_pt_1, te_pt_1])
    lo_bspline_1 = gmsh.model.occ.addBSpline([te_pt_1, lo_pr_pt_1, le_pt_1])

    # profile2
    le_pt_2 = gmsh.model.occ.addPoint(0, 0, 1, 1)
    te_pt_2 = gmsh.model.occ.addPoint(1, 0, 1, 1)
    up_pr_pt_2 = gmsh.model.occ.addPoint(0.2, 0.1, 1, 1)
    lo_pr_pt_2 = gmsh.model.occ.addPoint(0.2, -0.1, 1, 1)
    gmsh.model.occ.synchronize()
    up_bspline_2 = gmsh.model.occ.addBSpline([le_pt_2, up_pr_pt_2, te_pt_2])
    lo_bspline_2 = gmsh.model.occ.addBSpline([te_pt_2, lo_pr_pt_2, le_pt_2])

    # le/te line
    le_line = gmsh.model.occ.addLine(le_pt_1, le_pt_2)
    te_line = gmsh.model.occ.addLine(te_pt_1, te_pt_2)
    gmsh.model.occ.synchronize()
    profiles = [
        {
            "truncated": False,
            "lines_dimtag": [up_bspline_1, lo_bspline_1],
            "points_tag": [le_pt_1, te_pt_1],
            "adj_le_lines": [up_bspline_1, lo_bspline_1, le_line],
            "adj_te_lines": [up_bspline_1, lo_bspline_1, te_line],
            "chord_length": 1.0,
        },
        {
            "truncated": False,
            "lines_dimtag": [up_bspline_2, lo_bspline_2],
            "points_tag": [le_pt_2, te_pt_2],
            "adj_le_lines": [up_pr_pt_2, lo_bspline_2, le_line],
            "adj_te_lines": [up_pr_pt_2, lo_bspline_2, te_line],
            "chord_length": 1.0,
        },
    ]
    wing_sections = []
    # Test if the profile is correctly classified
    assert classify_wing_section(wing_sections, profiles[0], profiles[1]) == True
    # Test if the profile is not two times classified
    assert classify_wing_section(wing_sections, profiles[0], profiles[1]) == False
    # Test if wrong profile is not classified
    assert classify_wing_section(wing_sections, profiles[0], profiles[0]) == False

    gmsh.clear()
    gmsh.finalize()


def test_classify_special_section():
    """
    Test if a wing section composed of a bspline profile linked to a fake fuselage is
    correctly classified.

    This test create one profile in gmsh and link it to a non profile shapewith a
    leading edge line and a trailing edge line,check if it is correctly classified
    """
    gmsh.initialize()
    # profile1
    le_pt_1 = gmsh.model.occ.addPoint(0, 0, 0, 1)
    te_pt_1 = gmsh.model.occ.addPoint(1, 0, 0, 1)
    up_pr_pt_1 = gmsh.model.occ.addPoint(0.2, 0.1, 0, 1)
    lo_pr_pt_1 = gmsh.model.occ.addPoint(0.2, -0.1, 0, 1)
    gmsh.model.occ.synchronize()
    up_bspline_1 = gmsh.model.occ.addBSpline([le_pt_1, up_pr_pt_1, te_pt_1])
    lo_bspline_1 = gmsh.model.occ.addBSpline([te_pt_1, lo_pr_pt_1, le_pt_1])

    # square fuselage
    sq_pt1 = gmsh.model.occ.addPoint(0, 0, 1, 1)
    sq_pt2 = gmsh.model.occ.addPoint(0.5, -0.5, 1, 1)
    sq_pt3 = gmsh.model.occ.addPoint(1, 0, 1, 1)
    sq_pt4 = gmsh.model.occ.addPoint(0.5, -0.5, 1, 1)
    gmsh.model.occ.synchronize()
    sq_line1 = gmsh.model.occ.addLine(sq_pt1, sq_pt2)
    sq_line2 = gmsh.model.occ.addLine(sq_pt2, sq_pt3)
    sq_line3 = gmsh.model.occ.addLine(sq_pt3, sq_pt4)
    sq_line4 = gmsh.model.occ.addLine(sq_pt4, sq_pt1)

    # le/te line
    le_line = gmsh.model.occ.addLine(le_pt_1, sq_pt1)
    te_line = gmsh.model.occ.addLine(te_pt_1, sq_pt3)
    gmsh.model.occ.synchronize()
    profiles = [
        {
            "truncated": False,
            "lines_dimtag": [up_bspline_1, lo_bspline_1],
            "points_tag": [le_pt_1, te_pt_1],
            "adj_le_lines": [up_bspline_1, lo_bspline_1, le_line],
            "adj_te_lines": [up_bspline_1, lo_bspline_1, te_line],
            "chord_length": 1.0,
        }
    ]
    wing_sections = []
    wing_part = ModelPart("testwing")
    wing_part.lines_tags = [
        sq_line1,
        sq_line2,
        sq_line3,
        sq_line4,
        up_bspline_1,
        lo_bspline_1,
        te_line,
        le_line,
    ]
    wing_part.points_tags = [le_pt_1, te_pt_1, sq_pt1, sq_pt2, sq_pt3, sq_pt4]
    # Test if the profile is correctly classified
    assert classify_special_section(wing_part, wing_sections, profiles) == True

    gmsh.clear()
    gmsh.finalize()


def test_classify_wing():
    """
    Test if one of the wing of the simple test model is correctly classified

    This test import the whole simple.xml file and check if one of its wing is correctly
    classified
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
    assert nb_wing_section == 2

    # Test if the first wing section is correctly classified

    wing_sec1 = test_wingsection[0]

    truncated = wing_sec1["truncated"]
    assert truncated == True

    profile_1_sec1 = wing_sec1["profiles"][0]
    assert profile_1_sec1 == [22, 24, 26]

    profile_2_sec1 = wing_sec1["profiles"][1]
    assert profile_2_sec1 == [10, 11, 12]

    le_line_sec1 = wing_sec1["le_line"]
    assert le_line_sec1 == [23]

    te_line_sec1 = wing_sec1["te_line"]
    assert te_line_sec1 == [25, 21]

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
