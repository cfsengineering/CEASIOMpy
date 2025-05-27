"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import numpy as np

from ceasiompy.DynamicStability.func.utils import (
    exp_i,
    alpha,
    beta,
    dalpha_dt,
    dbeta_dt,
    complex_decomposition,
    complex_cross,
    sdsa_format
)

from unittest import main

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestUtils(unittest.TestCase):

    def test_exp_i(self):
        self.assertAlmostEqual(exp_i(np.pi, 1), np.exp(1j * np.pi), places=10)

    def test_alpha(self):
        result = alpha(np.pi, 1, 2)
        expected = 2 * np.exp(1j * np.pi)
        self.assertAlmostEqual(result, expected)

    def test_beta(self):
        result = beta(np.pi, 1, 3)
        expected = 3 * np.exp(1j * np.pi)
        self.assertAlmostEqual(result, expected)

    def test_dalpha_dt(self):
        omega, t, alpha_0 = 2.0, 0.5, 1.5
        result = dalpha_dt(omega, t, alpha_0)
        expected = 1j * omega * alpha(omega, t, alpha_0)
        self.assertAlmostEqual(result, expected)

    def test_dbeta_dt(self):
        omega, t, beta_0 = 2.0, 0.5, 1.5
        result = dbeta_dt(omega, t, beta_0)
        expected = 1j * omega * beta(omega, t, beta_0)
        self.assertAlmostEqual(result, expected)

    def test_complex_decomposition(self):
        arr = np.array([1 + 2j, 3 - 4j])
        real, imag = complex_decomposition(arr)
        np.testing.assert_array_equal(real, np.array([1, 3]))
        np.testing.assert_array_equal(imag, np.array([2, -4]))

    def test_complex_cross(self):
        a = np.array([1 + 2j, 3 + 4j, 5 + 6j])
        b = np.array([6 + 5j, 4 + 3j, 2 + 1j])
        result = complex_cross(a, b)
        # Compare with numpy's cross for real and imag parts
        expected_real = np.cross(a.real, b.real) - np.cross(a.imag, b.imag)
        expected_imag = np.cross(a.real, b.imag) + np.cross(a.imag, b.real)
        np.testing.assert_array_almost_equal(result.real, expected_real)
        np.testing.assert_array_almost_equal(result.imag, expected_imag)

    def test_sdsa_format(self):
        self.assertEqual(sdsa_format([1, 2, 3]), "1 2 3")
        self.assertEqual(sdsa_format(["a", "b", "c"]), "a b c")


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
