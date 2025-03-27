"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to get the flight conditions (alt, aoa, mach...) from
the input CPACS file, and write the command file for AVL.
More details at: https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-14
| Modified: Leon Deligny
| Date: 11-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.moduleinterfaces import get_module_path

from typing import Tuple
from pathlib import Path
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    AVL_PLOT_XPATH,
    AVL_DISTR_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def write_command_file(
    tixi: Tixi3,
    avl_path: Path,
    case_dir_path: Path,
    alpha: float,
    beta: float,
    pitch_rate: float,
    roll_rate: float,
    yaw_rate: float,
    mach_number: float,
    ref_velocity: float,
    ref_density: float,
    g_acceleration: float,
    aileron: float,
    elevator: float,
    rudder: float,
    save_plots: bool,
) -> Path:
    """
    Writes the command file for AVL.

    Args:
        tixi (handles): TIXI Handle of the CPACS file.
        avl_path (Path): Path to the AVL input file.
        case_dir_path (Path): path to the run case directory
        alpha (float): angle of attack [deg]
        beta (float): angle of attack [deg]
        pitch_rate (float): pitch rate [deg/s]
        roll_rate (float): roll rate [deg/s]
        yaw_rate (float): yaw rate [deg/s]
        mach_number (float): Mach number
        ref_velocity (float): reference upstream velocity [m/s]
        ref_density (float): reference upstream density [kg/m^3]
        g_acceleration (float): gravitational acceleration [m/s^2]
        aileron (float): Aileron angle [deg].
        elevator (float): Elevator angle [deg].
        rudder (float): Rudder angle [deg].
        save_plots (bool): Saving plots condition.

    Returns:
        (Path): Path to the command file.

    """

    command_path = str(case_dir_path) + "/avl_commands.txt"
    pyavl_dir = get_module_path("PyAVL")
    mass_path = Path(pyavl_dir, "files", "template.mass")

    # Get the reference dimensions
    s = tixi.getDoubleElement(REF_XPATH + '/area')
    c = tixi.getDoubleElement(REF_XPATH + '/length')
    b = s / c

    # See https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf
    # for how he non-dimensionalize the rates
    roll_rate_star = roll_rate * b / (2 * ref_velocity)
    pitch_rate_star = pitch_rate * c / (2 * ref_velocity)
    yaw_rate_star = yaw_rate * b / (2 * ref_velocity)

    command = [
        "load " + str(avl_path) + "\n",
        "mass " + str(mass_path) + "\n",
        "oper\n",
        "a a " + str(alpha) + "\n",
        "b b " + str(beta) + "\n",
        "r r " + str(roll_rate_star) + "\n",
        "p p " + str(pitch_rate_star) + "\n",
        "y y " + str(yaw_rate_star) + "\n",
        "d2 d2 " + str(aileron) + "\n",
        "d3 d3 " + str(elevator) + "\n",
        "d4 d4 " + str(rudder) + "\n",
        "m\n",
        "mn " + str(mach_number) + "\n",
        "g " + str(g_acceleration) + "\n",
        "d " + str(ref_density) + "\n",
        "v " + str(ref_velocity) + "\n\n",
    ]

    with open(command_path, "w") as command_file:
        command_file.writelines(command)
        command_file.write("x\n")

        if save_plots:
            command_file.writelines(["t\n", "h\n\n"])
            command_file.writelines(["g\n", "lo\n", "h\n\n"])

        command_file.write("x\n")

        for force_file in ["ft", "fn", "fs", "fe", "st", "sb"]:
            command_file.write(force_file + "\n")
            command_file.write(force_file + ".txt\n")

        command_file.write("\n\n\n")
        command_file.write("quit")

    return Path(command_path)


def get_option_settings(tixi: Tixi3) -> Tuple[bool, float, int, int, bool, float]:
    """
    Reads the settings of CEASIOMpy's graphical user interface.

    Args:
        TODO

    Returns:
        save_plots (bool): Save the geometry and results figures.
        vortex_distribution (float): Distribution of the vortices.
        Nchordwise (int): Number of chordwise vortices.
        Nspanwise (int): Number of spanwise vortices.
        integrate_fuselage (bool): If you add fuselage to geometry.
        rotation_rates_float (float): Rotation rates in deg/s. 

    """

    save_plots = get_value(tixi, AVL_PLOT_XPATH)
    vortex_distribution_gui = get_value(
        tixi, AVL_DISTR_XPATH
    )
    if vortex_distribution_gui == "cosine":
        vortex_distribution = 1.0
    elif vortex_distribution_gui == "sine":
        vortex_distribution = 2.0
    else:
        vortex_distribution = 3.0
    Nchordwise = get_value(tixi, AVL_NCHORDWISE_XPATH)
    Nspanwise = get_value(tixi, AVL_NSPANWISE_XPATH)
    integrate_fuselage = get_value(tixi, AVL_FUSELAGE_XPATH)

    rotation_rates_float = get_value(tixi, AVL_ROTRATES_XPATH)

    return save_plots, vortex_distribution, Nchordwise, Nspanwise, integrate_fuselage, rotation_rates_float

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
