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

from ceasiompy.utils.guisettings import (
    create_gui_settings_from_specs,
)
from ceasiompy.utils.workflowutils import current_workflow_dir
from ceasiompy.utils.ceasiompylogger import add_to_runworkflow_history
from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
)

from typing import List
from pathlib import Path
from types import ModuleType
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.stp import STP
from ceasiompy.utils.guisettings import GUISettings
from typing import (
    Union,
    Optional,
)

from ceasiompy.utils.moduleinterfaces import (
    MODNAME_INIT,
)
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

    def _run_module(
        self: "Workflow",
        module: str,
        iteration: int,
        geometry: Union[CPACS, STP],
        gui_settings: GUISettings,
    ) -> None:
        """
        Run a Specific Module.

        Function inherent to Workflow Object.
        """

        if iteration == 0:
            log.info(f"Workflow's working directory: {self.workflow_dir} \n")

        log.info(f"---------- Start of {module} ----------")

        init, main_module = _get_module_from_name(module)

        # Run the module
        if init.RES_DIR:
            results_dir = get_results_directory(
                module,
                create=True,
                wkflow_dir=self.workflow_dir,
            )
            main_module.main(geometry, gui_settings, results_dir)
        else:
            main_module.main(geometry, gui_settings)

        # Some Modules Interact with others
        # through GUI Settings
        gui_settings.save()

        log.info(f"---------- End of {module} ---------- \n")

    def run_workflow(
        self: "Workflow",
        geometry: Union[CPACS, STP],
        modules_list: List[str],
        gui_settings: Optional[GUISettings] = None,
    ) -> None:
        """
        Run the complete Worflow.
        """

        add_to_runworkflow_history(self.workflow_dir)
        if gui_settings is None:
            log.info("Generating GUI Settings from __specs__")
            gui_settings = create_gui_settings_from_specs(
                geometry=geometry,
                modules_list=modules_list,
                test=True,
            )

        for idx, module in enumerate(modules_list):
            self._run_module(
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


def _get_module_from_name(module: str) -> tuple[ModuleType, ModuleType]:
    python_file = _get_main_python_file(from_module=module)
    main = _get_ceasiompy_module(
        module=module,
        from_file=python_file,
    )
    init = _get_ceasiompy_module(
        module=module,
        from_file=MODNAME_INIT,
    )
    return init, main


def _get_ceasiompy_module(
    module: str,
    from_file: str,
) -> ModuleType:
    try:
        return importlib.import_module(f"ceasiompy.{module}.{from_file}")
    except ValueError as e:
        log.warning(
            f"Could not load ceasiompy module {module} "
            f"from file {from_file} "
            f"got error {e=}"
        )
        raise ValueError
    except Exception as e:
        log.error(
            f"For module {module=} {from_file=} "
            f"finished with exception {e=}"
        )
        raise Exception


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
