"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/advancemeshing.py'
"""

# Futures

from __future__ import annotations

# Imports
import gmsh
import pytest

from ceasiompy.cpacs2gmsh.meshing.advancemeshing import (
    min_fields,
    compute_area,
    distance_field,
    restrict_fields,
    compute_angle_surfaces,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CEASIOMpyTest
from ceasiompy.cpacs2gmsh.meshing.advancemeshing import MeshFieldState


# Classes

class TestAdvanceMeshing(CEASIOMpyTest):
    def test_distance_field(self: CEASIOMpyTest) -> None:
        """
        Test if a simple distance field can be generate for a line and a surface
        """

        gmsh.initialize()

        # Create a square with gmsh
        pt_1 = gmsh.model.occ.addPoint(0, 0, 0, 1)
        pt_2 = gmsh.model.occ.addPoint(1, 0, 0, 1)
        pt_3 = gmsh.model.occ.addPoint(1, 1, 0, 1)
        pt_4 = gmsh.model.occ.addPoint(0, 1, 0, 1)

        gmsh.model.occ.synchronize()
        line_1 = gmsh.model.occ.addLine(pt_1, pt_2)
        line_2 = gmsh.model.occ.addLine(pt_2, pt_3)
        line_3 = gmsh.model.occ.addLine(pt_3, pt_4)
        line_4 = gmsh.model.occ.addLine(pt_4, pt_1)

        # Create curve loop for generating the surfaces
        curveloop = gmsh.model.occ.addCurveLoop([line_1, line_2, line_3, line_4])

        gmsh.model.occ.synchronize()

        # Generate surfaces
        surface = gmsh.model.occ.addSurfaceFilling(curveloop)
        gmsh.model.occ.synchronize()

        # Create a distance fields
        mesh_fields = MeshFieldState()
        mesh_fields = distance_field(mesh_fields, 1, [line_1])
        mesh_fields = distance_field(mesh_fields, 1, [line_2])
        mesh_fields = distance_field(mesh_fields, 1, [line_3])
        mesh_fields = distance_field(mesh_fields, 1, [line_4])
        mesh_fields = distance_field(mesh_fields, 2, [surface])

        # Check mesh field are created
        assert mesh_fields.nbfields == 5
        # Check mesh field tags are correct
        gmsh_field_list = gmsh.model.mesh.field.list()
        assert all([a == b for a, b in zip(gmsh_field_list, [1, 2, 3, 4, 5])])

        for tag in gmsh_field_list:
            assert gmsh.model.mesh.field.getType(tag) == "Distance"
        gmsh.clear()
        gmsh.finalize()

    def test_restrict_fields(self: CEASIOMpyTest) -> None:
        """
        Test if a simple restrict field can be generate for a surface and a volume
        """

        gmsh.initialize()

        # Create a cube with gmsh
        box = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)

        # Create a distance fields on the first line of the cube
        mesh_fields = MeshFieldState()
        mesh_fields = distance_field(mesh_fields, 1, [1])

        # Create a simple matheval field on the previous distance_field
        mesh_fields.nbfields += 1
        gmsh.model.mesh.field.add("MathEval", mesh_fields.nbfields)
        gmsh.model.mesh.field.setString(mesh_fields.nbfields, "F", "(F1 /2)")

        # Create a restrict field on one of the cube's first surface
        mesh_fields = restrict_fields(mesh_fields, 2, [1])

        # do another matheval field on the distance_field
        mesh_fields.nbfields += 1
        gmsh.model.mesh.field.add("MathEval", mesh_fields.nbfields)
        gmsh.model.mesh.field.setString(mesh_fields.nbfields, "F", "(F1 /4)")

        # Create a restrict field on the cube0s volume
        mesh_fields = restrict_fields(mesh_fields, 3, [box])

        # Check mesh field are created
        assert mesh_fields.nbfields == 5

        # Check the restrict field tags are correct
        assert all([a == b for a, b in zip(mesh_fields.restrict_fields, [3, 5])])

        # Check mesh field tags are correct
        assert gmsh.model.mesh.field.getType(1) == "Distance"
        assert gmsh.model.mesh.field.getType(2) == "MathEval"
        assert gmsh.model.mesh.field.getType(3) == "Restrict"
        assert gmsh.model.mesh.field.getType(4) == "MathEval"
        assert gmsh.model.mesh.field.getType(5) == "Restrict"

        gmsh.clear()
        gmsh.finalize()

    def test_min_fields(self: CEASIOMpyTest) -> None:
        """
        Test if a simple min field can be generate for a restrict field
        """

        gmsh.initialize()

        # Create a sphere with gmsh
        gmsh.model.occ.addSphere(0, 0, 0, 1)

        # Create a distance fields on the first line of the sphere
        mesh_fields = MeshFieldState()
        mesh_fields = distance_field(mesh_fields, 1, [1])

        # Create a simple matheval field on the previous distance_field
        mesh_fields.nbfields += 1
        gmsh.model.mesh.field.add("MathEval", mesh_fields.nbfields)
        gmsh.model.mesh.field.setString(mesh_fields.nbfields, "F", "(F1 /2)")

        # Create a restrict field on one of the sphere surface
        mesh_fields = restrict_fields(mesh_fields, 2, [1])

        # Create the min field
        min_fields(mesh_fields)

        # Check mesh field are created
        assert mesh_fields.nbfields == 4

        # Check mesh field tags are correct
        assert gmsh.model.mesh.field.getType(1) == "Distance"
        assert gmsh.model.mesh.field.getType(2) == "MathEval"
        assert gmsh.model.mesh.field.getType(3) == "Restrict"
        assert gmsh.model.mesh.field.getType(4) == "Min"

        gmsh.clear()
        gmsh.finalize()

    def test_compute_area(self: CEASIOMpyTest) -> None:
        """
        Test if the area of a surface is correctly computed
        """

        gmsh.initialize()

        # Create a square with gmsh
        square = gmsh.model.occ.addRectangle(0, 0, 0, 1, 1)
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(2)

        # Compute the meshed area
        area = compute_area(square)

        # Check the area is correct
        assert pytest.approx(area, 0.01) == 1

        gmsh.clear()
        gmsh.finalize()

    def test_compute_angle_surfaces(self: CEASIOMpyTest) -> None:
        """
        Test if the function detects correctly angle too narrow
        """
        gmsh.initialize()
        p1 = gmsh.model.occ.addPoint(0, 0, 0, 0.1)
        p2 = gmsh.model.occ.addPoint(0, 1, 0, 0.1)
        p3 = gmsh.model.occ.addPoint(1, 1, 0, 0.1)
        p4 = gmsh.model.occ.addPoint(1, 0, 0, 0.1)
        p5 = gmsh.model.occ.addPoint(2, 0, 2, 0.1)
        p6 = gmsh.model.occ.addPoint(2, 1, 2, 0.1)
        p7 = gmsh.model.occ.addPoint(3, 0, 3.2, 0.1)
        p8 = gmsh.model.occ.addPoint(3, 1, 3.2, 0.1)
        l1, l2 = gmsh.model.occ.addLine(p1, p2), gmsh.model.occ.addLine(p2, p3)
        l3, l4 = gmsh.model.occ.addLine(p3, p4), gmsh.model.occ.addLine(p4, p1)
        l5, l6 = gmsh.model.occ.addLine(p4, p5), gmsh.model.occ.addLine(p5, p6)
        l7, l8 = gmsh.model.occ.addLine(p6, p3), gmsh.model.occ.addLine(p6, p8)
        l9, l0 = gmsh.model.occ.addLine(p8, p7), gmsh.model.occ.addLine(p7, p5)
        cl1 = gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])
        cl2 = gmsh.model.occ.addCurveLoop([-l3, -l7, -l6, -l5])
        cl3 = gmsh.model.occ.addCurveLoop([l6, l8, l9, l0])
        s1 = gmsh.model.occ.addPlaneSurface([cl1])
        s2 = gmsh.model.occ.addPlaneSurface([cl2])
        s3 = gmsh.model.occ.addPlaneSurface([cl3])
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(1)

        tags_coords_params = {-1: "yay"}
        for i in [s1, s2, s3]:
            tags, coord, param = gmsh.model.mesh.getNodes(2, i, True)
            tags_coords_params[i] = {
                'tags': tags,
                'coord': coord,
                'param': param,
            }

        anglefound = compute_angle_surfaces([s1, s2], tags_coords_params, l3)
        assert anglefound
        anglefound = compute_angle_surfaces([s3, s2], tags_coords_params, l5)
        assert not anglefound
        gmsh.finalize()


# Main

if __name__ == "__main__":
    main(verbosity=0)
