"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions and classes to run ceasiompy workflows

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-10-04

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import ceasiompy.__init__

import os
import shutil
import datetime
import platform
import importlib
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager

from cpacspy.cpacsfunctions import create_branch, get_value_or_default, open_tixi
from ceasiompy.SettingsGUI.settingsgui import create_settings_gui
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.moduleinterfaces import get_submodule_list
from ceasiompy.utils.xpath import WKDIR_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = Path(ceasiompy.__init__.__file__).parent

SOFT_LIST = ["SU2_DEF", "SU2_CFD", "SU2_SOL", "mpirun.mpich", "mpirun"]

OPTIM_METHOD = ["OPTIM", "DOE"]

# =================================================================================================
#   CLASSES
# =================================================================================================


@dataclass
class ModuleToRun:

    module_name: str
    wkflow_dir: Path
    cpacs_in: Path
    cpacs_out: Path = None

    def __post_init__(self) -> None:

        # Check if the module is valid
        if self.module_name not in get_submodule_list():
            raise ValueError(f"Module '{self.module_name}' did not exit!")

        # Set module path
        self.module_path = Path.joinpath(LIB_DIR, self.module_name)

        # Check if the workflow directory exist
        if not self.wkflow_dir.exists():
            raise FileNotFoundError(f"{str(self.wkflow_dir)} did not exist!")

        # Set default values
        self.is_settinggui = False
        self.inculde_in_optim = False
        self.optim_method = None

    def define_settinggui(self, related_module: list) -> None:

        self.is_settinggui = True
        self.related_module = related_module

    def define_optim_module(self, optim_method) -> None:

        if optim_method not in OPTIM_METHOD:
            raise ValueError(
                f"Not recognize optim_method! It must be test {' or '.join(OPTIM_METHOD)}"
            )

        self.optim_method = optim_method
        self.inculde_in_optim = True

    def create_module_wkflow_dir(self, cnt: int) -> None:

        if self.inculde_in_optim and self.optim_method:  # HERE <------
            module_wkflow_name = (
                str(cnt).rjust(2, "0") + "_" + self.optim_method + "_" + self.module_name
            )
        else:

            module_wkflow_name = str(cnt).rjust(2, "0") + "_" + self.module_name

        self.module_wkflow_path = Path.joinpath(self.wkflow_dir, module_wkflow_name)
        self.module_wkflow_path.mkdir()

        self.cpacs_out = Path.joinpath(self.module_wkflow_path, "ToolOutput.xml")

    def run(self, wkdir: Path = Path.cwd()) -> None:

        log.info("###############################################################################")
        log.info("# Run module: " + self.module_name)
        log.info("###############################################################################")

        if self.module_name == "SettingsGUI":

            create_settings_gui(str(self.cpacs_in), str(self.cpacs_out), self.related_module)

        else:

            for file in self.module_path.iterdir():
                if file.name.endswith(".py") and not file.name.startswith("__"):
                    python_file = file.stem

            # Import the main function of the module
            my_module = importlib.import_module(f"ceasiompy.{self.module_name}.{python_file}")

            # Run the module
            with change_working_dir(wkdir):
                my_module.main(str(self.cpacs_in), str(self.cpacs_out))


class Workflow:
    """Class to pass options of the workflow"""

    def __init__(self):

        self.working_dir = ""
        self.cpacs_path = Path("../test_files/CPACSfiles/D150_simple.xml").resolve()
        self.current_workflow_dir = None

        self.module_to_run = []
        self.module_to_run_obj = []

        self.optim_method = None
        self.module_optim = []

    def from_config_file(self, cfg_file: str) -> None:
        """Get parameters from a config file

        Args:
            cfg_file (str): Configuration file path
        """

        cfg = ConfigFile(cfg_file)

        self.working_dir = Path(cfg_file).parent.absolute()
        self.cpacs_path = Path(cfg["CPACS_TOOLINPUT"])

        try:
            self.module_to_run = cfg["MODULE_TO_RUN"]
        except KeyError:
            pass

        try:
            self.module_optim = cfg["MODULE_OPTIM"]
        except KeyError:
            pass

        try:
            self.optim_method = cfg["OPTIM_METHOD"]
        except KeyError:
            pass

    def write_config_file(self) -> None:
        """Write the workflow configuration file in the working directory."""

        cfg = ConfigFile()
        cfg["comment_1"] = f"File written {datetime.datetime.now()}"
        cfg["CPACS_TOOLINPUT"] = self.cpacs_path

        if self.module_to_run:
            cfg["MODULE_TO_RUN"] = self.module_to_run
        else:
            cfg["comment_module_to_run"] = "MODULE_TO_RUN = (  )"

        if self.module_optim:
            cfg["MODULE_OPTIM"] = self.module_optim
            cfg["OPTIM_METHOD"] = self.optim_method
        else:
            cfg["comment_module_optim"] = "MODULE_OPTIM = (  )"
            cfg["comment_optim_method"] = "OPTIM_METHOD = NONE"

        cfg_file = os.path.join(self.working_dir, "ceasiompy.cfg")
        cfg.write_file(cfg_file, overwrite=True)

    def set_workflow(self) -> None:
        """Create the directory structure and set input/output of each modules"""

        if not self.working_dir:
            raise ValueError("You must first define a working directory!")

        wkdir = self.working_dir
        os.chdir(wkdir)

        # Check index of the last workflow directory to set the next one
        wkflow_list = [int(dir.stem.split("_")[-1]) for dir in wkdir.glob("Workflow_*")]
        if wkflow_list:
            wkflow_idx = str(max(wkflow_list) + 1).rjust(3, "0")
        else:
            wkflow_idx = "001"

        self.current_wkflow_dir = Path.joinpath(wkdir, "Workflow_" + wkflow_idx)
        self.current_wkflow_dir.mkdir()

        # Copy CPACS to the workflow dir
        if not self.cpacs_path.exists():
            raise FileNotFoundError(f"{self.cpacs_path} has not been found!")

        wkflow_cpacs_in = Path.joinpath(self.current_wkflow_dir, "00_ToolInput.xml").absolute()

        shutil.copy(self.cpacs_path, wkflow_cpacs_in)

        # Create the directory structure for each mudule in the wokrflow and its corresponding obj
        cnt = 1

        for m, module_name in enumerate(self.module_to_run):

            # Check if it is the first module (to know where the cpacs input file should come from)
            if m == 0:
                cpacs_in = wkflow_cpacs_in
            else:
                cpacs_in = self.module_to_run_obj[m - 1].cpacs_out

            # Create an object for the module
            module_obj = ModuleToRun(module_name, self.current_wkflow_dir, cpacs_in)

            # Check if the module is SettingGUI
            related_modules = []
            if module_name == "SettingsGUI":
                related_modules = self.get_related_modules(self.module_to_run, m)
                module_obj.define_settinggui(related_modules)

            # Check if should be included in Optim/DoE
            if self.optim_method and module_name in self.module_optim:
                module_obj.define_optim_module(self.optim_method)

            module_obj.create_module_wkflow_dir(cnt)
            self.module_to_run_obj.append(module_obj)
            cnt += 1

        # Create Results directory
        new_res_dir = Path.joinpath(self.current_wkflow_dir, "Results")
        new_res_dir.mkdir()

    def run_workflow(self) -> None:
        """Run the complete Worflow"""

        log.info(f"Running the workflow in {self.current_wkflow_dir}")

        # TODO: Implement optim and doe method
        if self.optim_method == "OPTIM":
            raise NotImplementedError("OPTIM optimisation is not yet implemented yet!")
        elif self.optim_method == "DOE":
            raise NotImplementedError("DOE optimisation is not yet implemented yet!")

        for module_obj in self.module_to_run_obj:
            module_obj.run(self.current_wkflow_dir)

    @staticmethod
    def get_related_modules(module_list, idx) -> list:
        """Get modules list related to a specific SettingGUI module"""

        if "SettingsGUI" in module_list[idx + 1 :] and idx + 1 != len(module_list):
            idx_next = module_list.index("SettingsGUI", idx + 1)
            return module_list[idx:idx_next]
        else:
            return module_list[idx:]


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


# TODO: to be removed when not used anywhere
def create_new_wkdir(global_wkdir=""):
    """Function to create a woking directory.

    Function 'create_new_wkdir' creates a new working directory in the /tmp file
    this directory is called 'SU2Run_data_hour'.
    In the case of an optimisation or DoE, it will create a working directory
    in the folder that was created at the first iteration of the routine.

    Args:
        routine_date (str) : Date of the first folder to find where to create
        the new working directory.
        routine_type (str) : Indicates if the folder has a subfolder called
        'Optim' or 'DoE'.

    Returns:
        wkdir (str): working directory path

    """

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if global_wkdir != "":
        dir_name = "/Runs/Run" + date
        run_dir = global_wkdir + dir_name
    else:
        dir_name = "CEASIOMpy_Run_" + date
        wkdir = os.path.join(os.path.dirname(MODULE_DIR), "WKDIR")
        run_dir = os.path.join(wkdir, dir_name)

    if not os.path.exists(run_dir):
        os.mkdir(run_dir)

    log.info(" NEW WKDIR ")
    log.info(run_dir)
    return run_dir


# TODO: to be removed when not used anywhere
def get_wkdir_or_create_new(tixi):
    """Function get the wkdir path from CPACS or create a new one

    Function 'get_wkdir_or_create_new' checks in the CPACS file if a working
    directory already exit for this run, if not, a new one is created and
    return.

    Args:
        tixi (handle): TIXI handle

    Returns:
        wkdir_path (str): Path to the active working directory

    """

    wkdir_path = get_value_or_default(tixi, WKDIR_XPATH, "")
    if wkdir_path == "":
        wkdir_path = create_new_wkdir()
        create_branch(tixi, WKDIR_XPATH)
        tixi.updateTextElement(WKDIR_XPATH, wkdir_path)
    else:
        # Check if the directory really exists
        if not os.path.isdir(wkdir_path):
            wkdir_path = create_new_wkdir()
            create_branch(tixi, WKDIR_XPATH)
            tixi.updateTextElement(WKDIR_XPATH, wkdir_path)

    return wkdir_path


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
