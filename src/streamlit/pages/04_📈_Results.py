import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ceasiompy.utils.ceasiompyutils import aircraft_name
from ceasiompy.utils.commonpaths import DEFAULT_PARAVIEW_STATE
from cpacspy.cpacspy import CPACS
from cpacspy.utils import PARAMS_COEFS
from createsidbar import create_sidebar
from streamlit_autorefresh import st_autorefresh

how_to_text = (
    "### How to check your results\n"
    "1. Select the aeromap(s) you want to show\n"
    "1. Chose the parameter you want to plot\n"
    "1. Save some figure if you want\n"
    "1. Check results from each module\n"
)

create_sidebar(how_to_text)


def get_last_workflow():
    # TODO: make the function more general to CEASIOMpy and test it

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    last_workflow_nb = 0

    for dir in Path(st.session_state.workflow.working_dir).iterdir():
        if "Workflow_" in str(dir):
            last_workflow_nb = max(last_workflow_nb, int(str(dir).split("_")[-1]))

    if last_workflow_nb == 0:
        return None

    return Path(
        Path(st.session_state.workflow.working_dir),
        f"Workflow_{last_workflow_nb:03}",
    )


def display_results(results_dir):
    for file in sorted(Path(results_dir).iterdir()):

        if file.suffix == ".su2":
            if st.button("Show mesh", key=f"{file.stem}_su2_mesh"):
                os.system(f"dwfscope {str(file)}")

        if file.suffix == ".png":
            st.markdown(f"#### {file.stem.replace('_',' ')}")
            st.image(str(file))

        elif file.name == "history.csv":
            df = pd.read_csv(file)
            df = df.drop(["Time_Iter", "Outer_Iter", "Inner_Iter"], axis=1)
            st.line_chart(data=df, x=None, y=None, width=0, height=0, use_container_width=True)

        elif file.suffix == ".csv":
            df = pd.read_csv(file)
            st.markdown(f"**{file.name}**")
            st.dataframe(df)

        elif file.suffix == ".md":
            st.markdown(file.read_text())

        elif file.suffix == ".log" or file.suffix == ".txt":
            st.text_area(file.stem, file.read_text(), height=200)

        elif "Case" in file.name:
            with st.expander(file.stem, expanded=False):

                if st.button("Surface_flow", key=f"{file.stem}_surf_flow"):
                    open_paraview(file, "surface_flow.vtu")

                if st.button("Flow", key=f"{file.stem}_flow"):
                    open_paraview(file, "flow.vtu")

                display_results(file)


def open_paraview(case_dir, file_to_plot):

    paraview_state_txt = DEFAULT_PARAVIEW_STATE.read_text()

    file_path = Path(case_dir, file_to_plot)
    paraview_state = Path(case_dir, "paraview_state.pvsm")

    paraview_state.write_text(paraview_state_txt.replace("result_case_path", str(file_path)))

    os.system(f"paraview {str(paraview_state)}")


def show_aeromap():

    st.markdown("#### Aeromap")

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    current_workflow = get_last_workflow()
    list_of_files = []
    for file in current_workflow.iterdir():
        if file.is_file():
            list_of_files.append(file.stem)
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
        filt1_col1, filt1_col2 = st.columns([1, 2])

        with filt1_col1:
            filt1_remaining = [item for item in PARAMS_COEFS if item not in [x_axis, y_axis]]
            filter1 = st.selectbox("Filter by:", filt1_remaining)
        with filt1_col2:
            value_list = df_tmp[filter1].unique()
            value_selected = st.multiselect("Filter value:", value_list, value_list[0])

    with st.expander("Filter 2"):
        filt2_col1, filt2_col2 = st.columns([1, 2])
        with filt2_col1:
            filt2_remaining = [
                item for item in PARAMS_COEFS if item not in [x_axis, y_axis, filter1]
            ]
            filter2 = st.selectbox("Filter2 by:", filt2_remaining)
        with filt2_col2:
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

    fig.update_traces(
        mode="markers+lines",
        hovertemplate="x: %{x:.2f} \ny: %{y:.2f} ",
    )

    fig.update_layout(
        xaxis=dict(title=x_axis),
        yaxis=dict(title=y_axis),
        plot_bgcolor="rgb(255,255,255)",
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

    ac_name = aircraft_name(cpacs.tixi)

    st.plotly_chart(fig)

    col1, col2, _ = st.columns([2, 2, 3])

    with col1:
        img_format = st.selectbox("Format", [".png", ".svg", ".pdf"])
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("Save this figure 📷"):
            fig_name = f"{ac_name}_{y_axis}_vs_{x_axis}{img_format}"
            current_workflow = get_last_workflow()
            aerocoef_dir = Path(current_workflow, "Results", "AeroCoefficients")
            if not aerocoef_dir.exists():
                aerocoef_dir.mkdir(parents=True)
            fig.write_image(Path(aerocoef_dir, fig_name))


def show_results():

    st.markdown("#### Results")

    current_workflow = get_last_workflow()
    if not current_workflow:
        return

    results_dir = Path(current_workflow, "Results")

    st.info(f"All these results can be found in:\n\n{str(current_workflow.resolve())}")

    results_name = sorted([dir.stem for dir in results_dir.iterdir() if dir.is_dir()])
    results_tabs = st.tabs(results_name)

    for tab, tab_name in zip(results_tabs, results_name):

        with tab:
            st.markdown(f"{tab_name} res")

            display_results(Path(results_dir, tab_name))


st.title("Results")

show_aeromap()
show_results()

# st_autorefresh(interval=5000, limit=10000, key="auto_refresh")
