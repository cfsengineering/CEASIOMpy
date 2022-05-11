"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/wingclassification.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2019-05-09

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import sys
from pathlib import Path

import gmsh
import pytest
from ceasiompy.CPACS2GMSH.func.advancemeshing import distance_field, restrict_fields, min_fields

from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
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
def test_distance_field():
    """
    Test if a simple distance field can be generate for a line and a surface
    """
    gmsh.initialize()
    # square of 4 points
    pt_1 = gmsh.model.occ.addPoint(0, 0, 0, 1)
    pt_2 = gmsh.model.occ.addPoint(1, 0, 0, 1)
    pt_3 = gmsh.model.occ.addPoint(1, 1, 0, 1)
    pt_4 = gmsh.model.occ.addPoint(0, 1, 0, 1)

    gmsh.model.occ.synchronize()
    line_1 = gmsh.model.occ.addLine(pt_1, pt_2)
    line_2 = gmsh.model.occ.addLine(pt_2, pt_3)
    line_3 = gmsh.model.occ.addLine(pt_3, pt_4)
    line_4 = gmsh.model.occ.addLine(pt_4, pt_1)

    # create curve loop for generating the surfaces
    curveloop = gmsh.model.occ.addCurveLoop([line_1, line_2, line_3, line_4])

    gmsh.model.occ.synchronize()

    # Generate surfaces
    surface = gmsh.model.occ.addSurfaceFilling(curveloop)
    gmsh.model.occ.synchronize()

    # Create a distance fields
    mesh_fields = {"nbfields": 0, "restrict_fields": []}

    mesh_fields = distance_field(mesh_fields, 1, [line_1])
    mesh_fields = distance_field(mesh_fields, 1, [line_2])
    mesh_fields = distance_field(mesh_fields, 1, [line_3])
    mesh_fields = distance_field(mesh_fields, 1, [line_4])
    mesh_fields = distance_field(mesh_fields, 2, [surface])

    # Check mesh field are created
    assert mesh_fields["nbfields"] == 5
    # Check mesh field tags are correct
    gmsh_field_list = gmsh.model.mesh.field.list()
    assert all([a == b for a, b in zip(gmsh_field_list, [1, 2, 3, 4, 5])])

    for tag in gmsh_field_list:
        assert gmsh.model.mesh.field.getType(tag) == "Distance"
    gmsh.clear()
    gmsh.finalize()


def test_restrict_fields():
    """
    Test if a simple restrict field can be generate for a surface and a volume
    """
    """
    Test if a simple distance field can be generate for a line and a surface
    """
    gmsh.initialize()
    # create a cube with gmsh

    box = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    # Create a distance fields on the first line of the cube
    mesh_fields = {"nbfields": 0, "restrict_fields": []}

    mesh_fields = distance_field(mesh_fields, 1, [1])

    # create a simple matheval field on the previous distance_field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setString(mesh_fields["nbfields"], "F", "(F1 /2)")
    # Create a restrict field on one of the cube's first surface
    mesh_fields = restrict_fields(mesh_fields, 2, [1])

    # do another matheval field on the distance_field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setString(mesh_fields["nbfields"], "F", "(F1 /4)")
    # Create a restrict field on the cube0s volume
    mesh_fields = restrict_fields(mesh_fields, 3, [box])

    # Check mesh field are created
    assert mesh_fields["nbfields"] == 5

    # Check the restrict field tags are correct
    assert all([a == b for a, b in zip(mesh_fields["restrict_fields"], [3, 5])])

    # Check mesh field tags are correct

    assert gmsh.model.mesh.field.getType(1) == "Distance"
    assert gmsh.model.mesh.field.getType(2) == "MathEval"
    assert gmsh.model.mesh.field.getType(3) == "Restrict"
    assert gmsh.model.mesh.field.getType(4) == "MathEval"
    assert gmsh.model.mesh.field.getType(5) == "Restrict"

    gmsh.clear()
    gmsh.finalize()


def test_min_fields():
    """
    Test if a simple min field can be generate for a restrict field
    """
    gmsh.initialize()
    # create a sphere with gmsh

    gmsh.model.occ.addSphere(0, 0, 0, 1)
    # Create a distance fields on the first line of the sphere
    mesh_fields = {"nbfields": 0, "restrict_fields": []}

    mesh_fields = distance_field(mesh_fields, 1, [1])

    # create a simple matheval field on the previous distance_field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setString(mesh_fields["nbfields"], "F", "(F1 /2)")
    # Create a restrict field on one of the sphere surface
    mesh_fields = restrict_fields(mesh_fields, 2, [1])

    # create the min field
    mesh_fields = min_fields(mesh_fields)

    # Check mesh field are created
    assert mesh_fields["nbfields"] == 4

    # Check mesh field tags are correct

    assert gmsh.model.mesh.field.getType(1) == "Distance"
    assert gmsh.model.mesh.field.getType(2) == "MathEval"
    assert gmsh.model.mesh.field.getType(3) == "Restrict"
    assert gmsh.model.mesh.field.getType(4) == "Min"

    gmsh.clear()
    gmsh.finalize()


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
