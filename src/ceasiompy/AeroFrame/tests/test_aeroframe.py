"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions ModuleTemplate module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.AeroFrame.func.utils import second_moments_of_area

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# =================================================================================================
#   CLASSES
# =================================================================================================

class TestAeroFrame(CeasiompyTest):

    @log_test
    def test_second_moments_of_area_square(self) -> None:
        # Square with vertices (0,0), (1,0), (1,1), (0,1)
        x = [0.0, 1.0, 1.0, 0.0]
        y = [0.0, 0.0, 1.0, 1.0]
        ix, iy = second_moments_of_area(x, y)
        # For a unit square centered at (0.5, 0.5), Ix = Iy = 1/12
        self.assertAlmostEqual(ix, 1/12, places=6)
        self.assertAlmostEqual(iy, 1/12, places=6)

    @log_test
    def test_second_moments_of_area_triangle(self) -> None:
        # Triangle with vertices (0,0), (1,0), (0,1)
        x = [0.0, 1.0, 0.0]
        y = [0.0, 0.0, 1.0]
        ix, iy = second_moments_of_area(x, y)
        # For a right triangle with base and height 1, centered at (1/3, 1/3)
        # Ix = Iy = 1/36
        self.assertAlmostEqual(ix, 1/36, places=6)
        self.assertAlmostEqual(iy, 1/36, places=6)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
