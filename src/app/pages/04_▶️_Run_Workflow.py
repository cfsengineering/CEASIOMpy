"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to run a CEASIOMpy workflow.
"""

# Futures
from __future__ import annotations

# Imports

import psutil
import inspect
import streamlit as st

from html import escape
from textwrap import dedent
from streamlitutils import (
    create_sidebar,
    save_cpacs_file,
)

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow
from typing import (
    Final,
    Callable,
)

from ceasiompy import log
from cpacspy.utils import PARAMS
from constants import BLOCK_CONTAINER

# Constants

# Set the current page in session state
PAGE_NAME: Final[str] = "Run Workflow"

HOW_TO_TEXT: Final[str] = (
    "### Run your workflow \n"
)


# Functions

def _filter_supported_kwargs(fn, **kwargs):
    """Return only kwargs supported by the current Streamlit version."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {}
    return {key: value for key, value in kwargs.items() if key in params}


def _rerun() -> None:
    """Compatibility wrapper for Streamlit rerun."""
    if hasattr(st, "rerun"):
        st.rerun()


def ensure_module_status_css() -> None:
    st.markdown(
        dedent(
            """
        <style>
        .ceasiompy-module-card {
            border-radius: 10px;
            padding: 12px 14px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            margin: 0.5rem 0;
        }
        .ceasiompy-module-card.waiting { background: rgba(243, 244, 246, 0.9); }
        .ceasiompy-module-card.running { background: rgba(254, 249, 195, 0.9); }
        .ceasiompy-module-card.finished { background: rgba(220, 252, 231, 0.9); }
        .ceasiompy-module-card.failed { background: rgba(254, 226, 226, 0.9); }

        .ceasiompy-module-header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: baseline;
            margin-bottom: 0.25rem;
        }
        .ceasiompy-module-title { font-weight: 700; }
        .ceasiompy-module-status { font-weight: 700; text-transform: lowercase; }
        .ceasiompy-module-status.waiting { color: #6b7280; }
        .ceasiompy-module-status.running { color: #ca8a04; }
        .ceasiompy-module-status.finished { color: #16a34a; }
        .ceasiompy-module-status.failed { color: #dc2626; }

        .ceasiompy-module-meta {
            color: rgba(0, 0, 0, 0.65);
            font-size: 0.85rem;
            line-height: 1.2rem;
            margin-top: 0.1rem;
        }

        .ceasiompy-progress {
            height: 10px;
            background: rgba(0, 0, 0, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        .ceasiompy-progress > div { height: 100%; width: 0%; }
        .ceasiompy-progress.running > div { background: #f59e0b; }
        .ceasiompy-progress.finished > div { background: #22c55e; }
        .ceasiompy-progress.failed > div { background: #ef4444; }
        .ceasiompy-progress.waiting > div { background: #9ca3af; }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def ensure_workflow_button_css() -> None:
    st.markdown(
        dedent(
            """
            <style>
            /* Bigger, nicer buttons (only affects this page). */
            .stButton > button {
                height: 3rem;
                border-radius: 999px;
                font-weight: 700;
                border-width: 1px;
            }

            button[kind="primary"] {
                background: linear-gradient(135deg, #2563eb, #06b6d4);
                border: none;
            }
            button[kind="primary"]:hover {
                filter: brightness(0.98);
            }

            /* Make the secondary button look like a "danger" stop. */
            button[kind="secondary"] {
                border-color: rgba(220, 38, 38, 0.35);
            }
            button[kind="secondary"]:hover {
                border-color: rgba(220, 38, 38, 0.6);
                background: rgba(220, 38, 38, 0.06);
            }
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def make_progress_callback(status_container) -> Callable[[list | None], None]:
    """Create a progress callback bound to a placeholder created in this rerun."""

    def _callback(status_list: list | None = None) -> None:
        """Display each module with its current status."""

        if status_list is not None:
            st.session_state.workflow_status_list = status_list

        status_container.empty()

        with status_container.container():
            ensure_module_status_css()
            if status_list is None or not status_list:
                return None

            solver_running = any(
                item.get("status", "waiting") == "running"
                for item in status_list
            )
            has_failed = any(
                item.get("status") == "failed"
                for item in status_list
            )

            finished: bool = True
            for item in status_list:
                name = item.get("name", "Unknown")
                status = item.get("status", "waiting")

                status_class = "waiting"
                if status == "running":
                    status_class = "running"
                    finished = False
                elif status == "finished":
                    status_class = "finished"
                elif status == "failed":
                    status_class = "failed"
                    finished = False
                else:
                    finished = False

                detail = item.get("detail")
                detail_html = (
                    f"<div class='ceasiompy-module-meta'>{escape(str(detail))}</div>"
                    if detail
                    else ""
                )

                progress = item.get("progress")
                progress_value: float | None = None
                if isinstance(progress, (int, float)):
                    progress_value = min(max(float(progress), 0.0), 1.0)

                progress_html = ""
                if progress_value is not None:
                    progress_html = (
                        f"<div class='ceasiompy-progress {status_class}'>"
                        f"<div style='width: {progress_value * 100:.2f}%;'></div>"
                        f"</div>"
                        f"<div class='ceasiompy-module-meta'>{progress_value * 100:.1f}%</div>"
                    )

                eta_seconds = item.get("eta_seconds")
                elapsed_seconds = item.get("elapsed_seconds")
                time_parts: list[str] = []
                if isinstance(elapsed_seconds, (int, float)):
                    time_parts.append(f"elapsed {format_duration(float(elapsed_seconds))}")
                if isinstance(eta_seconds, (int, float)):
                    time_parts.append(f"ETA {format_duration(float(eta_seconds))}")
                time_html = (
                    f"<div class='ceasiompy-module-meta'>{escape(' · '.join(time_parts))}</div>"
                    if time_parts
                    else ""
                )

                with st.container():
                    st.markdown(
                        dedent(
                            f"""
        <div class="ceasiompy-module-card {status_class}">
            <div class="ceasiompy-module-header">
            <div class="ceasiompy-module-title">{escape(str(name))}</div>
            <div class="ceasiompy-module-status {status_class}">{escape(str(status))}</div>
            </div>
            {detail_html}
            {progress_html}
            {time_html}
        </div>
                            """
                        ).strip(),
                        unsafe_allow_html=True,
                    )

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

    return _callback


def lock_navigation() -> None:
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


def unlock_navigation() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stSidebarNav"] {
            pointer-events: auto;
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def terminate_solver_processes() -> None:
    """Terminate known solver processes spawned by workflows."""

    targets = {"avl", "su2_cfd"}
    mpi_wrappers = {"mpirun", "mpiexec", "srun", "orterun", "mpiexec.hydra"}
    to_terminate: list[psutil.Process] = []

    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if any(target in name or target in cmdline for target in targets | mpi_wrappers):
            to_terminate.append(proc)

    for proc in to_terminate:
        try:
            children = proc.children(recursive=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        try:
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        _, alive = psutil.wait_procs(children + [proc], timeout=2.0)
        for leftover in alive:
            try:
                leftover.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


def _run_workflow(
    on_progress: Callable[[list | None], None],
    spinner_slot,
) -> None:
    st.session_state.workflow_is_running = True
    st.session_state.workflow_run_failed = False

    st.session_state.workflow.modules_list = st.session_state.workflow_modules
    st.session_state.workflow.optim_method = "None"
    st.session_state.workflow.module_optim = ["NO"] * len(st.session_state.workflow.modules_list)
    st.session_state.workflow.write_config_file()

    working_dir = Path(st.session_state.workflow.working_dir)
    workflow_idx = str(st.session_state.workflow.workflow_dir).split(sep="_")[1]
    config_path = Path(working_dir, "ceasiompy.cfg")

    workflow = Workflow()
    workflow.from_config_file(config_path)
    workflow.set_workflow()

    # Lock user in this page
    lock_navigation()
    if st.sidebar.button(
        label="Stop ✖️",
        help="Terminate the workflow",
        type="secondary",
        **_filter_supported_kwargs(st.sidebar.button, width="stretch"),
        key="stop_workflow_sidebar",
    ):
        terminate_solver_processes()
        unlock_navigation()
    st.sidebar.warning("Workflow running. Stop it to unlock navigation.")

    try:
        with spinner_slot.container():
            with st.spinner(
                f"CEASIOMpy is running Workflow {workflow_idx}",
                **_filter_supported_kwargs(st.spinner, show_time=True),
            ):
                workflow.run_workflow(progress_callback=on_progress)
    except Exception as exc:
        log.error(f"Workflow failed: {exc}")
        st.exception(exc)
        st.session_state.workflow_run_failed = True
    finally:
        st.session_state.workflow_is_running = False
        spinner_slot.empty()

    status_list = st.session_state.get("workflow_status_list", [])
    has_failed = any(item.get("status") == "failed" for item in status_list)
    if st.session_state.get("workflow_run_failed") or has_failed:
        unlock_navigation()
        st.stop()
        return None

    # Workflow finished successfully: unlock navigation and redirect to Results.
    unlock_navigation()
    results_page = "pages/05_📈_Results.py"
    try:
        st.switch_page(results_page)
        # Some Streamlit versions don't immediately rerun after `switch_page`.
        _rerun()
    except Exception as exc:
        log.error(f"Page switch to Results failed: {exc}")
        st.session_state["workflow_page_switch_error"] = str(exc)
        st.success("Workflow finished running.")
        if st.button(
            "Go to Results",
            type="primary",
            **_filter_supported_kwargs(st.button, width="stretch"),
            key="go_to_results_after_workflow",
        ):
            st.switch_page(results_page)
            _rerun()
        st.stop()
        return None

    st.stop()


def workflow_runner(run_enabled: bool) -> None:
    ensure_workflow_button_css()

    st.markdown("---")
    if not run_enabled:
        st.info("Complete the required setup above to enable running a workflow.")
        return None

    run_clicked = st.button(
        label=f"""Run: **{" → ".join(st.session_state.workflow_modules)}**""",
        help="Run the workflow",
        type="primary",
        **_filter_supported_kwargs(st.button, width="stretch"),
    )

    spinner_slot = st.empty()
    status_placeholder = st.empty()
    on_progress = make_progress_callback(status_placeholder)
    on_progress(st.session_state.get("workflow_status_list"))

    if run_clicked:
        _run_workflow(on_progress, spinner_slot)


def display_simulation_settings() -> None:
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


# Main
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

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file have been selected!")
        display_geometry_view = False
    else:
        save_cpacs_file()

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

    run_enabled = display_geometry_view and display_workflow_view and display_simulation_view

    if display_simulation_view:
        st.markdown("---")
        display_simulation_settings()

    workflow_runner(run_enabled)

    # Update last_page
    st.session_state.last_page = PAGE_NAME
