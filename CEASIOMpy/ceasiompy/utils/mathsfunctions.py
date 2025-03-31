"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Math functions which are used in different modules of CEASIOMpy.

Python version: >=3.8

| Author : Leon Deligny
| Creation: 2025-Mar-03

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import copy
import math

import numpy as np

from math import (
    cos,
    sin,
)

from typing import Tuple
from numpy import ndarray

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def rot(angle: float) -> ndarray:
    """
    2D Rotation matrix.

    Args:
        angle (float): Angle of rotation [rad].

    Returns:
        (ndarray): Rotation matrix of this angle.
    """
    c = cos(angle)
    s = sin(angle)

    return np.array([
        [c, -s],
        [s, c],
    ])


def rotate_2d_point(x: Tuple[float, float], center_point: Tuple[float,
                    float], angle: float) -> Tuple[float, float]:
    """
    Rotate a point in a 2d space.

    Args:
        x (Tuple[float, float]): (x, z) point to rotate.
        center_point (Tuple[float, float]): Center of rotation.
        angle (float): Angle of ration [deg].

    Returns:
        (Tuple[float, float]): Rotated point.

    """
    angle_rad = math.radians(angle)
    rotation_matrix = rot(angle_rad)

    # Center the point
    x_centered = np.array([x[0] - center_point[0], x[1] - center_point[1]])

    # Apply the rotation matrix
    rotated_point = np.dot(rotation_matrix, x_centered)

    # Translate back to the original center
    return rotated_point[0] + center_point[0], rotated_point[1] + center_point[1]


def get_rotation_matrix(RaX: float, RaY: float, RaZ: float) -> Tuple[ndarray, ndarray, ndarray]:
    """
    Computes the rotation matrices for rotations around the X, Y, and Z axes.

    Args:
        RaX (float): Rotation angle around the X-axis [rad].
        RaY (float): Rotation angle around the Y-axis [rad].
        RaZ (float): Rotation angle around the Z-axis [rad].

    Returns:
        (Tuple[ndarray, ndarray, ndarray]): Rotation matrices for the X, Y, and Z axes resp.

    """

    cx = cos(RaX)
    sx = sin(RaX)

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cx, -sx],
        [0.0, sx, cx],
    ])

    cy = cos(RaY)
    sy = sin(RaY)

    Ry = np.array([
        [cy, 0.0, -sy],
        [0.0, 1.0, 0.0],
        [sy, 0.0, cy],
    ])

    cz = cos(RaZ)
    sz = sin(RaZ)

    Rz = np.array([
        [cz, -sz, 0.0],
        [sz, cz, 0.0],
        [0.0, 0.0, 1.0],
    ])

    return Rx, Ry, Rz


def euler2fix(rotation_euler: object) -> object:
    """
    Converts an Euler angle rotation into a fix angle rotation.

    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz (x,y',z").

    Fix angle (SUMO): Rotation around the axis are done independently (x,y,x).

    We are using XYZ Euler Angles, which are also known as Cardan angles.

    Source :
        https://ethz.ch/content/dam/ethz/special-interest/mavt/robotics-n-intelligent-systems/rsl-dam/documents/RobotDynamics2016/KinematicsSingleBody.pdf

    Args:
        rotation_euler (object): Object containing Euler rotation in x,y,z [deg].

    Returns:
        (object): Fixed angle rotation in x,y,z [deg].

    """

    # Angle of rotation (Euler angle)
    RaX = math.radians(rotation_euler.x)
    RaY = math.radians(rotation_euler.y)
    RaZ = math.radians(rotation_euler.z)

    # Direction cosine matrix
    Rx, Ry, Rz = get_rotation_matrix(RaX, RaY, RaZ)

    # Identity matrices
    DirCos = Rx @ (Ry @ (Rz @ np.eye(3)))

    # Angle of rotation (fix frame angle)
    rax = math.atan2(-DirCos[1, 2], DirCos[2, 2])
    ray = math.atan2(DirCos[0, 2], math.sqrt(DirCos[0, 0] ** 2 + DirCos[0, 1] ** 2))
    raz = math.atan2(-DirCos[0, 1], DirCos[0, 0])

    # Transform back to degree and round angles
    rax = round(math.degrees(rax), 2)
    ray = round(math.degrees(ray), 2)
    raz = round(math.degrees(raz), 2)

    # Return the rotation as an object
    rotation_fix = copy.deepcopy(rotation_euler)
    rotation_fix.x = rax
    rotation_fix.y = ray
    rotation_fix.z = raz

    return rotation_fix


def fix2euler(rotation_fix: object) -> object:
    """
    Convert a fix angle rotation into an Euler angle rotation.

    Fix angle (for SUMO): Rotation around the three axes are done independently.

    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz
    (x,y',z").

    We are using ZYX Euler angles, also known as Tait-Bryan angles.

    Source:
        https://ethz.ch/content/dam/ethz/special-interest/mavt/robotics-n-intelligent-systems/rsl-dam/documents/RobotDynamics2016/KinematicsSingleBody.pdf

    Args:
        rotation_fix (object): Fixed angle rotation in x,y,z [deg].

    Returns:
        (object): Euler rotation in x,y,z [deg].

    """

    # Angle of rotation (Fix frame angle)
    RaX = math.radians(rotation_fix.x)
    RaY = math.radians(rotation_fix.y)
    RaZ = math.radians(rotation_fix.z)

    # Rotation matrices
    Rx, Ry, Rz = get_rotation_matrix(RaX, RaY, RaZ)

    # Direction cosine matrix
    DirCos = Rz @ (Ry @ (Rx @ np.eye(3)))

    # Angle of rotation (euler angle)
    rax = math.atan2(DirCos[2, 1], DirCos[2, 2])
    ray = math.atan2(-DirCos[2, 0], math.sqrt(DirCos[2, 1] ** 2 + DirCos[2, 2] ** 2))
    raz = math.atan2(DirCos[1, 0], DirCos[0, 0])

    # Transform back to degree and round angles
    rax = round(math.degrees(rax), 2)
    ray = round(math.degrees(ray), 2)
    raz = round(math.degrees(raz), 2)

    # Return the rotation as an object
    rotation_euler = copy.deepcopy(rotation_fix)
    rotation_euler.x = rax
    rotation_euler.y = ray
    rotation_euler.z = raz

    return rotation_euler


def rotate_points(
    x: float,
    y: float,
    z: float,
    RaX: float,
    RaY: float,
    RaZ: float
) -> Tuple[float, float, float]:
    """
    Applies a 3D rotation to the coordinates of a point.

    Args:
        x (float): x coordinate of the initial point.
        y (float): y coordinate of the initial point.
        z (float): z coordinate of the initial point.
        RaX (float): Rotation angle around x-axis [rad].
        Ray (float): Rotation angle around y-axis [rad].
        RaZ (float): Rotation angle around z-axis [rad].

    Returns:
        (Tuple[float, float, float]): x, y, z coordinates of the rotated point.

    """
    R_x, R_y, R_z = get_rotation_matrix(RaX, RaY, RaZ)

    rotation_matrix = R_z @ R_y @ R_x

    point = np.array([x, y, z])
    rotated_point = rotation_matrix @ point

    return rotated_point[0], rotated_point[1], rotated_point[2]


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
