"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to run a CEASIOMpy workflow

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-09-16

TODO:

"""

import os
from pathlib import Path

import ceasiompy.__init__
import streamlit as st
from createsidbar import create_sidebar
from streamlit_autorefresh import st_autorefresh

CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

how_to_text = (
    "### How to Run your workflow?\n"
    "1. Just click on the *Run* button\n"
    "Depending your workflow it could take time to get result, you can see the logs of what's "
    "happening.\n\n"
    "2. When it is done, go to the *Results* page\n"
)

create_sidebar(how_to_text)

# Custom CSS
st.markdown(
    """
    <style>
    .css-4u7rgp  {
        padding: 15px;
        font-size: 20px;
        border-radius:10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_workflow_button():
    if st.button("Run ▶️", help="Run the workflow "):

        # save_cpacs_file()

        st.session_state.workflow.modules_list = st.session_state.workflow_modules
        st.session_state.workflow.optim_method = "None"
        st.session_state.workflow.module_optim = ["NO"] * len(
            st.session_state.workflow.modules_list
        )
        st.session_state.workflow.write_config_file()

        # Run workflow from an external script
        config_path = Path(st.session_state.workflow.working_dir, "ceasiompy.cfg")
        os.system(f"python run_workflow.py {config_path}  &")


def show_logs():

    st.markdown("")
    st.markdown("##### Logfile")

    with open(LOGFILE, "r") as f:
        lines = f.readlines()

    lines_str = "\n".join(reversed(lines))

    st.text_area("(more recent on top)", lines_str, height=300, disabled=True)


st.title("Run workflow")

run_workflow_button()
show_logs()

st_autorefresh(interval=1000, limit=10000, key="auto_refresh")
