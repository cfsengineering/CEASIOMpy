import streamlit as st
from pathlib import Path
from ceasiompy.utils.commonpaths import CEASIOMPY_PATH


st.title("CEASIOMpy")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##")
    st.markdown("Use the sidebar to navigate to the different pages.")

    st.markdown("[Github repository](https://github.com/cfsengineering/CEASIOMpy)")

    # Add button to change page when available

with col2:
    st.image(str(Path(CEASIOMPY_PATH, "documents/logos/CEASIOMpy_main_logos.png")), width=350)
