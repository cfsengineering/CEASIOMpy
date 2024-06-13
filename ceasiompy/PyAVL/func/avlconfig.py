"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to get the flight conditions (alt, aoa, mach...) from
the input CPACS file, and write the command file for AVL.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-14

TODO:

    * Things to improve...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    RANGE_XPATH,
    AVL_AEROMAP_UID_XPATH,
    AVL_PLOT_XPATH,
    AVL_VORTEX_DISTR_XPATH,
    AVL_FUSELAGE_XPATH,
)
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================
def write_command_file(
    avl_path,
    case_dir_path,
    alpha,
    beta,
    mach_number,
    ref_velocity,
    ref_density,
    g_acceleration,
    save_plots,
):
    """Function to write the command file for AVL.

    Function 'write_command_file' writes the command file to
    execute for AVL calculations.

    Args:
        avl_path (Path) : path to the AVL input file
        case_dir_path (Path) : path to the run case directory
        alpha (float) : angle of attack [deg]
        beta (float) : angle of attack [deg]
        mach_number (float) : Mach number
        ref_velocity (float) : reference upstream velocity [m/s]
        ref_density (float) : reference upstream density [kg/m^3]
        g_acceleration (float) : gravitational acceleration [m/s^2]

    Returns:
        avl_commands.txt : write the command AVL file.
        command_path (Path) : path to the command file.
    """

    command_path = str(case_dir_path) + "/avl_commands.txt"
    pyavl_dir = get_module_path("PyAVL")
    mass_path = Path(pyavl_dir, "files", "template.mass")

    if save_plots:
        with open(command_path, "w") as command_file:
            command_file.writelines(
                [
                    "load " + str(avl_path) + "\n",
                    "mass " + str(mass_path) + "\n",
                    "oper\n",
                    "g\n",
                    "h\n\n",
                    "a a " + str(alpha) + "\n",
                    "b b " + str(beta) + "\n",
                    "m\n",
                    "mn " + str(mach_number) + "\n",
                    "g " + str(g_acceleration) + "\n",
                    "d " + str(ref_density) + "\n",
                    "v " + str(ref_velocity) + "\n\n",
                ]
            )
            command_file.write("x\n")
            command_file.writelines(["t\n", "h\n\n"])
            command_file.writelines(["g\n", "lo\n", "h\n\n"])
            command_file.write("x\n")
            for force_file in ["ft", "fn", "fs", "fe", "st"]:
                command_file.write(force_file + "\n")
                # command_file.write(str(Path.cwd()) + "/" + force_file + ".txt\n")
                command_file.write(force_file + ".txt\n")
            command_file.write("\n\n\n")
            command_file.write("quit")

    else:  # same without lines saving figures
        with open(command_path, "w") as command_file:
            command_file.writelines(
                [
                    "load " + str(avl_path) + "\n",
                    "mass " + str(mass_path) + "\n",
                    "oper\n",
                    "a a " + str(alpha) + "\n",
                    "b b " + str(beta) + "\n",
                    "m\n",
                    "mn " + str(mach_number) + "\n",
                    "g " + str(g_acceleration) + "\n",
                    "d " + str(ref_density) + "\n",
                    "v " + str(ref_velocity) + "\n\n",
                ]
            )
            command_file.write("x\n")
            for force_file in ["ft", "fn", "fs", "fe", "st"]:
                command_file.write(force_file + "\n")
                command_file.write(str(Path.cwd()) + "/" + force_file + ".txt\n")
            command_file.write("\n\n\n")
            command_file.write("quit")

    with open(command_path, "r") as command_file:
        for line in command_file:
            print(line)

    return Path(command_path)


def get_aeromap_conditions(cpacs_path):
    """Function read the flight conditions from the aeromap.

    Function 'get_aeromap_conditions' reads the flight conditions
    (angle of attack, mach number...) from the aeromap of CEASIOMpy.

    Args:
        cpacs_path (Path) : path to the cpacs input file

    Returns:
        alt_list (list) : altitude of the cases.
        mach_list (list) : mach number of the cases.
        aoa_list (list) : angle of attack of the cases.
        aos_list (list) : angle of sweep of the cases.
    """
    cpacs = CPACS(cpacs_path)

    # Get the first aeroMap as default one or create automatically one
    aeromap_list = cpacs.get_aeromap_uid_list()

    if aeromap_list:
        aeromap_default = aeromap_list[0]
        log.info(f"The aeromap is {aeromap_default}")

        aeromap_uid = get_value_or_default(cpacs.tixi, AVL_AEROMAP_UID_XPATH, aeromap_default)

        activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
        alt_list = activate_aeromap.get("altitude").tolist()
        mach_list = activate_aeromap.get("machNumber").tolist()
        aoa_list = activate_aeromap.get("angleOfAttack").tolist()
        aos_list = activate_aeromap.get("angleOfSideslip").tolist()

    else:
        default_aeromap = cpacs.create_aeromap("DefaultAeromap")
        default_aeromap.description = "AeroMap created automatically"

        mach = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseMach", 0.3)
        alt = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseAltitude", 10000)

        default_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
        default_aeromap.save()

        alt_list = [alt]
        mach_list = [mach]
        aoa_list = [0.0]
        aos_list = [0.0]

        aeromap_uid = get_value_or_default(cpacs.tixi, AVL_AEROMAP_UID_XPATH, "DefaultAeromap")
        log.info(f"{aeromap_uid} has been created")

    cpacs.save_cpacs(cpacs_path, overwrite=True)
    return alt_list, mach_list, aoa_list, aos_list


def get_option_settings(cpacs_path):
    """Function read the setting of the graphical user interface.

    Function 'get_option_settings' reads the setting to use in AVL
    from the graphical user interface of CEASIOMpy.

    Args:
        cpacs_path (Path) : path to the cpacs input file

    Returns:
        save_plots (bool) : to save the geometry and results figures.
        vortex_distribution (float) : distribution of the vortices.
        Nchordwise (int) : number of chordwise vortices.
        Nspanwise (int) : number of spanwise vortices.
    """
    cpacs = CPACS(cpacs_path)

    save_plots = get_value_or_default(cpacs.tixi, AVL_PLOT_XPATH, False)
    vortex_distribution_gui = get_value_or_default(
        cpacs.tixi, AVL_VORTEX_DISTR_XPATH + "/Distribution", "equal"
    )
    if vortex_distribution_gui == "cosine":
        vortex_distribution = 1.0
    elif vortex_distribution_gui == "sine":
        vortex_distribution = 2.0
    else:
        vortex_distribution = 3.0
    Nchordwise = get_value_or_default(cpacs.tixi, AVL_VORTEX_DISTR_XPATH + "/Nchordwise", 5)
    Nspanwise = get_value_or_default(cpacs.tixi, AVL_VORTEX_DISTR_XPATH + "/Nspanwise", 20)
    integrate_fuselage = get_value_or_default(cpacs.tixi, AVL_FUSELAGE_XPATH, False)

    return save_plots, vortex_distribution, Nchordwise, Nspanwise, integrate_fuselage


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
