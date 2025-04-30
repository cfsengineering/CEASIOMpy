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
from streamlitutils import create_sidebar, get_last_workflow

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
        """Display results depending which type of file they are."""

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
                st.markdown(child.read_text())

            elif child.suffix == ".json":
                st.text_area(child.stem, child.read_text(), height=200)

            elif child.suffix == ".log" or child.suffix == ".txt":
                if "logs_container" not in st.session_state:
                    st.session_state["logs_container"] = st.container()
                    st.session_state.logs_container.markdown("**Logs**")
                st.session_state.logs_container.text_area(
                    child.stem, child.read_text(), height=200)

            elif child.name == "history.csv":
                st.markdown("**Convergence**")

                df = pd.read_csv(child)
                df.rename(columns=lambda x: x.strip().strip('"'), inplace=True)

                st.line_chart(df[["CD", "CL", "CMy"]])
                st.line_chart(df[["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoW]", "rms[RhoE]"]])

            elif child.suffix == ".csv":
                st.markdown(f"**{child.name}**")
                st.dataframe(pd.read_csv(child))

            elif "Case" in child.name and child.is_dir():
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


def show_aeromap():
    """Interactive graph to display aeromaps contained in the CPACS file."""

    st.markdown("#### Aeromap")

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    current_workflow = get_last_workflow()
    list_of_files = []

    for child in current_workflow.iterdir():
        if child.is_file():
            list_of_files.append(child.stem)

    if "ToolOutput" in list_of_files:
        cpacs = CPACS(Path(current_workflow, "ToolOutput.xml"))
        st.success("Your results are ready!")
    else:
        cpacs = st.session_state.cpacs
        st.info("No results found, these are aeromaps from the input CPACS file!")

    # Get aeromap(s) to plot from multiselect box
    aeromap_list = []
    aeromap_uid_list = cpacs.get_aeromap_uid_list()
    aeromap_selected = st.multiselect("Select aeromap", aeromap_uid_list)
    aeromap_list = [cpacs.get_aeromap_by_uid(aeromap_uid) for aeromap_uid in aeromap_selected]

    if not aeromap_list:
        st.warning("You must select at least one aeromap!")
        return

    # temp (TODO: could be improve, how to look into all df)
    df_tmp = aeromap_list[0].df

    col1, col2, _ = st.columns(3)

    with col1:
        x_axis = st.selectbox("x", PARAMS_COEFS, 3)
    with col2:
        y_axis = st.selectbox("y", PARAMS_COEFS, 5)

    with st.expander("Filter 1"):
        filter1_column1, filter1_column2 = st.columns([1, 2])

        with filter1_column1:
            filter1_remaining = [item for item in PARAMS_COEFS if item not in [x_axis, y_axis]]
            filter1 = st.selectbox("Filter by:", filter1_remaining)
        with filter1_column2:
            value_list = df_tmp[filter1].unique()
            value_selected = st.multiselect("Filter value:", value_list, value_list[0])

    with st.expander("Filter 2"):
        filter2_column1, filter2_column2 = st.columns([1, 2])
        with filter2_column1:
            filter2_remaining = [
                item for item in PARAMS_COEFS if item not in [x_axis, y_axis, filter1]
            ]
            filter2 = st.selectbox("Filter2 by:", filter2_remaining)
        with filter2_column2:
            value_list2 = df_tmp[filter2].unique()
            value_selected2 = st.multiselect("Filter2 value:", value_list2, value_list2[0])

    fig = go.Figure()
    for aeromap in aeromap_list:

        if not len(value_selected):
            value_selected = value_list

        for value in value_selected:
            if not len(value_selected2):
                value_selected2 = value_list2

            for value2 in value_selected2:
                df = aeromap.df[(aeromap.df[filter1] == value) & (aeromap.df[filter2] == value2)]
                legend = f"{aeromap.uid}<br>{filter1}={value}<br>{filter2}={value2}"
                fig.add_trace(go.Scatter(x=df[x_axis], y=df[y_axis], name=legend))

    fig.update_traces(mode="markers+lines", hovertemplate="x: %{x:.2f} \ny: %{y:.2f} ")

    fig.update_layout(
        xaxis=dict(title=x_axis), yaxis=dict(title=y_axis), plot_bgcolor="rgb(255,255,255)"
    )

    axis_options = {
        "showline": True,
        "linewidth": 2,
        "linecolor": "rgb(0,0,0)",
        "gridcolor": "rgb(188,188,188)",
        "zerolinecolor": "rgb(188,188,188)",
    }

    fig.update_xaxes(axis_options)
    fig.update_yaxes(axis_options)

    st.plotly_chart(fig)

    col1, col2, _ = st.columns([2, 2, 3])

    with col1:
        img_format = st.selectbox("Format", [".png", ".svg", ".pdf"])
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("Save this figure 📷"):
            fig_name = f"{cpacs.ac_name}_{y_axis}_vs_{x_axis}{img_format}"
            current_workflow = get_last_workflow()
            aerocoef_dir = Path(current_workflow, "Results", "ExportCSV")
            if not aerocoef_dir.exists():
                aerocoef_dir.mkdir(parents=True)
            fig.write_image(Path(aerocoef_dir, fig_name))


def show_results():
    """Display all the results of the current workflow."""

    st.markdown("#### Results")

    current_workflow = get_last_workflow()
    if not current_workflow:
        return

    results_dir = Path(current_workflow, "Results")
    results_name = sorted([dir.stem for dir in results_dir.iterdir() if dir.is_dir()])
    if not results_name:
        st.warning("No results have been found!")
        return

    st.info(f"All these results can be found in:\n\n{str(current_workflow.resolve())}")

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

    show_aeromap()
    show_results()

    if st.button("🔄 Refresh"):
        st.rerun()

    if st.checkbox("Auto refresh"):
        st_autorefresh(interval=2000, limit=10000, key="auto_refresh")

    # Update last_page
    st.session_state.last_page = PAGE_NAME
