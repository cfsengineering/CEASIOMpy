"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to run a CEASIOMpy workflow

| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# Futures
from __future__ import annotations

# ==============================================================================
#   IMPORTS
# ==============================================================================

import psutil
import streamlit as st

from CEASIOMpyStreamlit.streamlitutils import (
    create_sidebar,
    save_cpacs_file,
)

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow


# ==============================================================================
#   CONSTANTS
# ==============================================================================

# Set the current page in session state
PAGE_NAME = "Run Workflow"
STATUS_PLACEHOLDER_KEY = "workflow_status_placeholder"

HOW_TO_TEXT = (
    "### How to Run your workflow?\n"
    "1. Click on the *Run* button\n"
    "Some workflows takes time, you can always check the LogFile \n\n"
    "2. When it is done, go to the *Results* page\n"
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_status_placeholder():
    """Get or create the placeholder used to display module status."""

    if STATUS_PLACEHOLDER_KEY not in st.session_state:
        st.session_state[STATUS_PLACEHOLDER_KEY] = st.empty()
    return st.session_state[STATUS_PLACEHOLDER_KEY]


def progress_callback(status_list: list = None) -> None:
    """Display each module with its current status."""

    if status_list is not None:
        st.session_state.workflow_status_list = status_list

    status_container = get_status_placeholder()
    status_container.empty()

    with status_container.container():
        if status_list is None or not status_list:
            st.write("No workflow is running.")
            return None

        solver_running = any(item.get("status", "waiting") == "running" for item in status_list)
        has_failed = any(item.get("status") == "failed" for item in status_list)

        finished: bool = True
        for item in status_list:
            name = item.get("name", "Unknown")
            status = item.get("status", "waiting")

            if status == "running":
                icon = "🟡"
                finished = False
            elif status == "finished":
                icon = "🟢"
            elif status == "failed":
                icon = "❌"
                finished = False
            else:
                icon = "⚪"
                finished = False

            st.write(f"{icon} **{name}** — {status}")

        if has_failed:
            errors = [
                f"- {item.get('name', 'Unknown')}: {item.get('error', 'Unknown error')}"
                for item in status_list
                if item.get("status") == "failed"
            ]
            err_msg = "Workflow failed.\n" + "\n".join(errors)
            st.error(err_msg)
        elif not solver_running and finished:
            st.info("Workflow finished running, go in results page for analysis.")


def terminate_solver_processes() -> None:
    """Terminate known solver processes spawned by workflows."""

    targets = {"avl", "su2_cfd", "su2_cfd.exe"}
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if any(target in name or target in cmdline for target in targets):
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


def workflow_buttons() -> None:
    """
    Run workflow button.
    """

    # Create two buttons side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Run ▶️", help="Run the workflow"):
            st.session_state.workflow.modules_list = st.session_state.workflow_modules
            st.session_state.workflow.optim_method = "None"
            st.session_state.workflow.module_optim = ["NO"] * len(
                st.session_state.workflow.modules_list
            )
            st.session_state.workflow.write_config_file()

            # Run workflow from an external script (separate process)
            config_path = Path(st.session_state.workflow.working_dir, "ceasiompy.cfg")
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            workflow = Workflow()
            workflow.from_config_file(config_path)
            workflow.set_workflow()

            with st.spinner(
                'CEASIOMpy is running...',
                show_time=True,
            ):
                workflow.run_workflow(progress_callback=progress_callback)

    with col2:
        if st.button("Stop ✖️", help="Terminate the workflow"):
            terminate_solver_processes()


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
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
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
        workflow_buttons()
        _, right_col = st.columns(spec=[0.01, 0.99])
        with right_col:
            progress_callback(st.session_state.get("workflow_status_list"))

    # Update last_page
    st.session_state.last_page = PAGE_NAME
