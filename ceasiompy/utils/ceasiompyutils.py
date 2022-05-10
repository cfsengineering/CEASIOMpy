"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions utils to run ceasiompy workflows

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-02-04

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import importlib
import math
import os
import platform
import shutil
from contextlib import contextmanager
from pathlib import Path

from ceasiompy.SettingsGUI.settingsgui import create_settings_gui
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_submodule_list
from ceasiompy.utils.xpath import AIRCRAFT_NAME_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, open_tixi

log = get_logger()

SOFT_LIST = ["SU2_DEF", "SU2_CFD", "SU2_SOL", "mpirun.mpich", "mpirun"]


# =================================================================================================
#   CLASSES
# =================================================================================================


class SoftwareNotInstalled(Exception):
    """Raised when the a required software is not installed"""

    pass


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@contextmanager
def change_working_dir(working_dir):
    """Context manager to change the working directory just before the execution of a function."""

    try:
        cwd = os.getcwd()
        os.chdir(working_dir)
        yield

    finally:
        os.chdir(cwd)


def get_results_directory(module_name: str) -> Path:
    """Create (if not exists) and return the results directory for a module"""

    if module_name not in get_submodule_list():
        raise ValueError(f"Module '{module_name}' did not exit!")

    specs = importlib.import_module(f"ceasiompy.{module_name}.__specs__")
    results_dir = Path(Path.cwd(), specs.RESULTS_DIR)

    if not results_dir.is_dir():
        results_dir.mkdir(parents=True)

    return results_dir


def run_module(module, wkdir=Path.cwd(), iteration=0):
    """Run a 'ModuleToRun' object in a specific wkdir.

    Args:
        module (ModuleToRun): 'ModuleToRun' object (define in workflowclasses.py)
        wkdir (Path, optional): Path of the working directory. Defaults to Path.cwd().
    """

    log.info("#" * 99)
    log.info("# Run module: " + module.name)
    log.info("#" * 99)

    log.info("Working directory: " + str(wkdir))
    log.info("CPACS input file: " + str(module.cpacs_in))
    log.info("CPACS output file: " + str(module.cpacs_out))

    if module.name == "SettingsGUI":

        create_settings_gui(
            str(module.cpacs_in), str(module.cpacs_out), module.gui_related_modules
        )

    elif module.name == "Optimisation" and iteration > 0:

        log.info("Optimisation module is only run at first iteration!")

    else:

        for file in module.module_dir.iterdir():
            if file.name.endswith(".py") and not file.name.startswith("__"):
                python_file = file.stem

        # Import the main function of the module
        my_module = importlib.import_module(f"ceasiompy.{module.name}.{python_file}")

        # Run the module
        with change_working_dir(wkdir):
            my_module.main(module.cpacs_in, module.cpacs_out)


def get_install_path(software_name: str, raise_error: bool = False) -> Path:
    """Return the installation path of a software.

    Args:
        software_name (str): Name of the software.
        raise_error (bool, optional): If True, raise an error if the software is not installed.

    """

    install_path = shutil.which(software_name)

    if install_path is not None:
        log.info(f"{software_name} is installed at: {install_path}")
        return Path(install_path)

    log.warning(f"{software_name} is not installed on your computer!")

    if raise_error:
        raise SoftwareNotInstalled(f"{software_name} is not installed on your computer!")
    else:
        return None


# TODO make it more genearl, also for sumo and other
def run_soft(software, config_path, wkdir, nb_cpu=1):
    """Function run one of the existing SU2 software

    Function 'run_soft' create the command line to run correctly a SU2 software
    (SU2_DEF, SU2_CFD, SU2_SOL) with MPI (if installed).

    Args:
        software (str): Software to execute (SU2_DEF, SU2_CFD, SU2_SOL)
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    mpi_install_path = get_install_path("mpirun")  # "mpirun.mpich"
    soft_install_path = get_install_path(software)

    log.info(f"{nb_cpu} cpu over {str(os.cpu_count())} will be used for this calculation.")

    logfile_path = Path(wkdir, f"logfile{software}.log")

    command_line = [soft_install_path, config_path, ">", logfile_path]

    if mpi_install_path is not None:
        command_line = [mpi_install_path, "-np", str(int(nb_cpu))] + command_line

    log.info(f">>> Running {software} on {nb_cpu} cpu(s)")
    log.info(f"    from {wkdir}")

    with change_working_dir(wkdir):
        os.system(" ".join(map(str, command_line)))

    log.info(f">>> {software} End")

    # TODO: try to use subprocess instead of os.system, how to deal with log file...?
    # import subprocess
    # p = subprocess.Popen(command_line, stdout=subprocess.PIPE)
    # log_lines = p.communicate()[0]
    # logfile = open(logfile_path, 'w')
    # logfile.writelines(log_lines)
    # logfile.close()


def aircraft_name(tixi_or_cpacs):
    """The function get the name of the aircraft from the cpacs file or add a
        default one if non-existant.

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns:
        name (str): Name of the aircraft.
    """

    # TODO: MODIFY this function, temporary it could accept a cpacs path or tixi handle
    # check xpath
    # *modify corresponding test

    if isinstance(tixi_or_cpacs, Path):
        tixi = open_tixi(str(tixi_or_cpacs))
    else:
        tixi = tixi_or_cpacs

    name = get_value_or_default(tixi, AIRCRAFT_NAME_XPATH, "Aircraft")

    name = name.replace(" ", "_")
    log.info(f"The name of the aircraft is : {name}")

    return name


def get_part_type(cpacs_path, part_uid):
    """The function get the type of the aircraft from the cpacs file.

    Args:
        cpacs_path (str): Path to the CPACS file
        part_uid (str): UID of the part

    Returns:
        part_type (str): Type of the part.
    """
    tixi = open_tixi(str(cpacs_path))

    # split uid if mirrored part
    part_uid = part_uid.split("_mirrored")[0]
    part_xpath = tixi.uIDGetXPath(part_uid)

    if "wings/wing" in part_xpath:
        log.info(f"'{part_uid}' is a wing")
        return "wing"

    if "fuselages/fuselage" in part_xpath:
        log.info(f"'{part_uid}' is a fuselage")
        return "fuselage"

    if "enginePylons/enginePylon" in part_xpath:
        log.info(f"'{part_uid}' is a pylon")
        return "pylon"

    # TODO: complete when engine/flaps are available with TiGL

    log.warning(f"'{part_uid}' cannot be categorized!")
    return None


def get_reasonable_nb_cpu():
    """Get a reasonable number of processors depending on the total number of processors on
    the host machine. Approximately 1/4 of the total number of processors will be used.
    This function is generally used to set up a default value for the number of processors,
    the user can then override this value with the settings."""

    cpu_count = os.cpu_count()

    if cpu_count is None:
        return 1

    return math.ceil(cpu_count / 4)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
