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
import json
import streamlit as st

from streamlit_autorefresh import st_autorefresh
from CEASIOMpyStreamlit.streamlitutils import (
    create_sidebar,
    save_cpacs_file,
    rm_wkflow_status,
    get_last_workflow,
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

    rm_wkflow_status()


def get_modules_status():
    """Load the module status of the last workflow if available."""

    if "workflow" not in st.session_state:
        return None

    wkflow_dir = get_last_workflow()
    if wkflow_dir is None:
        return None

    status_file = Path(wkflow_dir, "workflow_status.json")
    if not status_file.exists():
        return None

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def display_modules_status() -> None:
    """Display each module with its current status."""

    status_list = get_modules_status()
    if not status_list:
        st.write("No workflow is running.")
        return None

    solver_running: bool = False
    for item in status_list:
        if item.get("status", "waiting") == "running":
            solver_running = True
            break

    st.markdown("#### Modules status")
    if solver_running:
        for item in status_list:
            name = item.get("name", "Unknown")
            status = item.get("status", "waiting")

            if status == "running":
                icon = "🟡"
            elif status == "finished":
                icon = "🟢"
            else:
                icon = "⚪"

            st.write(f"{icon} **{name}** — {status}")
    else:
        st.info(
            "Workflow finished running, "
            "go in results page for analysis."
        )


def workflow_buttons() -> None:
    """
    Run workflow button.
    """

    # Create two buttons side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Run ▶️", help="Run the workflow"):
            rm_wkflow_status()
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
        if st.button("Stop ✖️", help="Terminate the workflow"):
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

    display_buttons: bool = True
    if "last_page" in st.session_state and st.session_state.last_page != PAGE_NAME:
        save_cpacs_file(logging=False)

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file have been selected!")
        display_buttons = False

    if "workflow_modules" not in st.session_state or st.session_state.workflow_modules == []:
        st.warning("No modules have been selected!")
        display_buttons = False

    if display_buttons:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            display_modules_status()
        with col_right:
            workflow_buttons()

    # AutoRefresh for logs
    st_autorefresh(interval=1000, limit=10000, key="auto_refresh")

    # Update last_page
    st.session_state.last_page = PAGE_NAME
