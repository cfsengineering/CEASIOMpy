"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate SU2 Configuration and results.

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-09-30

TODO:


"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_mesh_marker(su2_mesh_path):
    """Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_marker' return all the SU2 mesh marker (except Farfield)
    found in the SU2 mesh file.

    Args:
        su2_mesh_path (interger):  Path to the SU2 mesh

    """

    if not os.path.isfile(su2_mesh_path):
        raise FileNotFoundError(f"The SU2 mesh '{su2_mesh_path}' has not been found!")

    if not su2_mesh_path.endswith(".su2"):
        raise ValueError("The input must be SU2 mesh (*.su2)!")

    with open(su2_mesh_path) as f:
        lines = f.readlines()

    wall_marker_list = []
    eng_bc_marker_list = []

    for line in lines:
        if "MARKER_TAG" in line and "Farfield" not in line:
            marker = line.split("=")[1].strip("\n").strip()

            if marker.endswith("Intake") or marker.endswith("Exhaust"):
                eng_bc_marker_list.append(marker)
            else:
                wall_marker_list.append(marker)

    if not wall_marker_list and not eng_bc_marker_list:
        raise ValueError('No "MARKER_TAG" has been found in the mesh!')

    log.info(f"{len(wall_marker_list)} wall BC have bend found:")
    for marker in wall_marker_list:
        log.info(f"  - {marker}")

    log.info(f"{len(eng_bc_marker_list)} engine BC have bend found:")
    for eng_marker in eng_bc_marker_list:
        log.info(f"  - {eng_marker}")

    return wall_marker_list, eng_bc_marker_list


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
    print("You can use this module by importing:")
    print("from ceasiompy.SU2Run.func.su2meshutils import get_mesh_marker")
