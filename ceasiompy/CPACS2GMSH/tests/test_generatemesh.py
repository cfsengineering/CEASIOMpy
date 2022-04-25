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
    """
    This test try to generate a simple mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml

    """

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    generate_gmsh(
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
    )

    with open(os.path.join(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    # assert "NMARK= 4" in content
    assert "MARKER_TAG= wing1" in content
    assert "MARKER_TAG= wing1_m" in content
    assert "MARKER_TAG= fuselage1" in content
    assert "MARKER_TAG= farfield" in content

    # Erase generated file
    for file in os.listdir(TEST_OUT_PATH):
        if (".brep" in file) or (".su2" in file):
            os.remove(os.path.join(TEST_OUT_PATH, file))


def test_generate_gmsh_symm():
    """
    This test try to generate a simple symmetric mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml

    """

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    generate_gmsh(
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        symmetry=True,
    )

    with open(os.path.join(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    # assert "NMARK= 4" in content
    assert "MARKER_TAG= wing1" in content
    assert "MARKER_TAG= fuselage1" in content
    assert "MARKER_TAG= farfield" in content
    assert "MARKER_TAG= symmetry" in content

    # Erase generated file
    for file in os.listdir(TEST_OUT_PATH):
        if (".brep" in file) or (".su2" in file):
            os.remove(os.path.join(TEST_OUT_PATH, file))


def test_symm_part_removed():
    """
    Test if when symmetry is used, symmetry part are removed

    """

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)
    generate_gmsh(
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        symmetry=True,
    )

    with open(os.path.join(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    # symmetric wing should be removed
    assert "MARKER_TAG= wing1_m" not in content

    # Erease generated file
    for file in os.listdir(TEST_OUT_PATH):
        if (".brep" in file) or (".su2" in file):
            os.remove(os.path.join(TEST_OUT_PATH, file))


def test_assignation():
    """
    Test if the assignation mechanism is correct on all parts
    test if the assignation of the entities of wing1 is correct

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
    )
    fuselage1_child = set([(3, 3)])
    wing1_m_child = set([(3, 6)])

    wing1_child = set([(3, 4)])
    wing1_volume_tag = [4]
    wing1_surfaces_tags = [2, 3, 4, 5, 7, 8, 9]
    wing1_lines_tags = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 22, 23, 24]
    wing1_points_tags = [3, 4, 5, 6, 7, 8, 9, 10, 16]

    for part in aircraft_parts:
        if part.name == "wing1_m":
            assert part.childs_dimtag == wing1_m_child
        if part.name == "fuselage1":
            assert part.childs_dimtag == fuselage1_child
        if part.name == "wing1":
            assert part.childs_dimtag == wing1_child
            assert part.volume_tag == wing1_volume_tag
            assert part.surfaces_tags == wing1_surfaces_tags
            assert part.lines_tags == wing1_lines_tags
            assert part.points_tags == wing1_points_tags
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
