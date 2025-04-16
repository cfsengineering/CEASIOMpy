"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Classes to run ceasiompy workflows


| Author : Aidan Jungo
| Creation: 2019-10-04

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import shutil
from datetime import datetime
from pathlib import Path
import importlib

<<<<<<< HEAD
# from ceasiompy.Optimisation.optimisation import routine_launcher
from ceasiompy.utils.ceasiomlogger import add_to_runworkflow_history, get_logger
from ceasiompy.utils.ceasiompyutils import change_working_dir, run_module
=======
from ceasiompy.Optimisation.optimisation import routine_launcher
from ceasiompy.utils.ceasiompylogger import add_to_runworkflow_history
from ceasiompy.utils.ceasiompyutils import change_working_dir, run_module, get_results_directory
>>>>>>> origin/main
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.moduleinterfaces import get_module_list

from ceasiompy import log
from ceasiompy.utils.moduleinterfaces import MODNAME_INIT

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH, LOGFILE, MODULES_DIR_PATH

#
OPTIM_METHOD = ["Optimisation", "DOE"]

# =================================================================================================
#   CLASSES
# =================================================================================================


class ModuleToRun:
    def __init__(
        self,
        name: str,
        wkflow_dir: Path,
        cpacs_in: Path = None,
        cpacs_out: Path = None,
    ) -> None:

        # Check module name validity
        accepted_names = get_module_list(only_active=False) + OPTIM_METHOD
        if name not in accepted_names:
            raise ValueError(f"Module '{name}' did not exit!")

        # Check workflow directory exist
        if not wkflow_dir.exists():
            raise FileNotFoundError(f"{str(wkflow_dir)} did not exist!")

        # Main attributes
        self.name = name
        self.wkflow_dir = wkflow_dir
        self.cpacs_in = cpacs_in
        init = importlib.import_module(f"ceasiompy.{name}.{MODNAME_INIT}")
        add_res_dir: bool = init.RES_DIR

        if add_res_dir:
            self.results_dir = get_results_directory(
                name, create=True, wkflow_dir=wkflow_dir)
        else:
            self.results_dir = None
        self.cpacs_out = cpacs_out

        # Set module path
        self.module_dir = Path(MODULES_DIR_PATH, self.name)

        # Set other default values
        self.gui_related_modules = []
        self.is_optim_module = False
        self.optim_method = None
        self.optim_related_modules = []

    def create_module_wkflow_dir(self, cnt: int) -> None:

        if self.is_optim_module and self.optim_method:
            module_wkflow_name = str(cnt).rjust(
                2, "0") + "_" + self.optim_method
        else:
            module_wkflow_name = str(cnt).rjust(2, "0") + "_" + self.name

        self.module_wkflow_path = Path.joinpath(
            self.wkflow_dir, module_wkflow_name)
        self.module_wkflow_path.mkdir()


class OptimSubWorkflow:
    """Class to define and run CEASIOMpy optimisation (opim/doe) subworkflow."""

    def __init__(
        self, subworkflow_dir: Path, cpacs_in: Path, optim_method: str, modules_list: list
    ) -> None:

        self.subworkflow_dir = subworkflow_dir
        self.cpacs_in = cpacs_in
        self.optim_method = optim_method
        self.modules_list = modules_list  # List of modules to run (str)

        # If Otimisation module was not in the list add it
        if "Optimisation" not in self.modules_list:
            self.modules_list.insert(0, "Optimisation")

        self.modules = [ModuleToRun(module, subworkflow_dir)
                        for module in modules_list]

        self.iteration = 0

    def set_subworkflow(self) -> None:
        """Set input and output for subworkflow."""

        for m, _ in enumerate(self.modules):

            # Create the module directory in the subworkflow directory
            with change_working_dir(self.subworkflow_dir):
                self.modules[m].create_module_wkflow_dir(m + 1)

            # Set the input/output of each modules
            if m == 0:
                if self.iteration == 0:
                    cpacs_in = self.cpacs_in
                else:
                    cpacs_in = self.modules[-1].cpacs_out
            else:
                cpacs_in = self.modules[m - 1].cpacs_out

            self.modules[m].cpacs_in = cpacs_in
            self.modules[m].cpacs_out = Path(
                self.modules[m].module_wkflow_path,
                "iter_" + str(self.iteration).rjust(2, "0") + ".xml",
            )

    def run_subworkflow(self) -> None:
        """Run the opimisation subworflow"""

        # log.info(f"Running optim subworkflow in {self.subworkflow_dir}")

        # First iteration
        for module in self.modules:
            run_module(module, self.subworkflow_dir)

        # TODO: copy last tool output when optim done (last iteration)
        shutil.copy(self.modules[-1].cpacs_out,
                    Path(self.subworkflow_dir, "ToolOutput.xml"))

        # TODO: Probably not here
        self.iteration += 1

        # Other iterations
        # module_optim = [module for module in self.modules]

<<<<<<< HEAD
        # routine_launcher(self.optim_method, module_optim, self.subworkflow_dir.parent)
=======
        routine_launcher(self.optim_method, module_optim,
                         self.subworkflow_dir.parent)
>>>>>>> origin/main


class Workflow:
    """Class to define and run CEASIOMpy workflow."""

    def __init__(self) -> None:

        self.working_dir = Path().cwd()
        self.cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml").resolve()
        self.current_wkflow_dir = None

        self.modules_list = []  # List of modules to run (str)
        self.modules = []  # List of modules to run (object ModuleToRun)

        self.optim_method = None
        self.module_optim = []

    def from_config_file(self, cfg_file: Path) -> None:
        """Get parameters from a config file

        Args:
            cfg_file (str): Configuration file path
        """

        cfg = ConfigFile(cfg_file)

        self.working_dir = cfg_file.parent.absolute()
        self.cpacs_in = Path(cfg["CPACS_TOOLINPUT"])

        self.modules_list = cfg["MODULE_TO_RUN"]

        try:
            self.module_optim = cfg["MODULE_OPTIM"]
        except KeyError:
            self.module_optim = ["NO"] * len(self.modules_list)

        try:
            self.optim_method = cfg["OPTIM_METHOD"]
        except KeyError:
            self.optim_method = "None"

    def write_config_file(self) -> None:
        """Write the workflow configuration file in the working directory."""

        cfg = ConfigFile()
        cfg["comment_1"] = f"File written {datetime.now()}"
        cfg["CPACS_TOOLINPUT"] = self.cpacs_in

        if self.modules_list:
            cfg["MODULE_TO_RUN"] = self.modules_list
        else:
            cfg["comment_modules_list"] = "MODULE_TO_RUN = (  )"

        if self.module_optim:
            cfg["MODULE_OPTIM"] = self.module_optim
            cfg["OPTIM_METHOD"] = self.optim_method
        else:
            cfg["comment_module_optim"] = "MODULE_OPTIM = (  )"
            cfg["comment_optim_method"] = "OPTIM_METHOD = NONE"

        cfg_file = Path(self.working_dir, "ceasiompy.cfg")
        cfg.write_file(cfg_file, overwrite=True)

    def set_workflow(self) -> None:
        """Create the directory structure and set input/output of each modules"""

        # Check optim method validity
        if str(self.optim_method) not in (OPTIM_METHOD + ["None", "NONE"]):
            raise ValueError(
                f"Optimisation method {self.optim_method} not supported")

        # Check coherence of the optimisation modules from config file
        if "YES" in self.module_optim:
            if not self.optim_method:
                raise ValueError(
                    "Some modules are define as optimisation module but "
                    "no optimisation method is defined"
                )

            optim_idx = [i for i, val in enumerate(
                self.module_optim) if val == "YES"]
            for i, val in enumerate(optim_idx[:-1]):
                if val + 1 != optim_idx[i + 1]:
                    raise ValueError(
                        "All optimisation module must be contiguous!")

        # Check working directory
        if not self.working_dir:
            raise ValueError("Working directory is not defined!")

        wkdir = self.working_dir
        os.chdir(wkdir)

        # Check index of the last workflow directory to set the next one
        wkflow_list = [int(dir.stem.split("_")[-1])
                       for dir in wkdir.glob("Workflow_*")]
        if wkflow_list:
            wkflow_idx = str(max(wkflow_list) + 1).rjust(3, "0")
        else:
            wkflow_idx = "001"

        self.current_wkflow_dir = Path.joinpath(
            wkdir, "Workflow_" + wkflow_idx)
        self.current_wkflow_dir.mkdir()

        # Copy CPACS to the workflow dir
        if not self.cpacs_in.exists():
            raise FileNotFoundError(f"{self.cpacs_in} has not been found!")

        wkflow_cpacs_in = Path.joinpath(
            self.current_wkflow_dir, "00_ToolInput.xml").absolute()

        shutil.copy(self.cpacs_in, wkflow_cpacs_in)

        # Create the module object and its directory structure
        cnt = 1
        module_optim_idx = None

        for m, module_name in enumerate(self.modules_list):

            # Check if it is the first module (to know where the cpacs input file should come from)
            if m == 0:
                cpacs_in = wkflow_cpacs_in
            else:
                cpacs_in = self.modules[-1].cpacs_out

            # Create an object for the module if not and opitm module
            if self.module_optim[m] == "NO":
                module = ModuleToRun(
                    module_name, self.current_wkflow_dir, cpacs_in)

            skip_create_module = False

            # Check if should be included in Optim/DoE
            if self.optim_method and self.module_optim[m] == "YES":
                if module_optim_idx is None:
                    module = ModuleToRun(
                        self.optim_method, self.current_wkflow_dir, cpacs_in)
                    module.optim_method = self.optim_method
                    module.is_optim_module = True
                    module.optim_related_modules.append(module_name)
                    module_optim_idx = m
                else:
                    self.modules[module_optim_idx].optim_related_modules.append(
                        module_name)
                    skip_create_module = True

            if not skip_create_module:
                module.create_module_wkflow_dir(cnt)
                self.modules.append(module)
                module.cpacs_out = Path.joinpath(
                    module.module_wkflow_path, "ToolOutput.xml")
                cnt += 1

        # Create Optim/DoE subworkflow directory for the optim module if exists
        if module_optim_idx:
            module_optim_obj = self.modules[module_optim_idx]
            self.subworkflow = OptimSubWorkflow(
                module_optim_obj.module_wkflow_path,
                module_optim_obj.cpacs_in,
                self.optim_method,
                module_optim_obj.optim_related_modules,
            )
            self.subworkflow.set_subworkflow()

    def run_workflow(self, test=False) -> None:
        """Run the complete Worflow"""

        add_to_runworkflow_history(self.current_wkflow_dir)

        for module in self.modules:
            if module.is_optim_module:
                self.subworkflow.run_subworkflow()
            else:
                run_module(
                    module,
                    self.current_wkflow_dir,
                    self.modules_list.index(
                        module.name
                    ), test)

        shutil.copy(module.cpacs_out, Path(
            self.current_wkflow_dir, "ToolOutput.xml"))

        # Copy logfile in the Workflow directory
        shutil.copy(LOGFILE, self.current_wkflow_dir)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
