"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from ceasiompy.DynamicStability.func.dotderivatives import (
    access_angle_derivatives,
    access_angle_derivatives_np,
    access_angle_dot_derivatives,
    access_angle_dot_derivatives_np,
    compute_moments,
)

from unittest import (
    main,
    TestCase,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestDotDerivatives(TestCase):

    def test_access_angle_derivatives(self):
        f_real = np.array([1.0, 2.0, 3.0])
        f_img = np.array([0.5, 1.0, 1.5])
        omega = np.pi
        t = 0.5
        angle_0 = 2.0
        x, y, z = access_angle_derivatives(f_real, f_img, omega, t, angle_0)
        # Check types and shapes
        self.assertTrue(isinstance(x, float))
        self.assertTrue(isinstance(y, float))
        self.assertTrue(isinstance(z, float))

    def test_access_angle_derivatives_np(self):
        f_real = np.ones((3, 4))
        f_img = np.zeros((3, 4))
        omega = 1.0
        t = 0.0
        angle_0 = 1.0
        result = access_angle_derivatives_np(f_real, f_img, omega, t, angle_0)
        self.assertEqual(result.shape, (3, 4))
        np.testing.assert_array_almost_equal(result, f_real)

    def test_access_angle_dot_derivatives(self):
        f_real = np.array([1.0, 2.0, 3.0])
        f_img = np.array([0.5, 1.0, 1.5])
        omega = 2.0
        t = 0.5
        angle_0 = 1.0
        x, y, z = access_angle_dot_derivatives(f_real, f_img, omega, t, angle_0)
        self.assertTrue(isinstance(x, float))
        self.assertTrue(isinstance(y, float))
        self.assertTrue(isinstance(z, float))

    def test_access_angle_dot_derivatives_np(self):
        f_real = np.ones((3, 4))
        f_img = np.zeros((3, 4))
        omega = 2.0
        t = 0.0
        angle_0 = 1.0
        result = access_angle_dot_derivatives_np(f_real, f_img, omega, t, angle_0)
        self.assertEqual(result.shape, (3, 4))

    def test_compute_moments_real(self):
        aerogrid = {"offset_j": np.zeros((2, 3))}
        forces = np.ones((3, 2))
        x_hinge = 0.0
        moments = compute_moments(aerogrid, forces, x_hinge)
        self.assertEqual(moments.shape, (3,))

    def test_compute_moments_complex(self):
        aerogrid = {"offset_j": np.zeros((2, 3))}
        forces = (np.ones((3, 2)) + 1j * np.ones((3, 2)))
        x_hinge = 0.0
        moments = compute_moments(aerogrid, forces, x_hinge)
        self.assertEqual(moments.shape, (3,))


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main()
