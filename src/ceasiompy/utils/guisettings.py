# =================================================================================================
#    IMPORTS
# =================================================================================================

import re
import streamlit as st

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.moduleinterfaces import get_specs_for_module

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from typing import (
    List,
    Union,
    Optional,
)

from ceasiompy import (
    log,
    WKDIR_PATH,
)
from ceasiompy.utils import (
    GUI_SETTINGS,
    AEROMAP_LIST,
)

# =================================================================================================
#    CLASSES
# =================================================================================================


class GUISettings:
    def __init__(
        self: 'GUISettings',
        cpacs_path: Optional[Path] = None,
        stp_path: Optional[Path] = None,
    ) -> None:
        #
        self.cpacs_path = cpacs_path
        self.stp_path = stp_path

        self.file_name = self._get_file_name()

        # Create Basic GUI Settings
        self._create_document()

    def _safe_guard(self: 'GUISettings') -> None:
        # Safeguards
        if self.cpacs_path is not None and self.stp_path is not None:
            log.error(
                "Either self.cpacs_path or self.stp_path should be None. "
                "One geometry path can only exist."
            )

        if self.cpacs_path is None and self.stp_path is None:
            log.error(
                "Either self.cpacs_path or self.stp_path should NOT be None. "
                "One geometry path can only exist."
            )

    def _get_file_name(self: 'GUISettings') -> str:
        self._safe_guard()

        if self.cpacs_path is not None:
            return self.cpacs_path.name

        if self.stp_path is not None:
            return self.stp_path.name

    def _get_current_path_settings(self: 'GUISettings') -> str:
        return f'{current_workflow_dir() / GUI_SETTINGS}'

    def _create_document(self: 'GUISettings') -> None:
        '''
        Creates New GUI Settings (OVER-RIDE)
        '''
        self._safe_guard()

        # Create New Document
        tixi = Tixi3()

        self.tixi = tixi  # Keeps reference (i.e. mutable)

        # Tixi3.create requires the root element name
        tixi.create("Settings")

        # create CEASIOMpy node under /Settings
        tixi.createElement("/Settings", "CEASIOMpy")

        # Filename is always specified
        tixi.addTextElement("/Settings", "file_name", str(self.file_name))

        if self.cpacs_path is not None:
            tixi.addTextElement("/Settings", "cpacs_path", str(self.cpacs_path))

        if self.stp_path is not None:
            tixi.addTextElement("/Settings", "stp_path", str(self.stp_path))

        self.save()

    def save(self: 'GUISettings') -> None:
        if hasattr(self, "tixi"):
            path_to_save: str = self._get_current_path_settings()
            self.tixi.save(path_to_save)

            # Create new to modify
            new_tixi = Tixi3()
            new_tixi.open(path_to_save)

            self.tixi = new_tixi  # Keeps reference (i.e. mutable)
        else:
            log.error(
                "Could NOT save GUI Settings. "
                "You need to instantiate a TIXI handle."
            )


# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def update_gui_settings_from_specs(
    geometry: Union[CPACS, Path],
    gui_settings: Optional[GUISettings],
    module_name: str,
    test: bool,  # For github workflows
) -> GUISettings:
    if gui_settings is None:
        # Generate a New GUISettings Object
        if isinstance(geometry, CPACS):
            gui_settings = GUISettings(
                cpacs_path=geometry.cpacs_file,
            )
        else:
            gui_settings = GUISettings(
                stp_path=geometry,
            )

    tixi = gui_settings.tixi
    cpacsin_out: CPACSInOut = get_specs_for_module(module_name).cpacs_inout
    inputs = cpacsin_out.get_gui_dict()

    for name, default_value, var_type, _, xpath, _, _, test_value, _ in inputs.values():
        if test:
            value = test_value
        else:
            value = default_value

        parts = xpath.strip("/").split("/")
        for i in range(1, len(parts) + 1):
            path = "/" + "/".join(parts[:i])
            if not tixi.checkElement(path):
                tixi.createElement("/" + "/".join(parts[: i - 1]), parts[i - 1])

        # Check if the name or var_type is in the dictionary and call the corresponding function
        if name in AEROMAP_LIST and "cpacs" in st.session_state:
            aeromap_uid_list = st.session_state.cpacs.get_aeromap_uid_list()
            if not len(aeromap_uid_list):
                log.error("You must create an aeromap in order to use this module !")
            else:
                # Use first aeromap
                tixi.updateTextElement(xpath, aeromap_uid_list[0])

        elif var_type == str:
            tixi.updateTextElement(xpath, value)
        elif var_type == float:
            tixi.updateDoubleElement(xpath, value, format="%g")
        elif var_type == bool:
            tixi.updateBooleanElement(xpath, value)
        elif var_type == int:
            tixi.updateIntegerElement(xpath, value, format="%d")
        elif var_type == list:
            tixi.updateTextElement(xpath, str(value[0]))
        elif var_type == "DynamicChoice":
            create_branch(tixi, xpath + "type")
            tixi.updateTextElement(xpath + "type", str(value[0]))
        elif var_type == "multiselect":
            tixi.updateTextElement(xpath, ";".join(str(ele) for ele in value))
        else:
            tixi.updateTextElement(xpath, value)

    gui_settings.save()

    st.session_state.gui_settings = gui_settings
    return gui_settings


def current_workflow_dir() -> Path:
    """
    Get the current workflow directory.
    """

    # collect numeric suffixes only (defensive against unexpected folder names)
    idx_list: List[int] = []

    # Make sure WKDIR_PATH exists as a dir
    WKDIR_PATH.mkdir(exist_ok=True)

    pattern = re.compile(r"Workflow_(\d+)$")
    for p in WKDIR_PATH.iterdir():
        if not p.is_dir():
            log.warning(f"There should be only Directories in {WKDIR_PATH=}")
            continue

        m = pattern.match(p.name)
        if m:
            try:
                idx_list.append(int(m.group(1)))
            except ValueError as e:
                log.error(f"Could not process pattern of workflows {e=}")

    if idx_list:
        max_idx = max(idx_list)
        last_wkflow_dir = WKDIR_PATH / get_workflow_idx(max_idx)
        has_subdirs = any(p.is_dir() for p in last_wkflow_dir.iterdir())

        # If the last workflow contains the toolinput file, we increment index
        if has_subdirs:
            new_idx = max_idx + 1
        else:
            new_idx = max_idx
    else:
        new_idx = 1

    current_wkflow_dir = WKDIR_PATH / get_workflow_idx(new_idx)
    current_wkflow_dir.mkdir(parents=True, exist_ok=True)

    return current_wkflow_dir


def get_workflow_idx(wkflow_idx: int) -> str:
    return f"Workflow_{str(wkflow_idx).rjust(3, '0')}"
