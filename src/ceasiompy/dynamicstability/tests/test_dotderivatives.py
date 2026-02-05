"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import numpy as np

from ceasiompy.dynamicstability.func.dotderivatives import (
    check_x_hinge,
    compute_moments,
    get_main_wing_le,
    get_dynamic_pressure,
    scale_beta_coefficients,
    scale_alpha_coefficients,
    access_angle_derivatives,
    compute_beta_panel_forces,
    compute_alpha_panel_forces,
    access_angle_derivatives_np,
    access_angle_dot_derivatives,
    access_angle_dot_derivatives_np,
)

from ambiance import Atmosphere
from ceasiompy.dynamicstability.func.panelaeroconfig import AeroModel
from unittest import (
    main,
    TestCase,
)

from unittest.mock import patch
from ceasiompy.dynamicstability import MODULE_NAME as DYNAMIC_STABILITY


# Classes

class DummySelf:
    def __init__(self, s, c, b):
        self.s = s
        self.c = c
        self.b = b


class TestDotDerivatives(TestCase):

    def test_compute_alpha_panel_forces(self: "TestDotDerivatives") -> None:
        # Minimal aerogrid with 2 panels
        aerogrid = {
            "N": np.eye(3)[:, :2].T,  # shape (2,3) -> (3,2) after .T
            "A": np.array([1.0, 2.0]),
            "n": 2,
        }
        q_alpha_jj = np.eye(2)
        omegaalpha = 1.0
        q_dyn = 100.0
        t = 0.0
        alpha_0 = 0.1

        alphaforces = compute_alpha_panel_forces(
            aerogrid, q_alpha_jj, omegaalpha, q_dyn, t, alpha_0, 0.0
        )

        # Should return two arrays of shape (3, 2)
        self.assertEqual(alphaforces.shape, (3, 2))
        self.assertTrue(isinstance(alphaforces, np.ndarray))

    def test_compute_beta_panel_forces(self: "TestDotDerivatives") -> None:
        # Minimal aerogrid with 2 panels
        aerogrid = {
            "N": np.eye(3)[:, :2].T,  # shape (2,3) -> (3,2) after .T
            "A": np.array([1.0, 2.0]),
            "n": 2,
        }
        q_beta_jj = np.eye(2)
        omegabeta = 2.0
        q_dyn = 100.0
        t = 0.0
        beta_0 = 0.2

        betaforces = compute_beta_panel_forces(
            aerogrid, q_beta_jj, omegabeta, q_dyn, t, beta_0, 0.0
        )

        # Should return two arrays of shape (3, 2)
        self.assertEqual(betaforces.shape, (3, 2))
        self.assertTrue(isinstance(betaforces, np.ndarray))

    def test_get_main_wing_le(self: "TestDotDerivatives") -> None:
        # Two wings, main wing has smallest X1[0]
        wings_list = [{
            "EID": 1,  # str
            "CP": 0,  # int
            "n_span": 2,  # int
            "n_chord": 2,  # int
            "X1": np.array([0, 0, 0]),
            "length12": 1,  # float
            "X4": np.array([1, 1, 1]),
            "length43": 1,  # float
        }]
        model = AeroModel(wings_list)
        model.build_aerogrid()
        x, y, z = get_main_wing_le(model)
        self.assertEqual(x, 1)
        self.assertEqual(y, -1)
        self.assertEqual(z, 1)

    def test_check_x_hinge_warns(self: "TestDotDerivatives") -> None:
        aerogrid = {"offset_j": np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])}
        x_hinge = 1.0
        with patch(f"ceasiompy.{DYNAMIC_STABILITY}.func.dotderivatives.log") as mock_log:
            check_x_hinge(aerogrid, x_hinge)
            mock_log.warning.assert_called()
            args, _ = mock_log.warning.call_args
            self.assertIn("Hinge point can not be equal", args[0])

    def test_scale_alpha_coefficients(self) -> None:
        dummy = DummySelf(s=10.0, c=2.0, b=5.0)
        q_dyn = 100.0
        # All numerators are 1.0 for simplicity
        args = [q_dyn] + [1.0] * 9
        result = scale_alpha_coefficients(dummy, *args)
        qs = q_dyn * dummy.s
        qsb = qs * dummy.b
        qsc = qs * dummy.c

        # Check a few values
        self.assertAlmostEqual(result[0], 1.0 / qs)  # cx_alpha
        self.assertAlmostEqual(result[3], 1.0 / qsb)  # cl_alpha
        self.assertAlmostEqual(result[4], 1.0 / qsc)  # cm_alpha
        self.assertAlmostEqual(result[6], 1.0 / qsc)  # cm_alphadot
        self.assertAlmostEqual(result[7], 1.0 / qs)  # cz_alphadot

        # Check length
        self.assertEqual(len(result), 9)

    def test_scale_beta_coefficients(self) -> None:
        dummy = DummySelf(s=10.0, c=2.0, b=5.0)
        q_dyn = 100.0
        # All numerators are 1.0 for simplicity
        args = [q_dyn] + [1.0] * 9
        result = scale_beta_coefficients(dummy, *args)
        qs = q_dyn * dummy.s
        qsb = qs * dummy.b
        qsc = qs * dummy.c

        # Check a few values
        self.assertAlmostEqual(result[0], 1.0 / qs)
        self.assertAlmostEqual(result[3], 1.0 / qsb)
        self.assertAlmostEqual(result[4], 1.0 / qsc)
        self.assertAlmostEqual(result[6], 1.0 / qs)
        self.assertAlmostEqual(result[7], 1.0 / qsb)

        # Check length
        self.assertEqual(len(result), 9)

    def test_get_dynamic_pressure(self) -> None:
        atm = Atmosphere(h=0.0)
        mach = 0.5
        velocity = atm.speed_of_sound[0] * mach
        q_dyn = get_dynamic_pressure(atm, velocity)
        self.assertAlmostEqual(q_dyn, atm.density[0] * (velocity**2) / 2.0)

    def test_access_angle_derivatives(self: "TestDotDerivatives") -> None:
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

    def test_access_angle_derivatives_np(self: "TestDotDerivatives") -> None:
        f_real = np.ones((3, 4))
        f_img = np.zeros((3, 4))
        omega = 1.0
        t = 0.0
        angle_0 = 1.0
        result = access_angle_derivatives_np(f_real, f_img, omega, t, angle_0)
        self.assertEqual(result.shape, (3, 4))
        np.testing.assert_array_almost_equal(result, f_real)

    def test_access_angle_dot_derivatives(self: "TestDotDerivatives") -> None:
        f_real = np.array([1.0, 2.0, 3.0])
        f_img = np.array([0.5, 1.0, 1.5])
        omega = 2.0
        t = 0.5
        angle_0 = 1.0
        x, y, z = access_angle_dot_derivatives(f_real, f_img, omega, t, angle_0)
        self.assertTrue(isinstance(x, float))
        self.assertTrue(isinstance(y, float))
        self.assertTrue(isinstance(z, float))

    def test_access_angle_dot_derivatives_np(self: "TestDotDerivatives") -> None:
        f_real = np.ones((3, 4))
        f_img = np.zeros((3, 4))
        omega = 2.0
        t = 0.0
        angle_0 = 1.0
        result = access_angle_dot_derivatives_np(f_real, f_img, omega, t, angle_0)
        self.assertEqual(result.shape, (3, 4))

    def test_compute_moments_real(self: "TestDotDerivatives") -> None:
        aerogrid = {"offset_j": np.zeros((2, 3))}
        forces = np.ones((3, 2))
        x_hinge = 0.0
        y_hinge = 0.0
        z_hinge = 0.0
        moments = compute_moments(aerogrid, forces, x_hinge, y_hinge, z_hinge)
        self.assertEqual(moments.shape, (3,))

    def test_compute_moments_complex(self: "TestDotDerivatives") -> None:
        aerogrid = {"offset_j": np.zeros((2, 3))}
        forces = np.ones((3, 2)) + 1j * np.ones((3, 2))
        x_hinge = 0.0
        y_hinge = 0.0
        z_hinge = 0.0
        moments = compute_moments(aerogrid, forces, x_hinge, y_hinge, z_hinge)
        self.assertEqual(moments.shape, (3,))


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
