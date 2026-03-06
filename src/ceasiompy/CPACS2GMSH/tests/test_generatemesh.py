"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'
"""

# Imports
import gmsh

from ceasiompy.CPACS2GMSH.func.wingclassification import get_entities_from_volume


# Functions

def test_get_entities_from_volume():
    """
    Test on a simple cube if the lower dimensions entities are correctly found.
    """

    gmsh.initialize()
    test_cube = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    surfaces_dimtags, lines_dimtags, points_dimtags = get_entities_from_volume([(3, test_cube)])
    assert len(surfaces_dimtags) == 6
    assert len(lines_dimtags) == 12
    assert len(points_dimtags) == 8
    assert surfaces_dimtags == [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]
    assert lines_dimtags == [(1, i) for i in range(1, 13)]
    assert points_dimtags == [(0, i) for i in range(1, 9)]
    gmsh.clear()
    gmsh.finalize()


# Main
if __name__ == "__main__":
    test_get_entities_from_volume()
