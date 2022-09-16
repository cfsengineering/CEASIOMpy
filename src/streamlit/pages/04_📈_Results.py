from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from cpacspy.cpacspy import CPACS
from cpacspy.utils import PARAMS_COEFS
from genericpath import isfile
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Results", page_icon="📈")
st.title("Results")


def get_last_workflow():

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    last_workflow_nb = 0

    for dir in Path(st.session_state.workflow.working_dir).iterdir():
        if "Workflow_" in str(dir):
            last_workflow_nb = max(last_workflow_nb, int(str(dir).split("_")[-1]))

    return Path(
        Path(st.session_state.workflow.working_dir),
        f"Workflow_{str(last_workflow_nb).rjust(3, '0')}",
    )


def show_aeromap():

    st.markdown("#### Aeromap")

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    last_workflow = get_last_workflow()
    list_of_files = []
    for file in last_workflow.iterdir():
        if file.is_file():
            list_of_files.append(file.stem)
    if "ToolOutput" in list_of_files:
        cpacs = CPACS(Path(last_workflow, "ToolOutput.xml"))
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

    # Option choose axis
    col1, col2, col3 = st.columns(3)

    with col1:
        x_axis = st.selectbox("x", PARAMS_COEFS, 3)
    with col2:
        y_axis = st.selectbox("y", PARAMS_COEFS, 5)

    # Option filter 1
    with st.expander("Filter 1"):
        filt1_col1, filt1_col2 = st.columns([1, 2])

        with filt1_col1:
            filt1_remaining = [item for item in PARAMS_COEFS if item not in [x_axis, y_axis]]
            filter1 = st.selectbox("Filter by:", filt1_remaining)
        with filt1_col2:
            value_list = df_tmp[filter1].unique()
            value_selected = st.multiselect("Filter value:", value_list, value_list[0])

    # Option filter 2
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

    # Plot figure
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

    grid_color = "rgb(188,188,188)"
    axis_color = "rgb(0,0,0)"
    bg_color = "rgb(255,255,255)"

    fig.update_layout(
        xaxis=dict(title=x_axis),
        yaxis=dict(title=y_axis),
        plot_bgcolor=bg_color,
    )
    fig.update_xaxes(
        showline=True,
        linewidth=2,
        linecolor=axis_color,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
    )
    fig.update_yaxes(
        showline=True,
        linewidth=2,
        linecolor=axis_color,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
    )

    st.plotly_chart(fig)

    col1, col2, _ = st.columns([2, 2, 3])

    with col1:
        img_format = st.selectbox("Format", [".png", ".svg", ".pdf"])
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("Save this figure 📷"):
            fig_name = f"{y_axis}_vs_{x_axis}{img_format}"
            current_workflow = get_last_workflow()
            fig.write_image(Path(current_workflow, "Results", fig_name))

    # fig.write_html("test_file.html")


def show_results():

    st.markdown("#### Results")

    st.info("This part is under construction, it can not be use yet!")

    last_workflow = get_last_workflow()

    if not last_workflow:
        return

    for dir in Path(last_workflow, "Results").iterdir():
        if dir.is_dir():
            with st.expander(dir.name, expanded=False):
                st.text("")
                for file in dir.iterdir():
                    st.markdown(file)


show_aeromap()
show_results()

st_autorefresh(interval=3000, limit=100, key="auto_refresh")
