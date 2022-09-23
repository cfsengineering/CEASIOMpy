from pathlib import Path

from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacspy import CPACS
from PIL import Image

import streamlit as st
from directory_picker import st_directory_picker

im = Image.open(CEASIOMPY_LOGO_PATH)
st.set_page_config(page_title="CEASIOMpy", page_icon=im)


def section_select_working_dir():

    st.markdown("#### Working directory")

    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()
    st.session_state.workflow.working_dir = st_directory_picker(Path("../../WKDIR").absolute())


def section_select_cpacs():

    st.markdown("#### CPACS file")

    st.session_state.cpacs_file = st.file_uploader("Select a CPACS file", type=["xml"])

    if st.session_state.cpacs_file:

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )

        with open(cpacs_new_path, "wb") as f:
            f.write(st.session_state.cpacs_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        st.session_state.cpacs = CPACS(cpacs_new_path)

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")

        if "cpacs" not in st.session_state:
            st.session_state.cpacs = CPACS(cpacs_new_path)

    else:
        st.warning("No CPACS file has been selected!")


st.title("CEASIOMpy")

col1, col2 = st.columns([5, 3])

with col1:
    st.markdown("### How to use CEASIOMpy?")
    st.markdown("- Select a Working directory")
    st.markdown("- Select a CPACS file")
    st.markdown("- Use the side bar to go to the Workflow page")

with col2:
    st.image(str(CEASIOMPY_LOGO_PATH), width=220)

section_select_working_dir()
section_select_cpacs()
