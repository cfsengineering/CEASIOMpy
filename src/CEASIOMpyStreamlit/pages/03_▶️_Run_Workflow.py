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

import sys
import psutil
import subprocess
import streamlit as st

from streamlit_autorefresh import st_autorefresh
from streamlitutils import (
    create_sidebar,
    save_cpacs_file,
)

from pathlib import Path


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
    # First, terminate the workflow process tracked in the Streamlit session (if any)
    workflow_pid = st.session_state.get("workflow_pid")
    if workflow_pid is not None:
        try:
            proc = psutil.Process(workflow_pid)

            # Terminate child processes first
            for child in proc.children(recursive=True):
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            proc.terminate()
            _, alive = psutil.wait_procs([proc], timeout=3)

            # Force kill remaining processes if they did not terminate gracefully
            for p in alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        finally:
            # Clear stored PID even if something went wrong
            st.session_state["workflow_pid"] = None

    # Fallback: look for any stray runworkflow.py processes and terminate them
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if any("runworkflow.py" in part for part in cmdline):
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


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

            # Run workflow from an external script (separate process)
            config_path = Path(st.session_state.workflow.working_dir, "ceasiompy.cfg")
            script_path = Path(__file__).resolve().parents[1] / "runworkflow.py"

            # Launch the workflow in a separate process so it can be
            # terminated independently of the Streamlit GUI.
            process = subprocess.Popen(
                [sys.executable, str(script_path), str(config_path)],
                cwd=script_path.parent,
            )

            # Store the PID so that terminate_previous_workflows can stop it later
            st.session_state["workflow_pid"] = process.pid

    with col2:
        if st.button("Terminate ✖️", help="Terminate the workflow"):
            terminate_previous_workflows()


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
        save_cpacs_file()

    workflow_buttons()

    # AutoRefresh for logs
    st_autorefresh(interval=1000, limit=10000, key="auto_refresh")

    # Update last_page
    st.session_state.last_page = PAGE_NAME
