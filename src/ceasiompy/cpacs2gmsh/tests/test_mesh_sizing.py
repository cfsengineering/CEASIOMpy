"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/mesh_sizing.py'
"""

# Futures

from __future__ import annotations

# Imports

from ceasiompy.cpacs2gmsh.utility.mesh_sizing import (
    get_wing_ref_chord,
    get_fuselage_mean_circumference,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# Classes
class TestMeshSizing(CeasiompyTest):

    def test_fuselage_size(self: CeasiompyTest) -> None:
        """
        This test takes the fuselage dimension on which the mesh size is calculated.
        """
        self.assert_equal_function(
            f=get_fuselage_mean_circumference,
            input_args=(self.test_cpacs.tixi, ),
            expected=(17.441775789525824, ),
        )

    def test_wing_size(self: CeasiompyTest) -> None:
        """
        This test takes the fuselage dimension on which the mesh size is calculated.
        """
        self.assert_equal_function(
            f=get_wing_ref_chord,
            input_args=(self.test_cpacs.tixi, ),
            expected=(3.71464, ),
        )


# Main
if __name__ == "__main__":
    main(verbosity=0)
