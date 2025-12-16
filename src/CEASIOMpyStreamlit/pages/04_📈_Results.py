"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy

| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# =================================================================================================
#    IMPORTS
# =================================================================================================

import os

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from streamlit_autorefresh import st_autorefresh
from ceasiompy.utils.commonpaths import get_wkdir
from CEASIOMpyStreamlit.streamlitutils import (
    create_sidebar,
    get_last_workflow,
    highlight_stability,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from cpacspy.utils import PARAMS_COEFS
from ceasiompy.utils.commonpaths import DEFAULT_PARAVIEW_STATE

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT = (
    "### How to check your results\n"
    "1. Select an aeromap(s) \n"
    "1. Choose the parameters to plot\n"
    "1. Save the figure\n"
    "1. Check the results for each module\n"
)

PAGE_NAME = "Results"

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def clear_containers(container_list):
    """Delete the session_state variable of a list of containers."""

    for container in container_list:
        if container in st.session_state:
            del st.session_state[container]


def display_results_else(path):
    if path.is_dir():
        for child in path.iterdir():
            display_results(child)
    else:
        st.text_area(path.stem, path.read_text(), height=200, key=str(path))


def display_results(results_dir):
    try:
        # """Display results depending which type of file they are."""

        container_list = ["logs_container", "figures_container", "paraview_container"]
        clear_containers(container_list)

        for child in sorted(Path(results_dir).iterdir()):

            if child.suffix == ".smx":
                if st.button(f"Open {child.name} with SUMO", key=f"{child}_sumo_geom"):
                    os.system(f"dwfsumo {str(child)}")

            elif child.suffix == ".su2":
                if st.button(f"Open {child.name} with Scope", key=f"{child}_su2_mesh"):
                    os.system(f"dwfscope {str(child)}")

            elif child.suffix == ".vtu":
                if "paraview_container" not in st.session_state:
                    st.session_state["paraview_container"] = st.container()
                    st.session_state.paraview_container.markdown("**Paraview**")

                if st.session_state.paraview_container.button(
                    f"Open {child.name} with Paraview", key=f"{child}_vtu"
                ):
                    open_paraview(child)

            elif child.suffix == ".png":
                if "figures_container" not in st.session_state:
                    st.session_state["figures_container"] = st.container()
                    st.session_state.figures_container.markdown("**Figures**")

                st.session_state.figures_container.markdown(f"{child.stem.replace('_', ' ')}")
                st.session_state.figures_container.image(str(child))

            elif child.suffix == ".md":
                md_text = child.read_text()
                # Simple table highlighting for "Stable"/"Unstable"

                html = highlight_stability(md_text)
                st.markdown(html, unsafe_allow_html=True)

            elif child.suffix == ".json":
                st.text_area(child.stem, child.read_text(), height=200)

            elif child.suffix == ".log" or child.suffix == ".txt":
                if "logs_container" not in st.session_state:
                    st.session_state["logs_container"] = st.container()
                    st.session_state.logs_container.markdown("**Logs**")
                st.session_state.logs_container.text_area(
                    child.stem, child.read_text(), height=200
                )

            elif child.name == "history.csv":
                st.markdown("**Convergence**")

                df = pd.read_csv(child)
                df.rename(columns=lambda x: x.strip().strip('"'), inplace=True)

                st.line_chart(df[["CD", "CL", "CMy"]])
                st.line_chart(df[["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoW]", "rms[RhoE]"]])

            elif child.suffix == ".csv":
                st.markdown(f"**{child.name}**")
                st.dataframe(pd.read_csv(child))

            # elif "Case" in child.name and child.is_dir():
            elif child.is_dir():
                with st.expander(child.stem, expanded=False):
                    display_results(child)

    except BaseException:
        display_results_else(results_dir)


def open_paraview(file):
    """Open Paraview with the file pass as argument."""

    paraview_state_txt = DEFAULT_PARAVIEW_STATE.read_text()
    paraview_state = Path(file.parent, "paraview_state.pvsm")
    paraview_state.write_text(paraview_state_txt.replace("result_case_path", str(file)))

    os.system(f"paraview {str(paraview_state)}")


def workflow_number(path: Path) -> int:
    parts = path.name.split("_")
    if parts and parts[-1].isdigit():
        return int(parts[-1])
    return -1


def get_workflow_dirs(current_wkdir: Path) -> list[Path]:
    if not current_wkdir.exists():
        return []
    workflow_dirs = [
        wkflow
        for wkflow in current_wkdir.iterdir()
        if wkflow.is_dir() and wkflow.name.startswith("Workflow_")
    ]
    return sorted(workflow_dirs, key=workflow_number)


def show_results():
    """Display the results of the selected workflow."""

    st.markdown("#### Results")

    current_wkdir = get_wkdir()
    if not current_wkdir or not current_wkdir.exists():
        st.warning("No Workflow working directory found.")
        return

    workflow_dirs = get_workflow_dirs(current_wkdir)
    if not workflow_dirs:
        st.warning("No workflows have been found in the working directory.")
        return

    workflow_names = [wkflow.name for wkflow in workflow_dirs]
    default_index = max(len(workflow_names) - 1, 0)
    chosen_workflow_name = st.selectbox(
        "Choose workflow", workflow_names, index=default_index, key="results_chosen_workflow"
    )
    chosen_workflow = Path(current_wkdir, chosen_workflow_name)

    results_dir = Path(chosen_workflow, "Results")
    if not results_dir.exists():
        st.warning("No results have been found for the selected workflow!")
        return
    results_name = sorted([dir.stem for dir in results_dir.iterdir() if dir.is_dir()])
    if not results_name:
        st.warning("No results have been found!")
        return

    results_tabs = st.tabs(results_name)

    for tab, tab_name in zip(results_tabs, results_name):
        with tab:
            display_results(Path(results_dir, tab_name))


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    # Define interface
    create_sidebar(HOW_TO_TEXT)

    st.title("Results")

    show_results()

    st_autorefresh(interval=2000, limit=10000, key="auto_refresh")

    # Update last_page
    st.session_state.last_page = PAGE_NAME
