"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to get the flight conditions (alt, aoa, mach...) from
the input CPACS file, and write the command file for AVL.
More details at: https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf.
"""

# Imports

from pydantic import validate_call
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import (
    has_display,
    get_selected_aeromap_values,
)
from ceasiompy.utils.mathsfunctions import non_dimensionalize_rate
from ceasiompy.PyAVL.func.utils import (
    get_atmospheric_cond,
    practical_limit_rate_check,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.PyAVL.func.cpacs2avl import Avl

from ceasiompy import (
    log,
    ceasiompy_cfg,
)
from ceasiompy.PyAVL import MODULE_DIR
from ceasiompy.PyAVL.func import FORCE_FILES
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    LENGTH_XPATH,
)
from ceasiompy.PyAVL import (
    AVL_ROTRATES_XPATH,
    # AVL_EXPAND_VALUES_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)


# Functions

@validate_call(config=ceasiompy_cfg)
def retrieve_gui_values(cpacs: CPACS, results_dir: Path) -> tuple[
    list, list, list, list,
    list, list,
    Path,
    bool, int, bool,
]:
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_selected_aeromap_values(cpacs)

    rotation_rates_float = get_value(tixi, AVL_ROTRATES_XPATH)
    control_surface_float = get_value(tixi, AVL_CTRLSURF_ANGLES_XPATH)

    # Convert to lists
    rotation_rates_list = [float(x) for x in str(rotation_rates_float).split(";")]
    control_surface_list = [float(x) for x in str(control_surface_float).split(";")]

    avl_file = Avl(tixi, results_dir)
    avl_path = avl_file.convert_cpacs_to_avl()
    expand = False  # get_value(tixi, AVL_EXPAND_VALUES_XPATH)

    practical_limit_rate_check(
        tixi=tixi,
        alt_list=alt_list,
        mach_list=mach_list,
        rotation_rates_list=rotation_rates_list,
    )

    return (
        alt_list, mach_list, aoa_list, aos_list,
        rotation_rates_list, control_surface_list,
        avl_path, expand,
    )


def get_physics_conditions(
    tixi: Tixi3,
    alt: float,
    mach: float,
    roll_rate: float,
    pitch_rate: float,
    yaw_rate: float,
) -> tuple[float, float, float, float, float, float]:
    # Get the reference dimensions
    s = tixi.getDoubleElement(AREA_XPATH)
    c = tixi.getDoubleElement(LENGTH_XPATH)
    b = s / c

    ref_density, g_acceleration, ref_velocity = get_atmospheric_cond(alt, mach)

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

    return (
        roll_rate_star, pitch_rate_star, yaw_rate_star,
        ref_density, g_acceleration, ref_velocity,
    )


def write_command_file(
    avl_path: Path,
    case_dir_path: Path,
    ref_density: float,
    g_acceleration: float,
    ref_velocity: float,
    mach_number: float,
    alpha: float,
    beta: float = 0.0,
    pitch_rate_star: float = 0.0,
    roll_rate_star: float = 0.0,
    yaw_rate_star: float = 0.0,
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

    command_path = str(case_dir_path) + "/avl_commands.txt"

    # Retrieve template file for mass
    mass_path = Path(MODULE_DIR, "files", "template.mass")

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

        if has_display():
            command_file.writelines(["t\n", "h\n\n"])
            command_file.writelines(["g\n", "lo\n", "h\n\n"])
        else:
            log.info("No Display available, can not generate plot.ps file.")

        command_file.write("x\n")

        for force_file in FORCE_FILES:
            command_file.write(force_file + "\n")
            command_file.write(force_file + ".txt\n")

        command_file.write("\n\n\n")
        command_file.write("quit")

    return Path(command_path)
