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
import math
from shapely.geometry import Polygon
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


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


def rotate_3D_points(x, y, z, angle_x, angle_y, angle_z):
    """Function to apply a 3D rotation to the coordinates of a point

    Function 'rotate_3D_points' returns the rotated points after applying
    a 3D rotation matrix.

    Source:
       * https://en.wikipedia.org/wiki/Rotation_matrix

    Args:
        x (float):  x coordinate of the initial point
        y (float):  y coordinate of the initial point
        z (float):  z coordinate of the initial point
        angle_x (float):  rotation angle around x-axis [rad]
        angle_y (float):  rotation angle around y-axis [rad]
        angle_z (float):  rotation angle around z-axis [rad]

    Returns:
        x_rot (float): x coordinate of the rotated point
        y_rot (float): y coordinate of the rotated point
        z_rot (float): z coordinate of the rotated point
    """
    R11 = math.cos(angle_z) * math.cos(angle_y)
    R12 = math.cos(angle_z) * math.sin(angle_y) * math.sin(angle_x) - \
        math.sin(angle_z) * math.cos(angle_x)
    R13 = math.cos(angle_z) * math.sin(angle_y) * math.cos(angle_x) + \
        math.sin(angle_z) * math.sin(angle_x)
    R21 = math.sin(angle_z) * math.cos(angle_y)
    R22 = math.sin(angle_z) * math.sin(angle_y) * math.sin(angle_x) + \
        math.cos(angle_z) * math.cos(angle_x)
    R23 = math.sin(angle_z) * math.sin(angle_y) * math.cos(angle_x) - \
        math.cos(angle_z) * math.sin(angle_x)
    R31 = -math.sin(angle_y)
    R32 = math.cos(angle_y) * math.sin(angle_x)
    R33 = math.cos(angle_y) * math.cos(angle_x)

    rotation_matrix = np.array([[R11, R12, R13],
                                [R21, R22, R23],
                                [R31, R32, R33]])

    x_rot = x * rotation_matrix[0, 0] + y * \
        rotation_matrix[0, 1] + z * rotation_matrix[0, 2]
    y_rot = x * rotation_matrix[1, 0] + y * \
        rotation_matrix[1, 1] + z * rotation_matrix[1, 2]
    z_rot = x * rotation_matrix[2, 0] + y * \
        rotation_matrix[2, 1] + z * rotation_matrix[2, 2]

    return x_rot, y_rot, z_rot


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")