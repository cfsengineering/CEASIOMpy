"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This function calculate, if it necessary, the Prandtl correction at blade's tip

Python version: >=3.8

| Author: Giacomo Benedetti
| Creation: 2022-11-22

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from math import pi, acos, exp, sqrt
import numpy as np


# =================================================================================================
#   FUNCTION
# =================================================================================================


def prandtl_corr(prandtl, blades_number, r, omega, radius, free_stream_velocity):

    if not prandtl:
        return np.ones(len(r))

    return (2 / pi) * np.arccos(
        np.exp(
            -0.5 * blades_number * (1 - r) * sqrt(1 + (omega * radius / free_stream_velocity) ** 2)
        )
    )
