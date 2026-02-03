"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/mesh_sizing.py'
"""

# Futures

from __future__ import annotations

# Imports

from ceasiompy.CPACS2GMSH.func.mesh_sizing import (
    wings_size,
    fuselage_size,
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
            f=fuselage_size,
            input_args=(self.test_cpacs.tixi, ),
            expected=(1.3953420631620659, 5e-05),
        )

    def test_wing_size(self: CeasiompyTest) -> None:
        """
        This test takes the fuselage dimension on which the mesh size is calculated.
        """
        self.assert_equal_function(
            f=wings_size,
            input_args=(self.test_cpacs.tixi, ),
            expected=(0.5571959999999999, 0.04457567999999999),
        )


# Main
if __name__ == "__main__":
    main(verbosity=0)
