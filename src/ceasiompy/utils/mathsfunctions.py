"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Math functions which are used in different modules of CEASIOMpy.
| Author : Leon Deligny
| Creation: 2025-Mar-03

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math

import numpy as np

from math import (
    cos,
    sin,
)

from typing import Tuple
from numpy import ndarray
from ceasiompy.utils.generalclasses import Point
from scipy.spatial.transform import Rotation as R

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

    return np.array(
        [
            [c, -s],
            [s, c],
        ]
    )


def rotate_2d_point(
    x: Tuple[float, float],
    center_point: Tuple[float, float],
    angle: float,
) -> Tuple[float, float]:
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

    Rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, cx, -sx],
            [0.0, sx, cx],
        ]
    )

    cy = cos(RaY)
    sy = sin(RaY)

    Ry = np.array(
        [
            [cy, 0.0, -sy],
            [0.0, 1.0, 0.0],
            [sy, 0.0, cy],
        ]
    )

    cz = cos(RaZ)
    sz = sin(RaZ)

    Rz = np.array(
        [
            [cz, -sz, 0.0],
            [sz, cz, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    return Rx, Ry, Rz


def euler2fix(rotation_euler):
    """
    Converts an Euler angle [deg] rotation into a fix angle [deg] rotation.

    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz (x,y',z").

    Fix angle (SUMO): Rotation around the axis are done independently (x,y,x).

    We are using XYZ Euler Angles, which are also known as Cardan angles.

    Source :
        https://ethz.ch/content/dam/ethz/special-interest/mavt/robotics-n-intelligent-systems/rsl-dam/documents/RobotDynamics2016/KinematicsSingleBody.pdf

    """
    object_ = False
    if isinstance(rotation_euler, Point):
        object_ = True
        rotation_euler = np.array([rotation_euler.x, rotation_euler.y, rotation_euler.z])

    rotation = R.from_euler("zyx", rotation_euler, degrees=True)

    fix_angles = rotation.as_euler("xyz", degrees=True)

    if object_:
        return Point(
            x=fix_angles[0],
            y=fix_angles[1],
            z=fix_angles[2],
        )
    else:
        return fix_angles


def fix2euler(rotation_fix):
    """
    Convert a fix angle [deg] rotation into an Euler angle [deg] rotation.

    Fix angle (for SUMO): Rotation around the three axes are done independently.

    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz
    (x,y',z").

    We are using ZYX Euler angles, also known as Tait-Bryan angles.

    Source:
        https://ethz.ch/content/dam/ethz/special-interest/mavt/robotics-n-intelligent-systems/rsl-dam/documents/RobotDynamics2016/KinematicsSingleBody.pdf

    """
    object_ = False
    if isinstance(rotation_fix, Point):
        object_ = True
        rotation_fix = np.array([rotation_fix.x, rotation_fix.y, rotation_fix.z])

    rotation = R.from_euler("xyz", rotation_fix, degrees=True)

    euler_angles = rotation.as_euler("zyx", degrees=True)

    if object_:
        return Point(
            x=euler_angles[0],
            y=euler_angles[1],
            z=euler_angles[2],
        )
    else:
        return euler_angles


def rotate_points(
    x: float, y: float, z: float, RaX: float, RaY: float, RaZ: float
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


def non_dimensionalize_rate(
    p: float,
    q: float,
    r: float,
    v: float,
    b: float,
    c: float,
) -> Tuple[float, float, float]:
    """
    Non-dimensionalize pitch, roll and yaw rates.

    Args:
        p (float): Roll rate in [deg/s].
        q (float): Pitch rate in [deg/s].
        r (float): Yaw rate in [deg/s].
        v (float): Velocity in [m/s].
        b (float): Span of aircraft [m].
        c (float): Chord of aircraft [m].

    Returns:
        pStar (float): Non-dimensionalized roll rate in [deg/s].
        qStar (float): Non-dimensionalized pitch rate in [deg/s].
        rStar (float): Non-dimensionalized yaw rate in [deg/s].

    """
    pStar = p * b / (2 * v)
    qStar = q * c / (2 * v)
    rStar = r * b / (2 * v)

    return pStar, qStar, rStar


def dimensionalize_rate(
    pStar: float,
    qStar: float,
    rStar: float,
    v: float,
    b: float,
    c: float,
) -> Tuple[float, float, float]:
    """
    Dimensionalize pitch, roll and yaw rates.

    Args:
        pStar (float): Non-dimensionalized roll rate in [deg/s].
        qStar (float): Non-dimensionalized pitch rate in [deg/s].
        rStar (float): Non-dimensionalized yaw rate in [deg/s].
        v (float): Velocity in [m/s].
        b (float): Span of aircraft [m].
        c (float): Chord of aircraft [m].

    Returns:
        p (float): Roll rate in [deg/s].
        q (float): Pitch rate in [deg/s].
        r (float): Yaw rate in [deg/s].

    """
    p = pStar * (2 * v) / b
    q = qStar * (2 * v) / c
    r = rStar * (2 * v) / b

    return p, q, r
