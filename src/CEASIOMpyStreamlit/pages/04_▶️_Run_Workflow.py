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
    section_3D_view,
)

from pathlib import Path
from typing import Final
from ceasiompy.utils.workflowclasses import Workflow

from cpacspy.utils import PARAMS
from CEASIOMpyStreamlit import BLOCK_CONTAINER

# ==============================================================================
#   CONSTANTS
# ==============================================================================

# Set the current page in session state
PAGE_NAME: Final[str] = "Run Workflow"
STATUS_PLACEHOLDER_KEY: Final[str] = "workflow_status_placeholder"

HOW_TO_TEXT: Final[str] = (
    "### How to Run your workflow?\n"
    "1. Click on the *Run* button\n"
    "Some workflows takes time, you can always check the LogFile \n\n"
    "2. When it is done, go to the *Results* page\n"
)

SPEC_SETTINGS: Final[list[float]] = [0.3, 0.7]

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

    targets = {"avl", "su2_cfd"}
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
    col1, col2 = st.columns([1.0, 1.0])

    with col1:
        if st.button(
            label="Run ▶️",
            help="Run the workflow",
        ):
            if "workflow" not in st.session_state:
                st.error(
                    "Load a CPACS file in the Geometry page first."
                )
                return None

            st.session_state.workflow.modules_list = st.session_state.workflow_modules
            st.session_state.workflow.optim_method = "None"
            st.session_state.workflow.module_optim = ["NO"] * len(
                st.session_state.workflow.modules_list
            )
            st.session_state.workflow.write_config_file()

            # Run workflow from an external script (separate process)
            config_path = Path(st.session_state.workflow.working_dir, "ceasiompy.cfg")
            if not config_path.exists():
                st.error(f"Config file not found: {config_path}")
                return None

            workflow = Workflow()
            workflow.from_config_file(config_path)
            workflow.set_workflow()

            with st.spinner(
                'CEASIOMpy is running...',
                show_time=True,
            ):
                # Lock user in this page
                st.markdown(
                    """
                    <style>
                    div[data-testid="stSidebarNav"] {
                        pointer-events: none;
                        opacity: 0.5;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.sidebar.warning("Workflow running. Stop it to unlock navigation.")
                try:
                    workflow.run_workflow(progress_callback=progress_callback)
                except Exception as exc:
                    st.exception(exc)
                st.switch_page("pages/04_📈_Results.py")
                st.stop()

    with col2:
        if st.button(
            label="Stop ✖️",
            help="Terminate the workflow",
        ):
            terminate_solver_processes()


def display_reference_geometry() -> None:
    left_col, right_col = st.columns(
        spec=SPEC_SETTINGS
    )
    with left_col:
        st.markdown("#### ✈️ Geometry")

    with right_col:
        section_3D_view(force_regenerate=True, height=200)


def display_simulation_settings() -> None:
    left_col, right_col = st.columns(
        spec=SPEC_SETTINGS
    )

    with left_col:
        st.markdown("#### ⚙️ Settings")

    with right_col:
        selected_aeromap = st.session_state.cpacs.get_aeromap_by_uid(selected_aeromap_id)
        aero_df = selected_aeromap.df[PARAMS].reset_index(drop=True)

        st.markdown(f"Using AeroMap: **{selected_aeromap_id}**")
        st.dataframe(
            aero_df,
            hide_index=True,
            column_config={
                "altitude": st.column_config.NumberColumn("Altitude", min_value=0.0),
                "machNumber": st.column_config.NumberColumn("Mach", min_value=1e-2),
                "angleOfAttack": st.column_config.NumberColumn("α°"),
                "angleOfSideslip": st.column_config.NumberColumn("β°"),
            },
            column_order=["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"],
        )


def display_workflow_settings() -> None:
    left_col, right_col = st.columns(
        spec=SPEC_SETTINGS
    )
    with left_col:
        st.markdown("#### ➡ Workflow")
    with right_col:
        st.button(" → ".join(st.session_state.workflow_modules))


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
        """
        + BLOCK_CONTAINER
        + """
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

    display_geometry_view: bool = True
    display_workflow_view: bool = True
    display_simulation_view: bool = True

    if "last_page" in st.session_state and st.session_state.last_page != PAGE_NAME:
        save_cpacs_file(logging=False)

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file have been selected!")
        display_geometry_view = False

    if "workflow" not in st.session_state:
        st.warning("Workflow is not initialized. Load a CPACS file in the Geometry page first.")
        display_workflow_view = False

    if "workflow_modules" not in st.session_state or st.session_state.workflow_modules == []:
        st.warning("No modules have been selected!")
        display_workflow_view = False

    selected_aeromap_id = st.session_state.get("selected_aeromap_id", None)
    if selected_aeromap_id is None:
        st.warning("No aeromap has been selected, go to the Settings Page.")
        display_simulation_view = False

    if display_geometry_view:
        st.markdown("---")
        display_reference_geometry()

    if display_workflow_view:
        st.markdown("---")
        display_workflow_settings()

    if display_simulation_view:
        st.markdown("---")
        display_simulation_settings()

    if display_geometry_view and display_simulation_view:
        st.markdown("---")

        workflow_buttons()
        _, right_col = st.columns(spec=[0.01, 0.99])
        with right_col:
            progress_callback(st.session_state.get("workflow_status_list"))

    # Update last_page
    st.session_state.last_page = PAGE_NAME
