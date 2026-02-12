"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to get the flight conditions (alt, aoa, mach...) from
the input CPACS file, and write the command file for AVL.
More details at: https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf.
"""

# Imports
import os

from pydantic import validate_call
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import (
    has_display,
    get_selected_aeromap_values,
)
from ceasiompy.pyavl.func.data import create_case_dir
from ceasiompy.pyavl.func.utils import (
    practical_limit_rate_check,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.pyavl.func.data import AVLData
from ceasiompy.pyavl.func.cpacs2avl import Avl

from ceasiompy import (
    log,
    ceasiompy_cfg,
)
from ceasiompy.pyavl.func import FORCE_FILES
from ceasiompy.pyavl import (
    MODULE_DIR,
    AVL_ROTRATES_XPATH,
    # AVL_EXPAND_VALUES_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)


# Functions

@validate_call(config=ceasiompy_cfg)
def retrieve_gui_values(cpacs: CPACS, results_dir: Path) -> tuple[
    list, list, list, list,
    list, list,
    Path, bool,
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


def get_command_path(from_case_dir: Path) -> Path:
    return from_case_dir / "avl_commands.txt"


def write_command_file(
    i_case: int,
    avl_path: Path,
    avl_data: AVLData,
    results_dir: Path,
) -> Path:
    """
    Writes the command file for AVL.

    Returns:
        (Path): case_dir_path.
    """

    dynamic_case_params = {
        "q": avl_data.q,
        "p": avl_data.p,
        "r": avl_data.r,
        "aileron": avl_data.aileron,
        "elevator": avl_data.elevator,
        "rudder": avl_data.rudder,
    }
    non_zero_case_params = {
        key: value for key, value in dynamic_case_params.items() if abs(value) > 1e-12
    }

    case_dir_path = create_case_dir(
        i_case=i_case,
        avl_data=avl_data,
        results_dir=results_dir,
        **non_zero_case_params,
    )

    command_path = get_command_path(case_dir_path)

    avl_path = Path(avl_path).resolve()
    case_dir_path = Path(case_dir_path).resolve()
    avl_path_for_cmd = Path(os.path.relpath(avl_path, case_dir_path))

    # Retrieve template file for mass
    mass_path = Path(MODULE_DIR, "files", "template.mass")

    command = [
        "load " + str(avl_path_for_cmd) + "\n",
        "mass " + str(mass_path) + "\n",
        "oper\n",
        "a a " + str(avl_data.alpha) + "\n",
        "b b " + str(avl_data.beta) + "\n",
        "r r " + str(avl_data.p_star) + "\n",
        "p p " + str(avl_data.q_star) + "\n",
        "y y " + str(avl_data.r_star) + "\n",
        "d2 d2 " + str(avl_data.aileron) + "\n",
        "d3 d3 " + str(avl_data.elevator) + "\n",
        "d4 d4 " + str(avl_data.rudder) + "\n",
        "m\n",
        "mn " + str(avl_data.mach) + "\n",
        "g " + str(avl_data.g_acceleration) + "\n",
        "d " + str(avl_data.ref_density) + "\n",
        "v " + str(avl_data.ref_velocity) + "\n\n",
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

    return Path(case_dir_path)
