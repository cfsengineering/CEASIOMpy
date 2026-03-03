"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions ModuleTemplate module.

"""

# Imports

import numpy as np

from ceasiompy.utils.decorators import log_test
from ceasiompy.aeroframe.func.utils import (
    calculate_angle,
    compute_delta_a,
    second_moments_of_area,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestAeroFrame(CeasiompyTest):

    @log_test
    def test_calculate_angle(self):
        # Parallel vectors (angle = 0)
        v1 = np.array([1, 0, 0])
        v2 = np.array([2, 0, 0])
        self.assertAlmostEqual(calculate_angle(v1, v2), 0.0)

        # Perpendicular vectors (angle = 90)
        v1 = np.array([1, 0, 0])
        v2 = np.array([0, 1, 0])
        self.assertAlmostEqual(calculate_angle(v1, v2), 90.0)

        # Opposite vectors (angle = 180)
        v1 = np.array([1, 0, 0])
        v2 = np.array([-1, 0, 0])
        self.assertAlmostEqual(calculate_angle(v1, v2), 180.0)

        # Zero vector (should return 0)
        v1 = np.array([0, 0, 0])
        v2 = np.array([1, 0, 0])
        self.assertAlmostEqual(calculate_angle(v1, v2), 0.0)

    @log_test
    def test_compute_delta_a(self):
        # Example: delta_s = [1,2,3], distance_vector = [1,0,0], omega_s = [0,1,0]
        row = {
            "delta_S_mapped": np.array([1.0, 2.0, 3.0]),
            "distance_vector": np.array([1.0, 0.0, 0.0]),
            "omega_S_mapped": np.array([0.0, 1.0, 0.0]),
        }
        # np.cross([1,0,0], [0,1,0]) = [0,0,1]
        expected = np.array([1.0, 2.0, 4.0])
        result = compute_delta_a(row)
        np.testing.assert_array_almost_equal(result, expected)

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


# Main

if __name__ == "__main__":
    main(verbosity=0)
