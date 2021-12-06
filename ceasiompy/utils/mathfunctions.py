"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Math functions which are used in different modules of CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-19
| Last modifiction: 2019-10-04

TODO:

    * Angle naming could be imporve to respect coding guidelines
    * Add Source and documentation

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import copy
import math
import numpy as np

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def euler2fix(rotation_euler):
    """ Function to convert Euler angles into fix angles.

    Function to convert an Euler angle roation into a fix angle rotation
    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz (x,y',z")
    Fix angle (SUMO): Rotation around the axis are done independently (x,y,x)

    Source :
        * TODO: add math documentation

    Args:
        rotation_euler (object): Object containing Euler rotation in x,y,z [deg]

    Returns:
        rotation_fix (object): Object containing Fixed angle rotation
                               in x,y,z [degree]

    """

    # Angle of rotation (Euler angle)
    RaX = math.radians(rotation_euler.x)
    RaY = math.radians(rotation_euler.y)
    RaZ = math.radians(rotation_euler.z)

    # Rotation matrices
    Rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(RaX), -math.sin(RaX)],
            [0.0, math.sin(RaX), math.cos(RaX)],
        ]
    )
    Ry = np.array(
        [
            [math.cos(RaY), 0.0, -math.sin(RaY)],
            [0.0, 1.0, 0.0],
            [math.sin(RaY), 0.0, math.cos(RaY)],
        ]
    )
    Rz = np.array(
        [
            [math.cos(RaZ), -math.sin(RaZ), 0.0],
            [math.sin(RaZ), math.cos(RaZ), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    # Identity matrices
    I = np.eye(3)
    I2 = Rx @ I
    I3 = Ry @ I2

    # Direction cosine matrix
    DirCos = Rz @ I3

    # Angle of rotation (fix frame angle)
    rax = math.atan2(-DirCos[1, 2], DirCos[2, 2])
    ray = math.atan2(DirCos[0, 2], DirCos[2, 2] * math.cos(rax) - DirCos[1, 2] * math.sin(rax))
    raz = math.atan2(
        DirCos[1, 0] * math.cos(rax) + DirCos[2, 0] * math.sin(rax),
        DirCos[1, 1] * math.cos(rax) + DirCos[2, 1] * math.sin(rax),
    )

    # Transform back to degree and round angles
    rax = round(math.degrees(rax), 2)
    ray = round(math.degrees(ray), 2)
    raz = round(math.degrees(raz), 2)

    # Get the result between -180 and 180 deg
    if rax >= 180:
        rax = rax - 360
    if rax <= -180:
        rax = rax + 360
    if ray >= 180:
        ray = ray - 360
    if ray <= -180:
        ray = ray + 360
    if raz >= 180:
        raz = raz - 360
    if raz <= -180:
        raz = raz + 360

    # But for a mysterious reason... (convention?)
    ray = -ray

    # Return the rotation as an object
    rotation_fix = copy.deepcopy(rotation_euler)
    rotation_fix.x = rax
    rotation_fix.y = ray
    rotation_fix.z = raz

    return rotation_fix


def fix2euler(rotation_fix):
    """ Function to convert fix angles into Euler angles.

    Function to convert a fix angle rotation into an Euler angle roation
    Fix angle (for SUMO): Rotation around the tree axe are done independently
    (x,y,x)
    Euler angle (CPACS): First rotation around Ox, then rotation around
    already rotated Oy and finally rotation around already rotated Oz
    (x,y',z")

    Source :
        * TODO: add math documentation

    Args:
        rotation_fix (object): Object containing Fixed angle rotation
                               in x,y,z [degree]

    Returns:
        rotation_euler (object): Object containing Euler rotation in x,y,z [deg]


    """

    # Angle of rotation (Fix frame angle)
    RaX = math.radians(rotation_fix.x)
    RaY = math.radians(rotation_fix.y)
    RaZ = math.radians(rotation_fix.z)

    # Rotation matrices
    Rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(RaX), -math.sin(RaX)],
            [0.0, math.sin(RaX), math.cos(RaX)],
        ]
    )
    Ry = np.array(
        [
            [math.cos(RaY), 0.0, -math.sin(RaY)],
            [0.0, 1.0, 0.0],
            [math.sin(RaY), 0.0, math.cos(RaY)],
        ]
    )
    Rz = np.array(
        [
            [math.cos(RaZ), -math.sin(RaZ), 0.0],
            [math.sin(RaZ), math.cos(RaZ), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    # Direction cosine matrix
    DirCos = Rx @ Ry @ Rz

    # Angle of rotation (euler angle)
    rax = math.atan2(DirCos[2, 1], DirCos[2, 2])
    ray = math.atan2(DirCos[2, 0], math.sqrt(DirCos[2, 1] ** 2 + DirCos[2, 2] ** 2))
    raz = math.atan2(DirCos[0, 0], DirCos[1, 0])

    # Transform back to degree and round angles
    rax = round(math.degrees(rax), 2)
    ray = round(math.degrees(ray), 2)
    raz = round(-math.degrees(raz) + 90.0, 2)

    # Return the rotation as an object
    rotation_euler = copy.deepcopy(rotation_fix)
    rotation_euler.x = rax
    rotation_euler.y = ray
    rotation_euler.z = raz

    return rotation_euler


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
