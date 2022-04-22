"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-21

TODO:

    -Connect this script with the correct information of generatemesh.py



"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import os
import pickle
import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])
# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def gen_rot_disk(disk_position, disk_axis, radius):
    """
    Function to create a rotating disk in a given location
    ...

    Args:
    ----------
    disk_position : (float, float, float)
        position of the disk
    disk_axis : (float, float, float)
        axis of the disk
    radius : float
        radius of the disk
    """

    # generate the disk (gmsh always create a disk in the xy plane)
    disk_tag = gmsh.model.occ.addDisk(*disk_position, radius, radius)
    disk_dimtag = (2, disk_tag)

    disk_axis = list(disk_axis)
    xy_vector = [0, 0, 1]

    if disk_axis != xy_vector:
        rotation_axis = np.cross(disk_axis, xy_vector)
        gmsh.model.occ.rotate([disk_dimtag], *disk_position, *rotation_axis, np.pi / 2)
        gmsh.model.occ.synchronize()

    return disk_dimtag
