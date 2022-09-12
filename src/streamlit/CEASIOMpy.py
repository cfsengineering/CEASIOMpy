from pathlib import Path

from ceasiompy.utils.commonpaths import CEASIOMPY_PATH
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacspy import CPACS

import streamlit as st
from directory_picker import st_directory_picker


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

col1, col2 = st.columns(2)

with col1:
    st.markdown("##")
    st.markdown("Use the sidebar to navigate to the different pages.")

    st.markdown("[Github repository](https://github.com/cfsengineering/CEASIOMpy)")

    # Add button to change page when available

with col2:
    st.image(str(Path(CEASIOMPY_PATH, "documents/logos/CEASIOMpy_main_logos.png")), width=350)

section_select_working_dir()
section_select_cpacs()
