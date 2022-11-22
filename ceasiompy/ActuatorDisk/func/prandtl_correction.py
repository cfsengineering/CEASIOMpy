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


def prandtl_corr(prandtl, stations, blades_number, r, omega, radius, free_stream_velocity):
    correction_function = np.empty(stations)
    if prandtl:
        for i in range(stations):
            correction_function[i] = (2 / pi) * acos(
                exp(
                    -0.5
                    * blades_number
                    * (1 - r[i])
                    * sqrt(1 + (omega * radius / free_stream_velocity) ** 2)
                )
            )

    else:
        correction_function = np.ones(stations)

    return correction_function
