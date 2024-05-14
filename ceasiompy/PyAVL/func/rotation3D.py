"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to apply a 3D rotation to the coordinates of a point.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-13

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
import numpy as np
import math

log = get_logger()


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


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
    rotation_matrix = np.array([[math.cos(angle_z) * math.cos(angle_y), math.cos(angle_z) * math.sin(angle_y) * math.sin(angle_x) - math.sin(angle_z) * math.cos(angle_x), math.cos(angle_z) * math.sin(angle_y) * math.cos(angle_x) + math.sin(angle_z) * math.sin(angle_x)],
                                [math.sin(angle_z) * math.cos(angle_y), math.sin(angle_z) * math.sin(angle_y) * math.sin(angle_x) + math.cos(angle_z) * math.cos(
                                    angle_x), math.sin(angle_z) * math.sin(angle_y) * math.cos(angle_x) - math.cos(angle_z) * math.sin(angle_x)],
                                [-math.sin(angle_y), math.cos(angle_y) * math.sin(angle_x), math.cos(angle_y) * math.cos(angle_x)]])
    x_rot = x * rotation_matrix[0, 0] + y * \
        rotation_matrix[0, 1] + z * rotation_matrix[0, 2]
    y_rot = x * rotation_matrix[1, 0] + y * \
        rotation_matrix[1, 1] + z * rotation_matrix[1, 2]
    z_rot = x * rotation_matrix[2, 0] + y * \
        rotation_matrix[2, 1] + z * rotation_matrix[2, 2]

    return x_rot, y_rot, z_rot


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
