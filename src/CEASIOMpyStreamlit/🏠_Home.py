"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit home page for CEASIOMpy GUI

| Author: Giacomo Benedetti
| Creation: 2026-01-26

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from PIL import Image
from CEASIOMpyStreamlit.streamlitutils import create_sidebar
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH

# ==============================================================================
#   CONSTANTS
# ==============================================================================

PAGE_NAME = "Home"
VERSION = "0.2.0"

HOW_TO_TEXT = (
    "### Welcome to CEASIOMpy!\n"
    "CEASIOMpy is a Conceptual Aircraft Design Software that allows you to:\n"
    "- Design aircraft geometry\n"
    "- Create and run aerodynamic workflows\n"
    "- Analyze results\n\n"
    "Use the menu on the left to navigate between pages."
)

# ==============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":
    # Set page config with CEASIOMpy logo (must be first Streamlit command)
    logo = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(page_title="CEASIOMpy", page_icon=logo, layout="wide")

    # Create sidebar manually (without calling create_sidebar to avoid double set_page_config)
    st.sidebar.image(logo)
    st.sidebar.markdown(HOW_TO_TEXT)

    # Custom CSS to make the page full width
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 100%;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Page title
    st.title("🏠 " + PAGE_NAME)

    # Welcome section with logo
    st.markdown("---")

    col_text, col_logo = st.columns([3, 1])

    with col_text:
        st.markdown("## Welcome to CEASIOMpy")

        st.markdown(f"""
        **CEASIOMpy** is a Conceptual Aircraft Design Software developed for CFS ENGINEERING.

        Current version: `{VERSION}`

        ### Quick Start Guide

        1. **Geometry** - Design your aircraft or upload an existing geometry
        2. **Workflow** - Create a workflow by selecting analysis modules
        3. **Settings** - Configure the parameters for your analysis
        4. **Run Workflow** - Execute your workflow
        5. **Results** - View and analyze the results
        """)

    with col_logo:
        st.image("../../documents/logos/CEASIOMpy_512px.png", width=250)

    st.markdown("""
    ### Features

    - 🛩️ Aircraft geometry design and manipulation
    - 🔄 Flexible workflow creation
    - 📊 Aerodynamic analysis (AVL, SU2)
    - 📈 Results visualization
    - 🤖 Surrogate modeling capabilities

    ### Getting Started

    Use the navigation menu on the left to access different pages of the application.
    Start with the **Geometry** page to load or create your aircraft model.
    """)

    st.markdown("---")

    # Information boxes
    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "📖 **Documentation**\n\n"
            "For detailed information, visit the "
            "[CEASIOMpy documentation](https://github.com/cfsengineering/CEASIOMpy/"
            "tree/main?tab=readme-ov-file#available-modules)"
        )

    with col2:
        st.info(
            "💻 **GitHub**\n\n"
            "Contribute or report issues on "
            "[GitHub](https://github.com/cfsengineering/CEASIOMpy)"
        )

    st.markdown("---")

    # Footer
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
    Developed by CFS ENGINEERING, Lausanne, Switzerland
    </div>
    """, unsafe_allow_html=True)

    # Add last_page to session state
    st.session_state.last_page = PAGE_NAME
