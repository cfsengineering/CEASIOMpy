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

import re
from pathlib import Path
import requests
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_install_path
from ceasiompy.utils.moduleinterfaces import get_module_path

log = get_logger()


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
        su2_mesh_path (Path):  Path to the SU2 mesh

    """

    if not su2_mesh_path.is_file():
        raise FileNotFoundError(f"The SU2 mesh '{su2_mesh_path}' has not been found!")

    if not su2_mesh_path.suffix == ".su2":
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


def get_su2_version():
    """
    Return the version of the installed SU2
    """

    su2py_path = get_install_path("SU2_CFD.py")

    if su2py_path:
        with open(su2py_path, "r") as f:
            for line in f.readlines():
                try:
                    version = re.search(r"version\s*([\d.]+)", line).group(1)
                except AttributeError:
                    version = None

                if version is not None:
                    log.info(f"Version of SU2 detected: {version}")
                    return version

    return None


def get_su2_config_template():
    """Return path of the SU2 config template coresponding to the SU2 version."""

    su2_version = get_su2_version()
    su2_dir = get_module_path("SU2Run")
    su2_config_template_path = Path(su2_dir, "files", f"config_template_v{su2_version}.cfg")

    if not su2_config_template_path.exists():

        # Use the Euler Onera M6 config as template
        url = (
            f"https://raw.githubusercontent.com/su2code/SU2/v{su2_version}"
            "/TestCases/euler/oneram6/inv_ONERAM6.cfg"
        )
        r = requests.get(url)

        if r.status_code == 404:
            raise FileNotFoundError(
                f"The SU2 config template for SU2 version {su2_version} does not exist."
            )

        if not r.status_code == 200:
            raise ConnectionError(
                f"Cannot download the template file for SU2 version {su2_version} at {url}"
            )

        with open(su2_config_template_path, "wb") as f:
            f.write(r.content)

    return su2_config_template_path


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
    print("You can use this module by importing:")
    print("from ceasiompy.SU2Run.func.su2meshutils import get_mesh_marker")
