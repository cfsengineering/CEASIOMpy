# =================================================================================================
#    IMPORTS
# =================================================================================================

import streamlit as st

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.utils.moduleinterfaces import get_specs_for_module

from typing import Optional
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
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
        file_name: str,
        cpacs_path: Optional[str] = None,
        stp_path: Optional[str] = None,
    ) -> None:
        #
        self.file_name = file_name
        self.cpacs_path = cpacs_path
        self.stp_path = stp_path

        # Create Basic GUI Settings
        self._create_document()

    def _get_current_path_settings(self: 'GUISettings') -> str:
        return f'{current_workflow_dir() / GUI_SETTINGS}'

    def _create_document(self: 'GUISettings') -> None:
        '''
        Creates New GUI Settings (OVER-RIDE)
        '''
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
    gui_settings: GUISettings,
    module_name: str,
    test: bool,
) -> None:
    tixi = gui_settings.tixi
    st.session_state.gui_settings = gui_settings
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
        if name in AEROMAP_LIST:
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
