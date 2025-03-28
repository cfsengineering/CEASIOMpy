"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit utils functions for CEASIOMpy

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-12-01

TODO:

"""

from pathlib import Path

from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH
from PIL import Image

import streamlit as st


def create_sidebar(how_to_text):
    """Create side bar with a text explaining how the page should be used."""

    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(page_title="CEASIOMpy", page_icon=im)
    st.sidebar.image(im)
    st.sidebar.markdown(how_to_text)


def st_directory_picker(initial_path=Path()):
    """Workaround to be able to select a directory with Streamlit. Could be remove when this
    function will be integrated into Streamlit."""

    if "path" not in st.session_state:
        st.session_state.path = initial_path.absolute().resolve()

    manual_input = st.text_input("Selected directory:", st.session_state.path)

    manual_input = Path(manual_input)
    if manual_input != st.session_state.path:
        st.session_state.path = manual_input
        st.experimental_rerun()

    _, col1, col2, col3, _ = st.columns([3, 1, 3, 1, 3])

    with col1:
        st.markdown("#")
        if st.button("⬅️") and "path" in st.session_state:
            st.session_state.path = st.session_state.path.parent
            st.experimental_rerun()

    with col2:
        subdirectroies = [
            f.stem
            for f in st.session_state.path.iterdir()
            if f.is_dir() and (not f.stem.startswith(".") and not f.stem.startswith("__"))
        ]
        if subdirectroies:
            st.session_state.new_dir = st.selectbox("Subdirectories", sorted(subdirectroies))
        else:
            st.markdown("#")
            st.markdown("<font color='#FF0000'>No subdir</font>", unsafe_allow_html=True)

    with col3:
        if subdirectroies:
            st.markdown("#")
            if st.button("➡️") and "path" in st.session_state:
                st.session_state.path = Path(st.session_state.path, st.session_state.new_dir)
                st.experimental_rerun()

    return st.session_state.path
