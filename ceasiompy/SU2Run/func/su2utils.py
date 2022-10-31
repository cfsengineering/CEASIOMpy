"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate SU2 Configuration and results.

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2019-09-30

TODO:


"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import re
from pathlib import Path

import requests
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_install_path
from ceasiompy.utils.commonnames import (
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,
    ENGINE_EXHAUST_SUFFIX,
    ENGINE_INTAKE_SUFFIX,
)
from ceasiompy.utils.moduleinterfaces import get_module_path

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_mesh_markers(su2_mesh_path):
    """Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_markers' return a dictionary of the mesh markers found in the SU2 mesh file
    sorted as farfield, symmetry, engine_intake, engine_exhaust, wall.

    Args:
        su2_mesh_path (Path):  Path to the SU2 mesh

    Returns:
        mesh_markers (dict): Dictionary of the mesh markers found in the SU2 mesh file

    """

    if not su2_mesh_path.is_file():
        raise FileNotFoundError(f"The SU2 mesh '{su2_mesh_path}' has not been found!")

    if not su2_mesh_path.suffix == ".su2":
        raise ValueError("The input must be SU2 mesh (*.su2)!")

    mesh_markers = {
        "farfield": [],
        "symmetry": [],
        "engine_intake": [],
        "engine_exhaust": [],
        "actuator_disk_inlet": [],
        "actuator_disk_outlet": [],
        "wall": [],
    }

    with open(su2_mesh_path) as f:
        lines = f.readlines()

    for line in lines:

        if "MARKER_TAG" not in line:
            continue

        marker = line.split("=")[1].strip()

        if "farfield" in marker.lower():
            mesh_markers["farfield"].append(marker)
            log.info(f"'{marker}' marker has been marked as farfield.")
        elif "symmetry" in marker.lower():
            mesh_markers["symmetry"].append(marker)
            log.info(f"'{marker}' marker has been marked as symmetry.")
        elif marker.endswith(ENGINE_INTAKE_SUFFIX):
            mesh_markers["engine_intake"].append(marker)
            log.info(f"'{marker}' marker has been marked as engine_intake.")
        elif marker.endswith(ENGINE_EXHAUST_SUFFIX):
            mesh_markers["engine_exhaust"].append(marker)
            log.info(f"'{marker}' marker has been marked as engine_exhaust.")
        elif marker.endswith(ACTUATOR_DISK_INLET_SUFFIX):
            mesh_markers["actuator_disk_inlet"].append(marker)
            log.info(f"'{marker}' marker has been marked as actuator_disk_inlet.")
        elif marker.endswith(ACTUATOR_DISK_OUTLET_SUFFIX):
            mesh_markers["actuator_disk_outlet"].append(marker)
            log.info(f"'{marker}' marker has been marked as actuator_disk_outlet.")
        else:
            mesh_markers["wall"].append(marker)
            log.info(f"'{marker}' marker has been marked as wall.")

    if not any(mesh_markers.values()):
        raise ValueError("No mesh markers found!")

    for key, value in mesh_markers.items():
        if not value:
            mesh_markers[key] = ["None"]

    return mesh_markers


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


def get_su2_aerocoefs(force_file):
    """Get aerodynamic coefficients and velocity from SU2 forces file (forces_breakdown.dat)

    Args:
        force_file (Path): Path to the SU2 forces file

    Returns:
        cl, cd, cs, cmd, cms, cml, velocity: Aerodynamic coefficients and velocity
    """

    if not force_file.is_file():
        raise FileNotFoundError(f"The SU2 forces file '{force_file}' has not been found!")

    cl, cd, cs, cmd, cms, cml, velocity = None, None, None, None, None, None, None

    with open(force_file) as f:
        for line in f.readlines():
            if "Total CL:" in line:
                cl = float(line.split(":")[1].split("|")[0])
            if "Total CD:" in line:
                cd = float(line.split(":")[1].split("|")[0])
            if "Total CSF:" in line:
                cs = float(line.split(":")[1].split("|")[0])
            # TODO: Check which axis name corespond to that: cml, cmd, cms
            if "Total CMx:" in line:
                cmd = float(line.split(":")[1].split("|")[0])
            if "Total CMy:" in line:
                cms = float(line.split(":")[1].split("|")[0])
            if "Total CMz:" in line:
                cml = float(line.split(":")[1].split("|")[0])
            if "Free-stream velocity" in line and "m/s" in line:
                velocity = float(line.split(" ")[7])

    return cl, cd, cs, cmd, cms, cml, velocity


def get_efficiency_and_aoa(force_file):
    """Function to get efficiency (CL/CD) and angle of attack (AoA)

    Function 'get_efficiency_and_aoa' search for the efficiency (CL/CD) and
    the Angle of Attack (AoA) in the results file (forces_breakdown.dat)

    Args:
        force_file (Path): Path to the SU2 forces file

    Returns:
        cl_cd (float):  CL/CD ratio [-]
        aoa (float):    Angle of Attack [deg]

    """

    if not force_file.is_file():
        raise FileNotFoundError(f"The SU2 forces file '{force_file}' has not been found!")

    cl_cd = None
    aoa = None

    with open(force_file) as f:
        for line in f.readlines():
            if "CL/CD" in line:
                cl_cd = float(line.split(":")[1].split("|")[0])
                continue

            if "Angle of attack (AoA):" in line:
                aoa = float(line.split("Angle of attack (AoA):")[1].split("deg,")[0].strip())
                continue

            if cl_cd and aoa:
                break

    if cl_cd is None:
        raise ValueError(f"No value has been found for the CL/CD ratio in {force_file}")
    else:
        log.info("CL/CD ratio has been found and is equal to: " + str(cl_cd) + "[-]")

    if aoa is None:
        raise ValueError(f"No value has been found for the AoA in {force_file}")
    else:
        log.info("AoA has been found and is equal to: " + str(aoa) + "[-]")

    return cl_cd, aoa


def get_wetted_area(su2_logfile):
    """Function get the wetted area calculated by SU2

    Function 'get_wetted_area' finds the SU2 logfile and returns the wetted
    area value previously calculated by SU2.

    Args:
        su2_logfile (Path): Path to the working directory

    Returns:
        wetted_area (float): Wetted area calculated by SU2 [m^2]

    """

    if not su2_logfile.is_file():
        raise FileNotFoundError(f"The SU2 logfile '{su2_logfile}' has not been found!")

    with open(su2_logfile) as f:
        for line in f.readlines():
            if "Wetted area =" not in line:
                continue

            wetted_area = float(line.split(" ")[3])
            log.info(f"Wetted area value has been found : {wetted_area} [m^2]")
            return wetted_area

    log.warning("No value has been found for the wetted area!, returning 0 [m^2]")
    return 0


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
    print("You can use this module by importing for example:")
    print("from ceasiompy.SU2Run.func.su2meshutils import get_mesh_markers")
