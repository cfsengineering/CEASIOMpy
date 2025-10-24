"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Classes to run ceasiompy workflows
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
import importlib

from ceasiompy.utils.guisettings import update_gui_settings_from_specs
from ceasiompy.utils.ceasiompylogger import add_to_runworkflow_history
from ceasiompy.utils.ceasiompyutils import (
    change_working_dir,
    current_workflow_dir,
    get_results_directory,
)

from typing import Union
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy.utils.moduleinterfaces import MODNAME_INIT
from ceasiompy import (
    log,
    LOGFILE,
)


# =================================================================================================
#   CLASSES
# =================================================================================================


class Workflow:
    """Class to define and run CEASIOMpy workflow."""

    def __init__(self: "Workflow") -> None:
        self.workflow_dir = current_workflow_dir()

    def _run_modules(
        self: "Workflow",
        module: str,
        geometry: Union[CPACS, Path],
        gui_settings: GUISettings,
        iteration: int = 0,
        test: bool = False,
    ) -> None:
        """
        Run a 'ModuleToRun' object in a specific wkdir.
        """

        if iteration == 0:
            log.info(f"Workflow's working directory: {self.workflow_dir} \n")

        log.info("---------- Start of " + module + " ----------")

        pkg = importlib.import_module(f"ceasiompy.{module}")
        module_dir = Path(next(iter(pkg.__path__)))

        # Find main python file for module
        for file in module_dir.iterdir():
            if file.name.endswith(".py") and not file.name.startswith("__"):
                python_file = file.stem
                break
        else:
            log.warning(f"No python files found for module {module}.")

        # Import the main function from the module's python file
        my_module = importlib.import_module(f"ceasiompy.{module}.{python_file}")

        init = importlib.import_module(f"ceasiompy.{module}.{MODNAME_INIT}")
        has_results_dir = init.RES_DIR

        # Run the module
        with change_working_dir(self.workflow_dir):
            if test:
                log.info("Updating CPACS from __specs__")
                update_gui_settings_from_specs(gui_settings, module, test)

            if has_results_dir:
                results_dir = get_results_directory(
                    module,
                    create=True,
                    wkflow_dir=self.workflow_dir,
                )
                my_module.main(geometry, gui_settings, results_dir)
            else:
                my_module.main(geometry, gui_settings)

            log.info("---------- End of " + module + " ---------- \n")

    def run_workflow(
        self: "Workflow",
        geometry: Union[CPACS, Path],
        modules_list: list,
        gui_settings: GUISettings,
        test: bool = False,
    ) -> None:
        """
        Run the complete Worflow.
        """

        add_to_runworkflow_history(self.workflow_dir)
        log.info(f'Running the followuing list of modules: {modules_list=}')

        for idx, module in enumerate(modules_list):
            self._run_modules(
                test=test,
                iteration=idx,
                module=module,
                geometry=geometry,
                gui_settings=gui_settings,
            )

        # Copy logfile in the Workflow directory
        shutil.copy(LOGFILE, self.workflow_dir)
