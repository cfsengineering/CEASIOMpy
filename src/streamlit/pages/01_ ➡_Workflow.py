"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to create a CEASIOMpy workflow

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2022-09-16
| Modified: Leon Deligny
| Date: 07-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.moduleinterfaces import get_module_list
from streamlitutils import create_sidebar

# ==============================================================================
#   CONSTANTS
# ==============================================================================

PAGE_NAME = "Workflow"

HOW_TO_TEXT = (
    "### How to use Create a workflow?\n"
    "You can either:\n"
    "- Select a predefined workflow and modify it\n"
    "- Build your own workflow by selecting among available modules\n"
    "When it is done, go to the *Settings* page\n"
)


# ==============================================================================
#   FUNCTIONS
# ==============================================================================

def section_predefined_workflow():
    """
    Where to define the Pre-defined workflows.
    """

    st.markdown("#### Predefined Workflows")

    predefine_workflows = [
        ["PyAVL", "DynamicStability", "Database"],
        ["CPACSUpdater", "CPACSCreator", "CPACS2GMSH", "Database"],
        ["SU2Run", "Database"],
        ["CPACS2GMSH", "SU2Run", "SkinFriction"],
        # ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run", "ExportCSV"],
        ["CPACS2GMSH", "ThermoData", "SU2Run"],
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
                st.button(
                    module,
                    key=f"module_number_{i}"
                )

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
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS
    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    section_predefined_workflow()

    st.markdown("---")

    section_add_module()

    st.markdown("---")

    # Add last_page
    st.session_state.last_page = PAGE_NAME
