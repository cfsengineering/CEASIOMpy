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
import importlib
from pathlib import Path
from dataclasses import dataclass
from ceasiompy.utils.ceasiompyutils import change_working_dir

import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.SettingsGUI.settingsgui import create_settings_gui
from ceasiompy.Optimisation.optimisation import routine_launcher
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.moduleinterfaces import get_submodule_list
from ceasiompy.utils.xpath import WKDIR_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = Path(ceasiompy.__init__.__file__).parent


OPTIM_METHOD = ["OPTIM", "DOE"]

# =================================================================================================
#   CLASSES
# =================================================================================================


@dataclass
class ModuleToRun:

    module_name: str
    wkflow_dir: Path
    cpacs_in: Path = None
    cpacs_out: Path = None

    def __post_init__(self) -> None:

        # Check if the module is valid
        accepted_names = get_submodule_list() + OPTIM_METHOD
        if self.module_name not in accepted_names:
            raise ValueError(f"Module '{self.module_name}' did not exit!")

        # Set module path
        self.module_path = Path.joinpath(LIB_DIR, self.module_name)

        # Check if the workflow directory exist
        if not self.wkflow_dir.exists():
            raise FileNotFoundError(f"{str(self.wkflow_dir)} did not exist!")

        # Set default values
        self.is_settinggui = False
        self.gui_related_modules = []
        self.is_optim_module = False
        self.optim_method = None
        self.optim_related_modules = []

    def define_settinggui(self, gui_related_modules: list) -> None:

        self.is_settinggui = True
        self.gui_related_modules = gui_related_modules

    def define_optim_module(self, optim_method) -> None:

        if optim_method not in OPTIM_METHOD:
            raise ValueError(
                f"Not recognize optim_method! It must be test {' or '.join(OPTIM_METHOD)}"
            )

        self.optim_method = optim_method
        self.is_optim_module = True

    def create_module_wkflow_dir(self, cnt: int) -> None:

        if self.is_optim_module and self.optim_method:
            module_wkflow_name = str(cnt).rjust(2, "0") + "_" + self.optim_method
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

            create_settings_gui(str(self.cpacs_in), str(self.cpacs_out), self.gui_related_modules)

        elif self.module_name in OPTIM_METHOD:
            # TODO: Implement optim module
            pass

        else:

            for file in self.module_path.iterdir():
                if file.name.endswith(".py") and not file.name.startswith("__"):
                    python_file = file.stem

            # Import the main function of the module
            my_module = importlib.import_module(f"ceasiompy.{self.module_name}.{python_file}")

            # Run the module
            with change_working_dir(wkdir):
                my_module.main(str(self.cpacs_in), str(self.cpacs_out))


class OptimSubWorkflow:
    """Class to define and run CEASIOMpy optimisation (opim/doe) subworkflow."""

    def __init__(self, subworkflow_dir: Path, cpacs_path: Path, modules: list) -> None:

        self.subworkflow_dir = subworkflow_dir
        self.cpacs_path = cpacs_path
        self.modules = [ModuleToRun(module, self.subworkflow_dir) for module in modules]
        self.iteration = 0

    def set_subworkflow(self) -> None:
        """Create the directory structure and set input/output of each modules for the subworkflow."""

        self.set_cpacs_in_out()

        for i, module in enumerate(self.modules):
            with change_working_dir(self.subworkflow_dir):
                module.create_module_wkflow_dir(i + 1)

    def set_cpacs_in_out(self) -> None:
        """Set the input/output of module of the subworkflow."""

        # Set the input/output of each modules
        for i, module in enumerate(self.modules):
            if i == 0:
                if self.iteration == 0:
                    cpacs_in = self.cpacs_path
                else:
                    cpacs_in = self.modules[-1].cpacs_out
            else:
                cpacs_in = self.modules[i - 1].cpacs_out

            module.cpacs_in = cpacs_in
            module.cpacs_out = Path(
                module.wkflow_dir, "iter_" + str(self.iteration).rjust(2, "0") + ".xml"
            )

    def run_subworkflow(self) -> None:
        """Run the opimisation subworflow"""

        log.info(f"Running the subworkflow in {self.subworkflow_dir}")

        if self.iteration == 0:
            pass
            # TODO: Create the first iteration of the subworkflow
        else:
            pass


class Workflow:
    """Class to define and run CEASIOMpy workflow."""

    def __init__(self) -> None:

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
        module_optim_idx = None

        for m, module_name in enumerate(self.module_to_run):

            # Check if it is the first module (to know where the cpacs input file should come from)
            if m == 0:
                cpacs_in = wkflow_cpacs_in
            else:
                cpacs_in = self.module_to_run_obj[-1].cpacs_out

            # Create an object for the module if not and opitm module
            if self.module_optim[m] == "NO":
                module_obj = ModuleToRun(module_name, self.current_wkflow_dir, cpacs_in)

            # Check if the module is SettingGUI
            gui_related_moduless = []
            if module_name == "SettingsGUI":
                gui_related_moduless = self.get_gui_related_moduless(self.module_to_run, m)
                module_obj.define_settinggui(gui_related_moduless)

            skip_create_module = False

            # Check if should be included in Optim/DoE
            if self.optim_method and self.module_optim[m] == "YES":
                if module_optim_idx is None:
                    module_obj = ModuleToRun(self.optim_method, self.current_wkflow_dir, cpacs_in)
                    module_obj.define_optim_module(self.optim_method)
                    module_obj.optim_related_modules.append(module_name)
                    module_optim_idx = m
                else:
                    self.module_to_run_obj[module_optim_idx].optim_related_modules.append(
                        module_name
                    )
                    skip_create_module = True

            if not skip_create_module:
                module_obj.create_module_wkflow_dir(cnt)
                self.module_to_run_obj.append(module_obj)
                cnt += 1

        # Create Optim/DoE subworkflow directory for the optim module if exists
        if module_optim_idx is not None:
            module_optim_obj = self.module_to_run_obj[module_optim_idx]
            self.subworkflow = OptimSubWorkflow(
                module_optim_obj.module_wkflow_path,
                module_optim_obj.cpacs_in,
                module_optim_obj.optim_related_modules,
            )
            self.subworkflow.set_subworkflow()

        # Create Results directory
        new_res_dir = Path.joinpath(self.current_wkflow_dir, "Results")
        new_res_dir.mkdir()

    def run_workflow(self) -> None:
        """Run the complete Worflow"""

        log.info(f"Running the workflow in {self.current_wkflow_dir}")

        # TODO: Implement optim and doe method
        # if self.optim_method == "OPTIM":
        #     raise NotImplementedError("OPTIM optimisation is not yet implemented yet!")
        # elif self.optim_method == "DOE":
        #     raise NotImplementedError("DOE optimisation is not yet implemented yet!")

        for module_obj in self.module_to_run_obj:

            if module_obj.is_optim_module:

                self.subworkflow.run_subworkflow()

            else:

                module_obj.run(self.current_wkflow_dir)

    @staticmethod
    def get_gui_related_moduless(module_list, idx) -> list:
        """Get modules list related to a specific SettingGUI module"""

        if "SettingsGUI" in module_list[idx + 1 :] and idx + 1 != len(module_list):
            idx_next = module_list.index("SettingsGUI", idx + 1)
            return module_list[idx:idx_next]
        else:
            return module_list[idx:]


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
