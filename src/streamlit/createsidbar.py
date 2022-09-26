
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH
from PIL import Image

import streamlit as st


def create_sidebar(how_to_text):
    
    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(page_title="CEASIOMpy", page_icon=im)
    st.sidebar.image(im)
    st.sidebar.markdown(how_to_text)
    