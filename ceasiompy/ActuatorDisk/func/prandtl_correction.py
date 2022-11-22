from math import pi, acos, exp, sqrt
import numpy as np


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
