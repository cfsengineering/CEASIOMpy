"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Dimensionalization and non-dimensionalization methods of pitch/roll/yaw rates.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Feb-12

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from typing import (
    List,
    Tuple,
)

from numpy import (
    ndarray,
    complex128,
)

from ceasiompy import log


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def non_dimensionalize_rate(
    self,
    p: float,
    q: float,
    r: float,
    v: float,
) -> Tuple[float, float, float]:
    """
    Non-dimensionalize pitch, roll and yaw rates.

    Args:
        p (float): Roll rate in [deg/s].
        q (float): Pitch rate in [deg/s].
        r (float): Yaw rate in [deg/s].
        v (float): Velocity in [m/s].

    Returns:
        pStar (float): Non-dimensionalized roll rate in [deg/s].
        qStar (float): Non-dimensionalized pitch rate in [deg/s].
        rStar (float): Non-dimensionalized yaw rate in [deg/s].

    """
    pStar = p * self.b / (2 * v)
    qStar = q * self.c / (2 * v)
    rStar = r * self.b / (2 * v)

    return pStar, qStar, rStar


def dimensionalize_rate(
    self,
    pStar: float,
    qStar: float,
    rStar: float,
    v: float
) -> Tuple[float, float, float]:
    """
    Dimensionalize pitch, roll and yaw rates.

    Args:
        pStar (float): Non-dimensionalized roll rate in [deg/s].
        qStar (float): Non-dimensionalized pitch rate in [deg/s].
        rStar (float): Non-dimensionalized yaw rate in [deg/s].
        v (float): Velocity in [m/s].

    Returns:
        p (float): Roll rate in [deg/s].
        q (float): Pitch rate in [deg/s].
        r (float): Yaw rate in [deg/s].

    """
    p = pStar * (2 * v) / self.b
    q = qStar * (2 * v) / self.c
    r = rStar * (2 * v) / self.b

    return p, q, r


def exp_i(omega: float, t: float) -> complex128:
    """
    Computes e^{iwt}.
    """
    return np.exp(1j * t * omega)


def alpha(omega: float, t: float, alpha_0: float) -> complex:
    """
    Defines alpha oscillations for Doublet Lattice method.
    alpha(t) = alpha_0 e^{iwt}
    """

    return alpha_0 * exp_i(omega, t)


def beta(omega: float, t: float, beta_0: float) -> complex:
    """
    Defines beta oscillations for Doublet Lattice method.
    beta(t) = beta_0 e^{iwt}
    """

    return beta_0 * exp_i(omega, t)


def dalpha_dt(omega: float, t: float, alpha_0: float) -> complex:
    """
    Computes the derivative of alpha wrt to time at time t.
    d alpha / dt (t) = i w alpha_0 e^{iwt}.
    """
    return 1j * omega * alpha(omega, t, alpha_0)


def dbeta_dt(omega: float, t: float, beta_0: float) -> complex:
    """
    Computes the derivative of beta wrt to time at time t.
    d beta / dt (t) = i w beta_0 e^{iwt}.
    """

    return 1j * omega * beta(omega, t, beta_0)


def complex_decomposition(array: ndarray) -> Tuple[ndarray, ndarray]:
    """
    Decomposes a complex numpy array into its real and imaginary parts.
    """

    real_part = np.real(array)
    imaginary_part = np.imag(array)

    return real_part, imaginary_part


def complex_cross(a: ndarray, b: ndarray) -> ndarray:
    """
    Cross product of two complex ndarrays.
    """
    real_part = np.cross(a.real, b.real) - np.cross(a.imag, b.imag)
    imag_part = np.cross(a.real, b.imag) + np.cross(a.imag, b.real)

    return real_part + 1j * imag_part


def sdsa_format(list: List) -> str:
    return " ".join(map(str, list))

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
