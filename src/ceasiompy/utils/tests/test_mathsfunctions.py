"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions from 'lib/utils/mathfunctions.py'
"""

# Imports

import numpy as np
from pytest import approx
from ceasiompy.utils.mathsfunctions import (
    rot,
    euler2fix,
    fix2euler,
    rotate_2d_point,
    dimensionalize_rate,
    non_dimensionalize_rate,
)

from unittest import main
from ceasiompy.utils.generalclasses import Point
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# Functions

class TestMathsFunctions(CeasiompyTest):
    def test_rot_identity(self):
        """Test rot returns identity matrix for 0 radians."""
        R = rot(0)
        np.testing.assert_array_almost_equal(R, np.array([[1, 0], [0, 1]]))

    def test_rot_90deg(self):
        """Test rot returns correct matrix for 90 degrees (pi/2 radians)."""
        R = rot(np.pi / 2)
        np.testing.assert_array_almost_equal(R, np.array([[0, -1], [1, 0]]), decimal=6)

    def test_rot_minus_90deg(self):
        """Test rot returns correct matrix for -90 degrees (-pi/2 radians)."""
        R = rot(-np.pi / 2)
        np.testing.assert_array_almost_equal(R, np.array([[0, 1], [-1, 0]]), decimal=6)

    def test_rotate_2d_point_no_rotation(self):
        """Test rotate_2d_point returns the same point for 0 degree rotation."""
        x = (2.0, 3.0)
        center = (1.0, 1.0)
        angle = 0.0
        result = rotate_2d_point(x, center, angle)
        np.testing.assert_array_almost_equal(result, x)

    def test_rotate_2d_point_around_origin(self):
        """Test rotate_2d_point rotates around origin."""
        x = (1.0, 0.0)
        center = (0.0, 0.0)
        angle = 90.0
        result = rotate_2d_point(x, center, angle)
        np.testing.assert_array_almost_equal(result, (0.0, 1.0), decimal=6)

    def test_rotate_2d_point_around_center(self):
        """Test rotate_2d_point rotates around a non-origin center."""
        x = (2.0, 1.0)
        center = (1.0, 1.0)
        angle = 180.0
        result = rotate_2d_point(x, center, angle)
        np.testing.assert_array_almost_equal(result, (0.0, 1.0), decimal=6)

    def test_euler2fix(self):
        """Test convertion from Euler angles to fix angles"""

        euler_angle = Point()

        euler_angle.x = 0
        euler_angle.y = 0
        euler_angle.z = 0
        fix_angle = euler2fix(euler_angle)

        assert fix_angle.x == approx(0.0)
        assert fix_angle.y == approx(0.0)
        assert fix_angle.z == approx(0.0)

        euler_angle.x = 135
        euler_angle.y = 99
        euler_angle.z = -30
        fix_angle = euler2fix(euler_angle)
        assert fix_angle.x == approx(98.045944)
        assert fix_angle.y == approx(-14.5532525)
        assert fix_angle.z == approx(83.4377462)

        euler_angle.x = 50
        euler_angle.y = 32
        euler_angle.z = 65
        fix_angle = euler2fix(euler_angle)
        assert fix_angle.x == approx(64.580333)
        assert fix_angle.y == approx(-33.388795)
        assert fix_angle.z == approx(49.2418955)

    def test_fix2euler(self):
        """Test convertion from fix angles to Euler angles"""

        fix_angle = Point()

        # Test by doing both transformation
        fix_angle.x = 30.23
        fix_angle.y = -85.52
        fix_angle.z = -10.98
        euler_angle = fix2euler(fix_angle)
        fix_angle2 = euler2fix(euler_angle)

        assert fix_angle.x == approx(fix_angle2.x)
        assert fix_angle.y == approx(fix_angle2.y)
        assert fix_angle.z == approx(fix_angle2.z)

    def test_non_dimensionalize_rate(self):
        """Test non_dimensionalize_rate returns correct values."""
        p, q, r = 10.0, 20.0, 30.0  # deg/s
        v = 100.0  # m/s
        b = 30.0   # m
        c = 5.0    # m

        pStar, qStar, rStar = non_dimensionalize_rate(p, q, r, v, b, c)
        assert pStar == approx(10.0 * 30.0 / (2 * 100.0))
        assert qStar == approx(20.0 * 5.0 / (2 * 100.0))
        assert rStar == approx(30.0 * 30.0 / (2 * 100.0))

    def test_dimensionalize_rate(self):
        """Test dimensionalize_rate returns correct values."""
        pStar, qStar, rStar = 1.5, 0.5, 2.0
        v = 80.0
        b = 20.0
        c = 4.0

        p, q, r = dimensionalize_rate(pStar, qStar, rStar, v, b, c)
        assert p == approx(1.5 * (2 * 80.0) / 20.0)
        assert q == approx(0.5 * (2 * 80.0) / 4.0)
        assert r == approx(2.0 * (2 * 80.0) / 20.0)

    def test_dimensionalize_and_non_dimensionalize_inverse(self):
        """Test that dimensionalize_rate and non_dimensionalize_rate are inverses."""
        p, q, r = 12.0, 24.0, 36.0
        v = 120.0
        b = 40.0
        c = 6.0

        pStar, qStar, rStar = non_dimensionalize_rate(p, q, r, v, b, c)
        p2, q2, r2 = dimensionalize_rate(pStar, qStar, rStar, v, b, c)
        assert p == approx(p2)
        assert q == approx(q2)
        assert r == approx(r2)


# Main
if __name__ == "__main__":
    main(verbosity=0)
