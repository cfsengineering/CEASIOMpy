"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/mesh_sizing.py'
"""

# Futures

from __future__ import annotations

# Imports

from pytest import approx
from ceasiompy.CPACS2GMSH.func.mesh_sizing import (
    wings_size,
    fuselage_size,
)

from unittest import main
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# Classes
class TestMeshSizing(CeasiompyTest):
    
    def test_fuselage_size(self: CeasiompyTest) -> None:
        """
        This test takes the fuselage dimension on which the mesh size is calculated.
        """
        fuselage_maxlen, fuselage_minlen = fuselage_size(self.test_cpacs.tixi)
        print(f'{fuselage_maxlen=} {fuselage_minlen=}')
        self.assert_equal_function(
            f=fuselage_size,
            input_args=(self.test_cpacs.tixi, ),
            expected=(0.5, 0.05),
        )

    def test_wing_size(self: CeasiompyTest) -> None:
        """
        This test takes the fuselage dimension on which the mesh size is calculated.
        """

        wing_maxlen, wing_minlen = wings_size(self.test_cpacs.tixi)
        print(f'{wing_maxlen=} {wing_minlen=}')
        assert wing_maxlen == approx(0.15, abs=1e-2)
        assert wing_minlen == approx(0.012, abs=1e-4)


# Main
if __name__ == "__main__":
    main(verbosity=0)
