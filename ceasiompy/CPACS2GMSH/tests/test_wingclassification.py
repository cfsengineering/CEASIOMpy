"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/wingclassification.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2022-04-19

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import shutil
import sys
from pathlib import Path

import gmsh
import pytest
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.CPACS2GMSH.func.wingclassification import (
    detect_normal_profile,
    detect_truncated_profile,
)
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


@pytest.mark.skipif(
    sys.platform == "darwin", reason="'synchronize' function causes segmentation fault on macOS"
)
def test_detect_normal_profile():
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

    # create curve loop for generating the surfaces
    up_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_2, te_line, up_bspline_1, le_line])
    lo_curveloop = gmsh.model.occ.addCurveLoop([lo_bspline_2, te_line, lo_bspline_1, le_line])
    profile1_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_1, lo_bspline_1])
    profile2_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_2, lo_bspline_2])
    gmsh.model.occ.synchronize()

    # Generate surfaces
    gmsh.model.occ.addSurfaceFilling(up_curveloop)
    gmsh.model.occ.addSurfaceFilling(lo_curveloop)
    gmsh.model.occ.addSurfaceFilling(profile1_curveloop)
    gmsh.model.occ.addSurfaceFilling(profile2_curveloop)
    gmsh.model.occ.synchronize()

    profile_lines = [up_bspline_1, lo_bspline_1, up_bspline_2, lo_bspline_2, le_line, te_line]
    lines_composition = []
    for line in profile_lines:
        adj_surfs, _ = gmsh.model.getAdjacencies(1, line)
        lines_composition.append({"line_tag": line, "surf_tags": set(adj_surfs)})

    # Find the pair of le/te lines with all the lines of the wing part
    le_te_pair = []

    for index, line_comp1 in enumerate(lines_composition):
        for line_comp2 in lines_composition[index:]:
            # try to detect if two line form a normal profile
            le_te_pair, _ = detect_normal_profile(le_te_pair, line_comp1, line_comp2)

    # test if only one te_le_pair is detected in the profile

    assert len(le_te_pair) == 1
    # test if the correct le_te_pair is detected
    assert sorted(le_te_pair[0]) == sorted([le_line, te_line])
    gmsh.clear()
    gmsh.finalize()


@pytest.mark.skipif(
    sys.platform == "darwin", reason="'synchronize' function causes segmentation fault on macOS"
)
def test_detect_truncated_profile():
    """
    Test if a simple 2 bspline truncated profile wing section is correctly classified

    This test create two profile in gmsh and link them with a leading edge line and
    and two trailing edge line.
    Then we check if it is correctly classified
    """
    gmsh.initialize()
    # profile1
    le_pt_1 = gmsh.model.occ.addPoint(0, 0, 0, 1)
    te_pt1_1 = gmsh.model.occ.addPoint(1, 0.01, 0, 1)
    te_pt2_1 = gmsh.model.occ.addPoint(1, -0.01, 0, 1)

    up_pr_pt_1 = gmsh.model.occ.addPoint(0.2, 0.1, 0, 1)
    lo_pr_pt_1 = gmsh.model.occ.addPoint(0.2, -0.1, 0, 1)
    gmsh.model.occ.synchronize()
    up_bspline_1 = gmsh.model.occ.addBSpline([le_pt_1, up_pr_pt_1, te_pt1_1])
    lo_bspline_1 = gmsh.model.occ.addBSpline([te_pt2_1, lo_pr_pt_1, le_pt_1])
    trunc_line_1 = gmsh.model.occ.addBSpline([te_pt1_1, te_pt2_1])

    # profile2
    le_pt_2 = gmsh.model.occ.addPoint(0, 0, 1, 1)
    te_pt1_2 = gmsh.model.occ.addPoint(1, 0.01, 1, 1)
    te_pt2_2 = gmsh.model.occ.addPoint(1, -0.01, 1, 1)

    up_pr_pt_2 = gmsh.model.occ.addPoint(0.2, 0.1, 1, 1)
    lo_pr_pt_2 = gmsh.model.occ.addPoint(0.2, -0.1, 1, 1)
    gmsh.model.occ.synchronize()
    up_bspline_2 = gmsh.model.occ.addBSpline([le_pt_2, up_pr_pt_2, te_pt1_2])
    lo_bspline_2 = gmsh.model.occ.addBSpline([te_pt2_2, lo_pr_pt_2, le_pt_2])
    trunc_line_2 = gmsh.model.occ.addBSpline([te_pt1_2, te_pt2_2])
    gmsh.model.occ.synchronize()

    # le/te line
    le_line = gmsh.model.occ.addLine(le_pt_1, le_pt_2)
    te_line_up = gmsh.model.occ.addLine(te_pt1_1, te_pt1_2)
    te_line_lo = gmsh.model.occ.addLine(te_pt2_1, te_pt2_2)
    gmsh.model.occ.synchronize()

    # create curve loop for generating the surfaces
    up_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_2, te_line_up, up_bspline_1, le_line])
    lo_curveloop = gmsh.model.occ.addCurveLoop([lo_bspline_2, te_line_lo, lo_bspline_1, le_line])
    trunc_curveloop = gmsh.model.occ.addCurveLoop(
        [trunc_line_1, te_line_lo, trunc_line_2, te_line_up]
    )
    profile1_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_1, trunc_line_1, lo_bspline_1])
    profile2_curveloop = gmsh.model.occ.addCurveLoop([up_bspline_2, trunc_line_2, lo_bspline_2])
    gmsh.model.occ.synchronize()

    # Generate surfaces
    _ = gmsh.model.occ.addSurfaceFilling(up_curveloop)
    _ = gmsh.model.occ.addSurfaceFilling(lo_curveloop)
    _ = gmsh.model.occ.addSurfaceFilling(trunc_curveloop)
    _ = gmsh.model.occ.addSurfaceFilling(profile1_curveloop)
    _ = gmsh.model.occ.addSurfaceFilling(profile2_curveloop)
    gmsh.model.occ.synchronize()

    profile_lines = [
        up_bspline_1,
        lo_bspline_1,
        up_bspline_2,
        lo_bspline_2,
        le_line,
        te_line_up,
        te_line_lo,
    ]
    lines_composition = []
    for line in profile_lines:
        adj_surfs, _ = gmsh.model.getAdjacencies(1, line)
        lines_composition.append({"line_tag": line, "surf_tags": set(adj_surfs)})

    # Find the pair of le/te lines with all the lines of the wing part
    le_te_pair = []

    for index, line_comp1 in enumerate(lines_composition):
        for line_comp2 in lines_composition[index:]:
            # try to detect if two line form a normal profile
            le_te_pair, found_normal = detect_normal_profile(le_te_pair, line_comp1, line_comp2)
            if not found_normal:
                for line_comp3 in lines_composition:
                    # try to detect if three line form a truncated profile
                    le_te_pair, _ = detect_truncated_profile(
                        le_te_pair, line_comp1, line_comp2, line_comp3
                    )

    # test if only one te_le_pair is detected in the profile
    assert len(le_te_pair) == 1
    # test if the correct le_te_pair is detected
    assert sorted(le_te_pair[0]) == sorted([le_line, te_line_up, te_line_lo])
    gmsh.clear()
    gmsh.finalize()


@pytest.mark.skipif(
    sys.platform == "darwin", reason="'synchronize' function causes segmentation fault on macOS"
)
def test_classify_wing():
    """
    Test if one of the wing of the simple test model is correctly classified

    This test import the whole simple.xml file and check if one of its wing is correctly
    classified
    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_SIMPLE)

    export_brep(cpacs, CPACS_IN_PATH, TEST_OUT_PATH)

    _, aircraft_parts = generate_gmsh(
        CPACS_IN_PATH,
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        refine_factor=1.0,
        check_mesh=False,
        testing_gmsh=False,
    )

    for part in aircraft_parts:
        if "Wing_mirrored" == part.uid:
            test_wingsection = part.wing_sections

    # Test if the wing1_m is correctly classified
    assert len(test_wingsection) == 2

    # Test if the wing1_m section 1 is correctly classified

    section1 = test_wingsection[0]

    assert section1["lines_tags"] == [21, 23, 25]

    assert pytest.approx(section1["mean_chord"], 0.01) == 1

    # Delete files generated by the test
    files_to_delete = [p for p in TEST_OUT_PATH.iterdir() if p.suffix in [".brep", ".su2", ".cfg"]]
    for file in files_to_delete:
        file.unlink()


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
