# =================================================================================================
#    IMPORTS
# =================================================================================================

import streamlit as st

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.workflowutils import current_workflow_dir
from ceasiompy.utils.moduleinterfaces import get_specs_for_module

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.stp import STP
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from typing import (
    List,
    Union,
    Optional,
)

from ceasiompy import (
    log,
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
            log.info("Saving GUI Settings.")
        else:
            log.error(
                "Could NOT save GUI Settings. "
                "You need to instantiate a TIXI handle."
            )

    def update_from_specs(
        self: 'GUISettings',
        modules_list: List[str],
        test: bool = False,
    ) -> None:
        generate_settings(
            gui_settings=self,
            modules_list=modules_list,
            test=test,
        )

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def generate_settings(
    gui_settings: "GUISettings",
    modules_list: List[str],
    test: bool,
) -> None:
    tixi = gui_settings.tixi
    for module in modules_list:
        module_name = module
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

            # Check if the name or var_type is in the dictionary
            # and call the corresponding function
            if name in AEROMAP_LIST:
                if "cpacs" in st.session_state:
                    aeromap_uid_list = st.session_state.cpacs.get_aeromap_uid_list()
                elif "stp" in st.session_state:
                    aeromap_uid_list = st.session_state.stp.get_aeromaps_uid()
                else:
                    log.error("Error finding geometry.")

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
                tixi.updateTextElement(xpath, str(value))

    gui_settings.save()


def create_gui_settings_from_specs(
    geometry: Union[CPACS, STP],
    modules_list: List[str],
    test: bool,  # For github workflows
) -> GUISettings:
    # Generate a New GUISettings Object
    if isinstance(geometry, CPACS):
        gui_settings = GUISettings(
            cpacs_path=geometry.cpacs_file,
        )
    elif isinstance(geometry, STP):
        gui_settings = GUISettings(
            stp_path=geometry.stp_path,
        )

    generate_settings(
        gui_settings=gui_settings,
        modules_list=modules_list,
        test=test,
    )

    return gui_settings
