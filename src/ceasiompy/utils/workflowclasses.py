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

from pathlib import Path
from types import ModuleType
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings
from typing import (
    Union,
    Optional,
)

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
        iteration: int,
        geometry: Union[CPACS, Path],
        gui_settings: Optional[GUISettings] = None,
    ) -> None:
        """
        Run a 'ModuleToRun' object in a specific wkdir.
        """

        if iteration == 0:
            log.info(f"Workflow's working directory: {self.workflow_dir} \n")

        log.info("---------- Start of " + module + " ----------")

        python_file = _get_main_python_file(from_module=module)

        my_module: ModuleType = _get_ceasiompy_module(
            module=module,
            from_file=python_file,
        )

        # Run the module
        with change_working_dir(self.workflow_dir):
            if gui_settings is None:
                log.info("Generating GUI Settings from __specs__")
                gui_settings = update_gui_settings_from_specs(gui_settings, module)

            if my_module.RES_DIR:
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
        gui_settings: Optional[GUISettings] = None,
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


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def _get_ceasiompy_module(
    module: str,    
    from_file: str,
) -> ModuleType:
    try:
        return importlib.import_module(f"ceasiompy.{module}.{from_file}")
    except Exception as e:
        log.warning(
            f"Could not load ceasiompy module {module}"
            f"from file {from_file}"
        )

def _get_main_python_file(from_module: str) -> str:
    pkg = importlib.import_module(f"ceasiompy.{from_module}")
    module_dir = Path(next(iter(pkg.__path__)))

    # Find main python file for module
    for file in module_dir.iterdir():
        if file.name.endswith(".py") and not file.name.startswith("__"):
            python_file: str = file.stem
            break
    else:
        log.warning(f"No python files found for module {from_module}.")

    return python_file
