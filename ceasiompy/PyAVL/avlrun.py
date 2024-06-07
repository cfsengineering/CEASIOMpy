"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run AVL calculations in CEASIOMpy.
AVL allows to perform aerodynamic analyses using
the vortex-lattice method (VLM)

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-14

TODO:

    * Things to improve ...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.PyAVL.func.cpacs2avl import convert_cpacs_to_avl
from ceasiompy.PyAVL.func.avlconfig import (
    write_command_file,
    get_aeromap_conditions,
    get_option_settings,
)
from ceasiompy.PyAVL.func.avlresults import get_avl_results
from ceasiompy.utils.ceasiompyutils import get_results_directory

import subprocess
from pathlib import Path
from ambiance import Atmosphere


log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================
def run_avl(cpacs_path, wkdir):
    """Function to run AVL.

    Function 'run_avl' runs AVL calculations using a CPACS file
    as input.

    Args:
        cpacs_path (Path) : path to the CPACS input  file
        wkdir (Path) : path to the working directory
    """

    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(cpacs_path)
    save_fig, _, _, _, _ = get_option_settings(cpacs_path)

    for i_case in range(len(alt_list)):
        alt = alt_list[i_case]
        mach = mach_list[i_case]
        aoa = aoa_list[i_case]
        aos = aos_list[i_case]
        Atm = Atmosphere(alt)

        density = Atm.density[0]
        velocity = Atm.speed_of_sound[0] * mach
        g = Atm.grav_accel[0]

        case_dir_name = (
            f"Case{str(i_case).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
        )

        Path(wkdir, case_dir_name).mkdir(exist_ok=True)
        case_dir_path = Path(wkdir, case_dir_name)

        avl_path = convert_cpacs_to_avl(cpacs_path, wkdir=case_dir_path)

        command_path = write_command_file(
            avl_path,
            case_dir_path,
            save_plots=save_fig,
            alpha=aoa,
            beta=aos,
            mach_number=mach,
            ref_velocity=velocity,
            ref_density=density,
            g_acceleration=g,
        )
        subprocess.run(["xvfb-run", "avl"], stdin=open(str(command_path), "r"), cwd=case_dir_path)

        if save_fig:
            # Convert plot.ps to plot.pdf and remove plot.ps
            subprocess.run(["ps2pdf", "plot.ps", "plot.pdf"], cwd=case_dir_path)
            subprocess.run(["rm", "plot.ps"], cwd=case_dir_path)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    results_dir = get_results_directory(module_name="PyAVL")
    run_avl(cpacs_path, wkdir=results_dir)

    get_avl_results(cpacs_path, cpacs_out_path, wkdir=results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
