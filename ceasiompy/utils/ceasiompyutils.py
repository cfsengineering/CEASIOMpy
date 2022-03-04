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


import platform
import ceasiompy.__init__

import os
import shutil
import importlib
from pathlib import Path
from contextlib import contextmanager

from cpacspy.cpacsfunctions import get_value_or_default, open_tixi
from ceasiompy.SettingsGUI.settingsgui import create_settings_gui
from ceasiompy.utils.moduleinterfaces import (
    get_submodule_list,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.xpath import WKDIR_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

SOFT_LIST = ["SU2_DEF", "SU2_CFD", "SU2_SOL", "mpirun.mpich", "mpirun"]


# =================================================================================================
#   CLASSES
# =================================================================================================


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


# TODO: will be removed when not used anymore in optimisation.py
def copy_module_to_module(module_from, io_from, module_to, io_to):
    """Transfer CPACS file from one module to another.

    Function 'copy_module_to_module' copy the CPACS file form ToolInput or
    ToolOutput of 'module_from' to ToolInput or ToolOutput of 'module_to'

    Args:
        module_from (str): Name of the module the CPACS file is copy from
        io_from (str): "in" or "out", for ToolInput or ToolOutput
        module_to (str): Name of the module where the CPACS file will be copy
        io_to (str): "in" or "out", for ToolInput or ToolOutput

    """

    in_list = ["in", "In", "IN", "iN", "input", "Input", "INPUT", "ToolInput", "toolinput"]

    if io_from in in_list:
        file_copy_from = get_toolinput_file_path(module_from)
    else:  # 'out' or anything else ('out' by default)
        file_copy_from = get_tooloutput_file_path(module_from)
    log.info("Copy CPACS from:" + file_copy_from)

    if io_to in in_list:
        file_copy_to = get_toolinput_file_path(module_to)
    else:  # 'out' or anything else ('out' by default)
        file_copy_to = get_tooloutput_file_path(module_to)

    log.info("Copy CPACS to:" + file_copy_to)

    shutil.copy(file_copy_from, file_copy_to)


def run_module(module, wkdir=Path.cwd(), iter=0):
    """Run a 'ModuleToRun' ojbect in a specific wkdir.

    Args:
        module (ModuleToRun): 'ModuleToRun' ojbect (define in workflowclasses.py)
        wkdir (Path, optional): Path of the working directory. Defaults to Path.cwd().
    """

    log.info("###############################################################################")
    log.info("# Run module: " + module.name)
    log.info("###############################################################################")

    log.info("Working directory: " + str(wkdir))
    log.info("CPACS input file: " + str(module.cpacs_in))
    log.info("CPACS output file: " + str(module.cpacs_out))

    if module.name == "SettingsGUI":

        create_settings_gui(
            str(module.cpacs_in), str(module.cpacs_out), module.gui_related_modules
        )

    elif module.name == "Optimisation" and iter > 0:

        log.info("Optimisation module is only run at first iteration!")

    else:

        for file in module.module_dir.iterdir():
            if file.name.endswith(".py") and not file.name.startswith("__"):
                python_file = file.stem

        # Import the main function of the module
        my_module = importlib.import_module(f"ceasiompy.{module.name}.{python_file}")

        # Run the module
        with change_working_dir(wkdir):
            my_module.main(str(module.cpacs_in), str(module.cpacs_out))


# TODO: will be remove when not used anymore in optimisation.py
def run_subworkflow(module_to_run, cpacs_path_in="", cpacs_path_out=""):
    """Function to run a list of module in order.

    Function 'run_subworkflow' will exectute in order all the module contained
    in 'module_to_run' list. Every time the resuts of one module (generaly CPACS
    file) will be copied as input for the next module.

    Args:
        module_to_run (list): List of mododule to run (in order)
        cpacs_path_in (str): Path of the CPACS file use, if not already in the
                             ToolInput folder of the first submodule
        cpacs_path_out (str): Path of the output CPACS file use, if not already
                              in the ToolInput folder of the first submodule

    """

    if not module_to_run:
        log.info("No module to run")
        return 0

    # Check non existing module
    submodule_list = get_submodule_list()
    for module in module_to_run:
        if module not in submodule_list:
            raise ValueError(f"No module named '{module}'!")

    # Copy the cpacs file in the first module
    if cpacs_path_in:
        shutil.copy(cpacs_path_in, get_toolinput_file_path(module_to_run[0]))

    log.info("The following modules will be executed: ")
    for module in module_to_run:
        log.info(module)

    for m, module in enumerate(module_to_run):

        log.info(
            "#####################################################################################"
        )
        log.info("Run module: " + module)
        log.info(
            "#####################################################################################"
        )

        # Go to the module directory
        module_path = Path(Path(LIB_DIR), module)

        # Copy CPACS file from previous module to this one
        if m > 0:
            copy_module_to_module(module_to_run[m - 1], "out", module, "in")

        if module == "SettingsGUI":
            cpacs_in = get_toolinput_file_path(module)
            cpacs_out = get_tooloutput_file_path(module)

            # Check if there is at least one other 'SettingsGUI' after this one
            if "SettingsGUI" in module_to_run[m + 1 :] and m + 1 != len(module_to_run):
                idx = module_to_run.index("SettingsGUI", m + 1)
                create_settings_gui(cpacs_in, cpacs_out, module_to_run[m:idx])
            else:
                create_settings_gui(cpacs_in, cpacs_out, module_to_run[m:])
        else:
            # Find the python file to run
            # for file in os.listdir(module_path):
            #     if file.endswith(".py"):
            #         if not file.startswith("__"):
            #             main_python = file

            # Run the module
            # print(os.getcwd())
            # error = subprocess.call(["python", main_python])

            # if error:
            #     raise ValueError("An error ocured in the module " + module)

            # Run the module
            for file in module_path.iterdir():
                if file.name.endswith(".py") and not file.name.startswith("__"):
                    python_file = file.stem

            # Import the main function of the module
            my_module = importlib.import_module(f"ceasiompy.{module}.{python_file}")

            wkdir = get_results_directory("Optimisation")
            # Run the module
            with change_working_dir(wkdir):
                my_module.main(str(cpacs_in), str(cpacs_out))

    # Copy the cpacs file in the first module
    if cpacs_path_out:
        shutil.copy(get_tooloutput_file_path(module_to_run[-1]), cpacs_path_out)


def get_install_path(soft_check_list):
    """Function to get installation paths a sorfware used in SU2

    Function 'get_instal_path' check if the given list of software is installed,
    it retruns a dictionnay of software with thier intallation paths.

    Args:
        soft_check_list (list): List of software to check installation path

    Returns:
        soft_dict (dict): Dictionary of software with their installation path

    """

    current_os = platform.system()

    soft_dict = {}

    for soft in soft_check_list:

        # TODO: Check more and improve
        if current_os == "Darwin":
            log.info("Your OS is Mac")
            # Run with MPICH not implemeted yet on mac
            if "mpi" in soft:
                install_path = ""
            else:
                install_path = "/Applications/SU2/" + soft

        elif current_os == "Linux":
            log.info("Your OS is Linux")
            install_path = shutil.which(soft)

        elif current_os == "Windows":
            log.info("Your OS is Windows")
            # TODO

        else:
            raise OSError("OS not recognized!")

        if install_path:
            log.info(soft + " is installed at: " + install_path)
            soft_dict[soft] = install_path
        elif "mpi" in soft:
            log.warning(soft + " is not installed on your computer!")
            log.warning("Calculations will be run on 1 proc only")
            soft_dict[soft] = None
        else:
            raise RuntimeError(soft + " is not installed on your computer!")

    return soft_dict


# TODO make it more genearl, also for sumo and other
def run_soft(soft, config_path, wkdir, nb_proc):
    """Function run one of the existing SU2 software

    Function 'run_soft' create the comment line to run correctly a SU2 software
    (SU2_DEF, SU2_CFD, SU2_SOL) with MPI (if installed). The SOFT_DICT is
    create from the SOFT_LIST define at the top of this script.

    Args:
        soft (str): Software to execute (SU2_DEF, SU2_CFD, SU2_SOL)
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    # Get installation path for the following softwares
    SOFT_DICT = get_install_path(SOFT_LIST)

    # mpi_install_path = SOFT_DICT['mpirun.mpich']
    mpi_install_path = SOFT_DICT["mpirun"]

    soft_install_path = SOFT_DICT[soft]

    log.info("Number of proc available: " + str(os.cpu_count()))
    log.info(str(nb_proc) + " will be used for this calculation.")

    logfile_path = os.path.join(wkdir, "logfile" + soft + ".log")

    # if mpi_install_path is not None:
    #     command_line =  [mpi_install_path,'-np',str(nb_proc),
    #                      soft_install_path,config_path,'>',logfile_path]

    if mpi_install_path is not None:
        command_line = [
            mpi_install_path,
            "-np",
            str(int(nb_proc)),
            soft_install_path,
            config_path,
            ">",
            logfile_path,
        ]
    # elif soft == 'SU2_DEF' a disp.dat must be there to run with MPI
    else:
        command_line = [soft_install_path, config_path, ">", logfile_path]

    log.info(f">>> Running {soft} on {nb_proc} proc")
    log.info(f"    from {wkdir}")

    with change_working_dir(wkdir):
        os.system(" ".join(command_line))

    log.info(f">>> {soft} End")

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

    # TODO: MODIFY this funtion, temporary it could accept a cpacs path or tixi handle
    # check xpath
    # *modify corresponding test

    if isinstance(tixi_or_cpacs, str):

        tixi = open_tixi(tixi_or_cpacs)

        aircraft_name_xpath = "/cpacs/header/name"
        name = get_value_or_default(tixi, aircraft_name_xpath, "Aircraft")

        tixi.save(tixi_or_cpacs)

    else:

        aircraft_name_xpath = "/cpacs/header/name"
        name = get_value_or_default(tixi_or_cpacs, aircraft_name_xpath, "Aircraft")

    name = name.replace(" ", "_")
    log.info("The name of the aircraft is : " + name)

    return name


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
