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
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
import sys
from typing import List
from ceasiompy.SettingsGUI.settingsgui import create_settings_gui
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_submodule_list
from ceasiompy.utils.commonxpath import AIRCRAFT_NAME_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, open_tixi

log = get_logger()

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

        # Import the main function from the module
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


def run_software(
    software_name: str, arguments: List[str], wkdir: Path, with_mpi: bool = False, nb_cpu: int = 1
) -> None:
    """Run a software with the given arguments in a specific wkdir. If the software is compatible
    with MPI, 'with_mpi' can be set to True and the number of processors can be specified. A
    logfile will be created in the wkdir.

    Args:
        software_name (str): Name of the software to run.
        arguments (str): Arguments to pass to the software.
        wkdir (Path): Working directory where the software will be run.
        with_mpi (bool, optional): If True, run the software with MPI. Defaults to False.
        nb_cpu (int, optional): Number of processors to use. Defaults to 1. If with_mpi is True,

    """

    log.info(f"{int(nb_cpu)} cpu over {os.cpu_count()} will be used for this calculation.")

    logfile = Path(wkdir, f"logfile_{software_name}.log")
    install_path = get_install_path(software_name)

    command_line = []
    if with_mpi:
        mpi_install_path = get_install_path("mpirun")  # "mpirun.mpich"
        if mpi_install_path is not None:
            command_line += [mpi_install_path, "-np", str(int(nb_cpu))]

    command_line += [install_path]
    command_line += arguments

    # Use xvfb to run sumo to avoid problems with X11 (e.g. when running test on Github actions)
    if software_name in ["sumo", "dwfsumo"] and sys.platform == "linux":
        command_line = ["xvfb-run"] + command_line

    log.info(f">>> Running {software_name} on {int(nb_cpu)} cpu(s)")
    log.info(f"Working directory: {wkdir}")
    log.info(f"Logfile: {logfile}")
    log.info("Command line that will be run is:")
    log.info(" ".join(map(str, command_line)))

    with change_working_dir(wkdir):
        with open(logfile, "w") as logfile:
            subprocess.call(command_line, stdout=logfile)

    log.info(f">>> {software_name} End")


def get_reasonable_nb_cpu() -> int:
    """Get a reasonable number of processors depending on the total number of processors on
    the host machine. Approximately 1/4 of the total number of processors will be used.
    This function is generally used to set up a default value for the number of processors,
    the user can then override this value with the settings."""

    cpu_count = os.cpu_count()

    if cpu_count is None:
        return 1

    return math.ceil(cpu_count / 4)


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
        tixi = open_tixi(tixi_or_cpacs)
    else:
        tixi = tixi_or_cpacs

    name = get_value_or_default(tixi, AIRCRAFT_NAME_XPATH, "Aircraft")

    name = name.replace(" ", "_")
    log.info(f"The name of the aircraft is : {name}")

    return name


def get_part_type(tixi, part_uid: str) -> str:
    """The function get the type of the aircraft from the cpacs file.

    Args:
        cpacs_path (Path): Path to the CPACS file
        part_uid (str): UID of the part

    Returns:
        part_type (str): Type of the part.

    """

    # split uid if mirrored part
    part_uid = part_uid.split("_mirrored")[0]
    part_xpath = tixi.uIDGetXPath(part_uid)

    if "wings/wing" in part_xpath:
        log.info(f"'{part_uid}' is a wing")
        return "wing"

    elif "fuselages/fuselage" in part_xpath:
        log.info(f"'{part_uid}' is a fuselage")
        return "fuselage"

    elif "enginePylons/enginePylon" in part_xpath:
        log.info(f"'{part_uid}' is a pylon")
        return "pylon"

    elif "engine/nacelle/fanCowl" in part_xpath:
        log.info(f"'{part_uid}' is a fanCowl")
        return "fanCowl"

    elif "engine/nacelle/centerCowl" in part_xpath:
        log.info(f"'{part_uid}' is a centerCowl")
        return "centerCowl"

    elif "engine/nacelle/coreCowl" in part_xpath:
        log.info(f"'{part_uid}' is a coreCowl")
        return "coreCowl"

    elif "vehicles/engines/engine" in part_xpath:
        log.info(f"'{part_uid}' is an engine")
        return "engine"

    elif "vehicles/rotorcraft/model/rotors/rotor" in part_xpath:
        log.info(f"'{part_uid}' is an rotor")
        return "rotor"

    log.warning(f"'{part_uid}' cannot be categorized!")
    return None


def remove_file_type_in_dir(directory: Path, file_type_list: List[str]) -> None:
    """Remove all files of a given type in a directory.

    Args:
        directory (Path): Path to the directory
        file_type_list (List[str]): List of file types to remove.

    """

    if not directory.exists():
        raise FileNotFoundError(f"The directory {directory} does not exist!")

    for file in directory.iterdir():
        if not file.is_file():
            continue
        if file.suffix in file_type_list:
            file.unlink()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
