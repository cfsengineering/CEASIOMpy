"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to create a CEASIOMpy workflow

| Author: Aidan Jungo
| Creation: 2022-09-16
| Modified: Leon Deligny
| Date: 07-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from streamlit_app.utils.streamlitutils import create_sidebar
from ceasiompy.utils.moduleinterfaces import (
    get_module_list,
)

from typing import (
    List,
    Final,
)

from ceasiompy.SMUse import MODULE_NAME as SMUSE
from ceasiompy.PyAVL import MODULE_NAME as PYAVL
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN
from ceasiompy.SMTrain import MODULE_NAME as SMTRAIN
from ceasiompy.Database import MODULE_NAME as DATABASE
from ceasiompy.ExportCSV import MODULE_NAME as EXPORTCSV
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH
from ceasiompy.ThermoData import MODULE_NAME as THERMODATA
from ceasiompy.CPACSUpdater import MODULE_NAME as CPACSUPDATER
from ceasiompy.CPACSCreator import MODULE_NAME as CPACSCREATOR
from ceasiompy.SkinFriction import MODULE_NAME as SKINFRICTION
from ceasiompy.StaticStability import MODULE_NAME as STATICSTABILITY
from ceasiompy.DynamicStability import MODULE_NAME as DYNAMICSTABILITY
from ceasiompy.SaveAeroCoefficients import MODULE_NAME as SAVEAEROCOEF

# ==============================================================================
#   CONSTANTS
# ==============================================================================

PAGE_NAME: Final[str] = "Workflow"

HOW_TO_TEXT: Final[str] = (
    "### How to use Create a workflow?\n"
    "You can either:\n"
    "- Select a predefined workflow and modify it\n"
    "- Build your own workflow by selecting among available modules\n"
    "When it is done, go to the *Settings* page\n"
)

CSS: Final[str] = """
<style>
.css-1awtkze {
    border-radius:3px;
    background-color:#ff7f2a;
    padding: 6px;
}
.css-1awtkze:after {
content:'';
position: absolute;
top: 100%;
left: 50%;
margin-left: -20px;
margin-top: 2px;
width: 0;
height: 0;
border-top: solid 10px #9e9e93;
border-left: solid 10px transparent;
border-right: solid 10px transparent;
}
.stButton > button {
    border-radius:10px;
}
</style>
"""

# Resolve the module objects lazily here (runtime, not import time)
PREDEFINED_WORKFLOWS: Final[List[List[str]]] = [
    [PYAVL, STATICSTABILITY, DATABASE],
    [CPACSUPDATER, CPACSCREATOR, CPACS2GMSH, SU2RUN, EXPORTCSV],
    [CPACS2GMSH, THERMODATA, SU2RUN, SKINFRICTION, DATABASE],
    [SMTRAIN, SMUSE, SAVEAEROCOEF],
    [DYNAMICSTABILITY, DATABASE],
    # ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run", "ExportCSV"],
]

AVAILABLE_MODULES: Final[List[str]] = get_module_list()

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def section_predefined_workflow():
    """
    Where to define the Pre-defined workflows.
    """

    st.markdown("#### Predefined Workflows")

    for workflow_idx, workflow in enumerate(PREDEFINED_WORKFLOWS):
        display_names = [
            item
            for item in workflow
        ]
        button_label = " → ".join(display_names)
        # Provide a unique key to avoid StreamlitDuplicateElementId
        if st.button(button_label, key=f"predefined_workflow_{workflow_idx}"):
            # store the actual module objects (or strings if they are placeholders)
            st.session_state.modules_list = workflow


def section_add_module():
    """
    Where to select the workflow.
    """

    st.markdown("#### Your workflow")

    if "modules_list" not in st.session_state:
        st.session_state["modules_list"] = []

    if len(st.session_state.modules_list):
        for i, module in enumerate(st.session_state.modules_list):
            col1, col2, col3, _ = st.columns([6, 1, 1, 5])

            with col1:
                # Display human-friendly label but keep module object in state
                label = module
                st.button(label, key=f"module_number_{i}")

            with col2:
                if i > 0 and st.button("⬆️", key=f"move{i}", help="Move up"):
                    st.session_state.modules_list.pop(i)
                    st.session_state.modules_list.insert(i - 1, module)
                    st.session_state.gui_settings.update_from_specs(
                        modules_list=st.session_state.modules_list,
                    )
                    st.rerun()

            with col3:
                if st.button("❌", key=f"del{i}", help=f"Remove {label} from the workflow"):
                    st.session_state.modules_list.pop(i)
                    st.session_state.gui_settings.update_from_specs(
                        modules_list=st.session_state.modules_list,
                    )
                    st.rerun()
    else:
        st.warning("No module has been added to the workflow.")

    col1, col2 = st.columns(2)
    with col1:
        module = st.selectbox(
            "Module to add to the workflow:",
            AVAILABLE_MODULES,
        )

    with col2:
        # Add vertical spacing to match the label height of selectbox
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("✔", help="Add this module to the workflow"):
            st.session_state.modules_list.append(module)
            st.session_state.gui_settings.update_from_specs(
                modules_list=st.session_state.modules_list,
            )
            st.rerun()


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    # Define interface
    create_sidebar(
        page_name=PAGE_NAME,
        how_to_text=HOW_TO_TEXT,
    )

    # Custom CSS
    st.markdown(CSS, unsafe_allow_html=True)
    st.title(PAGE_NAME)

    section_predefined_workflow()

    st.markdown("---")

    section_add_module()

    st.markdown("---")

    # Add last_page
    st.session_state.last_page = PAGE_NAME
