"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions ModuleTemplate module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import tempfile
import numpy as np

from ceasiompy.utils.decorators import log_test
from ceasiompy.AeroFrame.func.utils import second_moments_of_area
from ceasiompy.AeroFrame.func.config import interpolate_leading_edge

from pathlib import Path
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
        self.assertAlmostEqual(ix, 1 / 12, places=6)
        self.assertAlmostEqual(iy, 1 / 12, places=6)

    @log_test
    def test_second_moments_of_area_triangle(self) -> None:
        # Triangle with vertices (0,0), (1,0), (0,1)
        x = [0.0, 1.0, 0.0]
        y = [0.0, 0.0, 1.0]
        ix, iy = second_moments_of_area(x, y)
        # For a right triangle with base and height 1, centered at (1/3, 1/3)
        # Ix = Iy = 1/36
        self.assertAlmostEqual(ix, 1 / 36, places=6)
        self.assertAlmostEqual(iy, 1 / 36, places=6)

    @log_test
    def test_interpolate_leading_edge(self) -> None:
        # Create a minimal AVL file with two Xle entries
        avl_content = (
            """
            SURFACE
            Xle
            0.0 0.0 0.0
            Xle
            1.0 1.0 1.0
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            avl_path = Path(tmpdir) / "test.avl"
            with open(avl_path, "w") as f:
                f.write(avl_content)
            wg_origin = [0.0, 0.0, 0.0]
            wg_scaling = [1.0, 1.0, 1.0]
            y_queries = [0.0, 0.5, 1.0]
            n_iter = 1
            # Call the function
            (
                xle_array, yle_array, zle_array,
                interpolated_xle, interpolated_yle, interpolated_zle,
            ) = interpolate_leading_edge(
                avl_path, tmpdir, wg_origin, wg_scaling, y_queries, n_iter
            )
            # Check original arrays
            np.testing.assert_array_almost_equal(xle_array, [0.0, 1.0])
            np.testing.assert_array_almost_equal(yle_array, [0.0, 1.0])
            np.testing.assert_array_almost_equal(zle_array, [0.0, 1.0])
            # Check interpolation at y=0.5 is (0.5, 0.5, 0.5)
            idx = y_queries.index(0.5)
            self.assertAlmostEqual(interpolated_xle[idx], 0.5)
            self.assertAlmostEqual(interpolated_yle[idx], 0.5)
            self.assertAlmostEqual(interpolated_zle[idx], 0.5)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
