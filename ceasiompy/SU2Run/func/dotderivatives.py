"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Computing derivatives for dynamic stability.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Feb-24

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from cpacspy.cpacsfunctions import get_value

from typing import Tuple
from numpy import ndarray
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

from ceasiompy.utils.commonxpath import (
    SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
    SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
    SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def norm(vector: ndarray) -> float:
    """
    Returns Euclidean norm of a vector ndarray.

    Args:
        vector (ndarray): Input vector on which we take the norm.

    Returns:
        float: Norm of this vector.

    """
    return np.linalg.norm(vector)**2


def load_parameters(tixi: Tixi3) -> Tuple[float, float, float, ndarray]:
    """
    Load parameters for derivatives computation.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.

    Returns:
        Tuple[float, float, float, ndarray]: Oscillation's parameters.

    """

    # Amplitude
    a = get_value(tixi, SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH)

    # Frequency
    omega = get_value(tixi, SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH)

    # Time
    n = int(get_value(tixi, SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH))

    # Ensure n is odd
    if n % 2 == 0:
        n += 1

    # Create time vector t
    t = np.linspace(0, 2 * np.pi * (n) / (omega * (n + 1)), n + 1)

    return a, omega, n, t


def compute_derivatives(
    a: float,
    omega: float,
    t: ndarray,
    f_time: ndarray,
    f_static: ndarray,
) -> Tuple[float, float]:
    """
    Compute derivatives through SU2 results.

    Source:
        https://www.overleaf.com/read/xgnbfvjhvbxp#809b6e

    Args:
        a (float): Amplitude (alpha_0).
        omega (float): Angular frequency (w).
        t (ndarray): Time vector (t_1, ..., t_n).
        f_time (ndarray): Forces/moments on dynamic object (F(alpha, alpha_dot)(t)).
        f_static (ndarray): Forces/moments on static object (F(0, 0)).

    Returns:
        Angle and Angle_dot derivative (alpha, alpha_dot derivatives).

    """

    log.info("t shape: %s", t.shape)

    # Define the variables
    cwt = np.cos(omega * t)
    swt = np.sin(omega * t)

    cwt_swt = np.dot(swt, cwt)

    n_cwt = norm(cwt)
    n_swt = norm(swt)

    # Define the matrix M (corresponds to M^-1 in latex).
    M = np.array([
        [n_cwt, -cwt_swt],
        [-cwt_swt, n_swt]
    ])

    det_M = n_cwt * n_swt - (cwt_swt ** 2)

    # Differences
    f = f_time - f_static
    log.info("f shape: %s", f.shape)

    # Define the vector
    vector = np.array([
        np.dot(swt, f),
        np.dot(cwt, f)
    ])

    log.info("vector shape: %s", vector.shape)

    x_min, y_min = (det_M / a) * np.dot(M, vector)

    log.info("x_min shape: %s, y_min shape: %s", x_min.shape, y_min.shape)

    return x_min, y_min

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
