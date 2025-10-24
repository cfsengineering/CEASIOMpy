"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions utils to run ceasiompy workflows
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import streamlit as st

from pydantic import validate_call
from ceasiompy.utils.guisettings import update_gui_settings_from_specs
from ceasiompy.utils.ceasiompyutils import (
    get_wkdir_status,
    change_working_dir,
    current_workflow_dir,
    get_results_directory,
)

from pathlib import Path
from unittest.mock import MagicMock
from cpacspy.cpacspy import (
    CPACS,
)
from typing import (
    Callable,
)

from ceasiompy import (
    log,
    ceasiompy_cfg,
)
from ceasiompy import (
    CPACS_FILES_PATH,
)
from ceasiompy.utils.moduleinterfaces import (
    MODNAME_SPECS,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@validate_call(config=ceasiompy_cfg)
def call_main(main: Callable, module_name: str, cpacs_path: Path = None) -> None:
    """
    Calls main with input/output CPACS of module named module_name.
    #TODO: Add Args and Returns.
    """
    st.session_state = MagicMock()
    wkflow_dir = current_workflow_dir()

    log.info(f"Workflow's working directory: {wkflow_dir} \n")
    log.info("----- Start of " + module_name + " -----")

    if cpacs_path is None:
        xml_file = "D150_simple.xml"
        cpacs_path = Path(CPACS_FILES_PATH, xml_file)
    else:
        xml_file = cpacs_path.name

    with change_working_dir(wkflow_dir):
        cpacs = CPACS(cpacs_path)
        log.info(f"Upload default values from {MODNAME_SPECS}.")
        update_gui_settings_from_specs(cpacs, module_name, test=True)

    new_cpacs_path = wkflow_dir / xml_file
    cpacs.save_cpacs(new_cpacs_path, overwrite=True)
    cpacs = CPACS(new_cpacs_path)

    log.info(f"Finished uploading default values from {MODNAME_SPECS}.")

    if get_wkdir_status(module_name):
        results_dir = get_results_directory(module_name, create=True, wkflow_dir=wkflow_dir)
        main(cpacs, results_dir)
    else:
        main(cpacs)

    cpacs.save_cpacs(new_cpacs_path, overwrite=True)

    log.info("----- End of " + module_name + " -----")
