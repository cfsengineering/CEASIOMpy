"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to get the flight conditions (alt, aoa, mach...) from
the input CPACS file, and write the command file for AVL.
More details at: https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf.


| Author: Romain Gauthier
| Creation: 2024-03-14
| Modified: Leon Deligny
| Date: 11-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pydantic import validate_call
from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.func.utils import get_atmospheric_cond
from ceasiompy.utils.mathsfunctions import non_dimensionalize_rate
from ceasiompy.utils.ceasiompyutils import (
    bool_,
    get_aeromap_conditions,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.PyAVL.func.cpacs2avl import Avl
from typing import (
    List,
    Tuple,
)

from ceasiompy import log, ceasiompy_cfg
from ceasiompy.PyAVL import MODULE_DIR
from ceasiompy.PyAVL.func import FORCE_FILES
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    LENGTH_XPATH,
)
from ceasiompy.PyAVL import (
    AVL_PLOT_XPATH,
    AVL_NB_CPU_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_AEROMAP_UID_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@validate_call(config=ceasiompy_cfg)
def retrieve_gui_values(cpacs: CPACS, results_dir: Path) -> Tuple[
    List, List, List, List,
    List, List,
    Path, bool,
    int,
]:
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(cpacs, AVL_AEROMAP_UID_XPATH)

    save_fig = bool_(get_value(tixi, AVL_PLOT_XPATH))
    rotation_rates_float = get_value(tixi, AVL_ROTRATES_XPATH)
    control_surface_float = get_value(tixi, AVL_CTRLSURF_ANGLES_XPATH)

    # Convert to lists
    rotation_rate_list = [float(x) for x in str(rotation_rates_float).split(';')]
    control_surface_list = [float(x) for x in str(control_surface_float).split(';')]

    avl_file = Avl(tixi, results_dir)
    avl_path = avl_file.convert_cpacs_to_avl()

    nb_cpu = int(get_value(tixi, AVL_NB_CPU_XPATH))

    return (
        alt_list, mach_list, aoa_list, aos_list,
        rotation_rate_list, control_surface_list,
        avl_path,
        save_fig,
        nb_cpu,
    )


def write_command_file(
    tixi: Tixi3,
    avl_path: Path,
    case_dir_path: Path,
    save_plots: bool,
    alt: float,
    mach_number: float,
    alpha: float,
    beta: float = 0.0,
    pitch_rate: float = 0.0,
    roll_rate: float = 0.0,
    yaw_rate: float = 0.0,
    aileron: float = 0.0,
    elevator: float = 0.0,
    rudder: float = 0.0,
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
        alt (float): Altitude.
        aileron (float): Aileron angle [deg].
        elevator (float): Elevator angle [deg].
        rudder (float): Rudder angle [deg].
        save_plots (bool): Saving plots condition.

    Returns:
        (Path): Path to the command file.

    """

    ref_density, g_acceleration, ref_velocity = get_atmospheric_cond(alt, mach_number)

    command_path = str(case_dir_path) + "/avl_commands.txt"

    # Retrieve template file for mass
    mass_path = Path(MODULE_DIR, "files", "template.mass")

    # Get the reference dimensions
    s = tixi.getDoubleElement(AREA_XPATH)
    c = tixi.getDoubleElement(LENGTH_XPATH)
    b = s / c

    # See https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf
    # for how he non-dimensionalize the rates
    roll_rate_star, pitch_rate_star, yaw_rate_star = non_dimensionalize_rate(
        p=roll_rate,
        q=pitch_rate,
        r=yaw_rate,
        v=ref_velocity,
        b=b,
        c=c,
    )

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

        for force_file in FORCE_FILES:
            command_file.write(force_file + "\n")
            command_file.write(force_file + ".txt\n")

        command_file.write("\n\n\n")
        command_file.write("quit")

    return Path(command_path)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
