import os
from pathlib import Path

import ceasiompy.__init__
import streamlit as st
from streamlit_autorefresh import st_autorefresh

CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

st.set_page_config(page_title="Run workflow", page_icon="🔄")
st.title("Run workflow")

# Custom CSS
st.markdown(
    """
    <style>
    .css-148uddy  {
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


run_workflow_button()
show_logs()

st_autorefresh(interval=1000, limit=10000, key="auto_refresh")
