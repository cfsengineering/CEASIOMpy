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
from ceasiompy.utils.moduleinterfaces import get_module_list

from typing import Final

from ceasiompy.SMUse import MODULE_NAME as SMUSE
from ceasiompy.PyAVL import MODULE_NAME as PYAVL
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN
from ceasiompy.SMTrain import MODULE_NAME as SMTRAIN
from ceasiompy.Database import MODULE_NAME as DATABASE
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH
from ceasiompy.CPACSUpdater import MODULE_NAME as CPACSUPDATER
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

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def section_predefined_workflow():
    """
    Where to define the Pre-defined workflows.
    """

    st.markdown("#### Predefined Workflows")

    predefine_workflows = [
        [PYAVL, STATICSTABILITY, DATABASE],
        [CPACSUPDATER, "CPACSCreator", CPACS2GMSH, SU2RUN, "ExportCSV"],
        [CPACS2GMSH, "ThermoData", SU2RUN, "SkinFriction", DATABASE],
        [SMTRAIN, SMUSE, SAVEAEROCOEF],
        [DYNAMICSTABILITY, DATABASE],
        # ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run", "ExportCSV"],
    ]

    for workflow in predefine_workflows:
        if st.button(" → ".join(workflow)):
            st.session_state.workflow_modules = workflow


def section_add_module():
    """
    Where to select the workflow.
    """

    st.markdown("#### Your workflow")

    if "workflow_modules" not in st.session_state:
        st.session_state["workflow_modules"] = []

    if len(st.session_state.workflow_modules):
        for i, module in enumerate(st.session_state.workflow_modules):

            col1, col2, col3, _ = st.columns([6, 1, 1, 5])

            with col1:
                st.button(module, key=f"module_number_{i}")

            with col2:
                if st.button("⬆️", key=f"move{i}", help="Move up") and i > 0:
                    st.session_state.workflow_modules.pop(i)
                    st.session_state.workflow_modules.insert(i - 1, module)
                    st.rerun()

            with col3:
                if st.button("❌", key=f"del{i}", help=f"Remove {module} from the workflow"):
                    st.session_state.workflow_modules.pop(i)
                    st.rerun()
    else:
        st.warning("No module has been added to the workflow.")

    module_list = get_module_list(only_active=True)

    available_module_list = sorted(module_list)

    col1, col2 = st.columns(2)

    with col1:
        module = st.selectbox("Module to add to the workflow:", available_module_list)

    with col2:
        # Add vertical spacing to match the label height of selectbox
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("✔", help="Add this module to the workflow"):
            st.session_state.workflow_modules.append(module)
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
