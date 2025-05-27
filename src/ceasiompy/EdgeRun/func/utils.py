"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for Airinnova AB, Stockholm, Sweden

Functions to manipulate Edge input file and results.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.moduleinterfaces import get_module_path

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_edge_ainp_template():
    """Return path of the M-Edge ainp template corresponding to the M-Edge version."""

    #    su2_version = get_su2_version()
    edge_dir = get_module_path("EdgeRun")
    edge_ainp_template_path = Path(edge_dir, "files", "default.ainp.tmp")
    if not edge_ainp_template_path.is_file():
        raise FileNotFoundError(
            f"The M-Edge ainp template '{edge_ainp_template_path}' has not been found!"
        )
    return edge_ainp_template_path


def get_edge_que_script_template():
    """Return path of the M-Edge ainp template corresponding to the M-Edge version."""

    edge_dir = get_module_path("EdgeRun")
    edge_queScript_template_path = Path(edge_dir, "files", "queue_template.script")
    if not edge_queScript_template_path.is_file():
        raise FileNotFoundError(
            f"The M-Edge queueScript template '{edge_queScript_template_path}' has not been found!"
        )
    return edge_queScript_template_path


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
            # TODO: Check which axis name correspond to that: cml, cmd, cms
            if "Total CMx:" in line:
                cmd = float(line.split(":")[1].split("|")[0])
            if "Total CMy:" in line:
                cms = float(line.split(":")[1].split("|")[0])
            if "Total CMz:" in line:
                cml = float(line.split(":")[1].split("|")[0])
            if "Free-stream velocity" in line and "m/s" in line:
                velocity = float(line.split(" ")[7])

    return cl, cd, cs, cmd, cms, cml, velocity
