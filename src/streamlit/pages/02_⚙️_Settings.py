"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to change settings of a CEASIOMpy workflow


| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from src.streamlit.moduletab import add_module_tab

from streamlitutils import (
    create_sidebar,
    save_cpacs_file,
)

# ==============================================================================
#   CONSTANTS
# ==============================================================================

HOW_TO_TEXT = (
    "### How to use Settings?\n"
    "1. With *Edit aeromap* you can create or modify an aeromap\n"
    "1. Through each tab you can modify the settings of each module\n"
    "1. Once finished, go to the *Run Workflow* page\n"
)

PAGE_NAME = "Settings"

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def section_settings():
    if "workflow_modules" not in st.session_state:
        st.warning("No module selected!")
        return

    if not len(st.session_state.workflow_modules):
        st.warning("You must first build a workflow in the corresponding tab.")

    add_module_tab()

    # Make sure to run at least once to pre-load the default values
    # of __specs__.py files. Then save each modifications independently.
    # Important: Needs to be called after add_module_tab.
    if "save_cpacs_file_run" not in st.session_state:
        save_cpacs_file()
        st.session_state.save_cpacs_file_run = True

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
            background-color: #9e9e93;
            padding: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    section_settings()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
