"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to ...

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-06-17

TODO:

    * Things to improve...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================
import numpy as np

from shapely.geometry import Polygon

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def PolyArea(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def compute_centroid(x_coords, y_coords):
    polygon = Polygon(zip(x_coords, y_coords))
    centroid = polygon.centroid
    return centroid.x, centroid.y


def second_moments_of_area(x, y):
    Ix = 0
    Iy = 0
    x_centr, y_centr = compute_centroid(x, y)
    x = [xi - x_centr for xi in x]
    y = [yi - y_centr for yi in y]

    n = len(x)
    for i in range(n):
        j = (i + 1) % n
        Ix += (y[i]**2 + y[i] * y[j] + y[j]**2) * (x[i] * y[j] - x[j] * y[i])
        Iy += (x[i]**2 + x[i] * x[j] + x[j]**2) * (x[i] * y[j] - x[j] * y[i])

    Ix /= 12
    Iy /= 12

    return Ix, Iy


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
