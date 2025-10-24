"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to run a CEASIOMpy workflow

| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import psutil
import signal
import streamlit as st

from streamlit_autorefresh import st_autorefresh
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from streamlitutils import (
    create_sidebar,
    save_gui_settings,
)

from pathlib import Path

from ceasiompy import LOGFILE

# ==============================================================================
#   CONSTANTS
# ==============================================================================

# Set the current page in session state
PAGE_NAME = "Run Workflow"

HOW_TO_TEXT = (
    "### How to Run your workflow?\n"
    "1. Click on the *Run* button\n"
    "Some workflows takes time, you can always check the LogFile \n\n"
    "2. When it is done, go to the *Results* page\n"
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def terminate_previous_workflows() -> None:
    """
    Terminate any previously running workflow processes.
    """
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            # Check if the process is running the workflow script
            if "python" in proc.info["name"] and "runworkflow.py" in proc.info["cmdline"]:
                # Terminate the process
                os.kill(proc.info["pid"], signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def workflow_buttons() -> None:
    """
    Run workflow button.
    """

    # Create two buttons side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Run ▶️", help="Run the workflow"):
            terminate_previous_workflows()

            st.session_state.workflow.modules_list = st.session_state.workflow_modules
            st.session_state.workflow.optim_method = "None"
            st.session_state.workflow.module_optim = ["NO"] * len(
                st.session_state.workflow.modules_list
            )
            st.session_state.workflow.write_config_file()

            # Run workflow from an external script
            config_path = Path(current_workflow_dir(), "ceasiompy.cfg")
            os.system(f"python runworkflow.py {config_path} &")

    with col2:
        if st.button("Terminate ✖️", help="Terminate the workflow"):
            terminate_previous_workflows()


def show_logs() -> None:
    """
    Log interface.
    """

    st.markdown("")
    st.markdown("##### Logfile")

    with open(LOGFILE, "r") as f:
        lines = f.readlines()

    lines_str = "\n".join(reversed(lines))

    st.text_area("(more recent on top)", lines_str, height=400, disabled=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    # Define Interface
    create_sidebar(HOW_TO_TEXT)

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

    st.title(PAGE_NAME)

    if "last_page" in st.session_state and st.session_state.last_page != PAGE_NAME:
        save_gui_settings()

    workflow_buttons()
    show_logs()

    # AutoRefresh for logs
    st_autorefresh(interval=1000, limit=10000, key="auto_refresh")

    # Update last_page
    st.session_state.last_page = PAGE_NAME
