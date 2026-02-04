"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to change settings of a CEASIOMpy workflow

| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# Imports

import streamlit as st

from streamlitutils import create_sidebar
from ceasiompy.utils.moduletab import add_module_tab

from constants import BLOCK_CONTAINER

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

    st.markdown("---")

    add_module_tab()


# Main

if __name__ == "__main__":

    # Define interface
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
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

    # Check if CPACS file exists (either in session state or on disk)
    display_settings = "cpacs" in st.session_state
    if not display_settings:
        st.warning("No CPACS file has been selected!")

    if display_settings:
        section_settings()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
