"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit home page for CEASIOMpy GUI

| Author: Giacomo Benedetti
| Creation: 2026-01-26
"""

# Imports


import streamlit as st

from importlib.metadata import version
from streamlitutils import create_sidebar

from importlib.metadata import PackageNotFoundError

from constants import BLOCK_CONTAINER

# ==============================================================================
#   CONSTANTS
# ==============================================================================

PAGE_NAME = "Welcome to CEASIOMpy"

try:
    VERSION = version("ceasiompy")
except PackageNotFoundError:
    VERSION = "unknown"

HOW_TO_TEXT = (
    "### Welcome !\n"
    "CEASIOMpy allows you to:\n"
    "- Design Easily\n"
    "- Run workflows\n"
    "- Analyze results\n\n"
)

# ==============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS to make the page full width
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

    # Page title
    st.title(PAGE_NAME)

    st.markdown("---")

    st.markdown(
        f"""
        **CEASIOMpy** (`v.{VERSION}`) is a Conceptual Aircraft Design Software developed by
        [CFS Engineering](https://cfse.ch/#navigation).
        """
    )

    st.markdown(
        """
        ### Start Up Guide

        Run your CFD simulations with ease by following these steps:

        1. **✈️ Geometry** - Upload your existing geometry (STL, VSP, CPACS)
        2. **➡ Workflow** - Create a workflow by selecting the modules of your interest
        3. **⚙️ Settings** - Choose your simulation parameters
        4. **▶️ Run Workflow** - Verify your configuration and run your workflow
        5. **📈 Results** - Check and analyze your results
        """
    )

    st.markdown("---")

    # Information boxes
    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "📖 **Documentation**\n\n"
            "Module's Details available "
            "[here](https://github.com/cfsengineering/CEASIOMpy/"
            "tree/main?tab=readme-ov-file#available-modules)."
        )

    with col2:
        st.info(
            "![YouTube logo](https://www.youtube.com/favicon.ico) "
            "**YouTube**\n\n"
            "Watch "
            "[YouTube tutorials](https://www.youtube.com/@cfs_engineering)."
        )

    # Add last_page to session state
    st.session_state.last_page = PAGE_NAME
