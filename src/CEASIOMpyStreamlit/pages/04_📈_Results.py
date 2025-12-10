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
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import joblib

from streamlit_autorefresh import st_autorefresh
from streamlitutils import (
    create_sidebar,
    get_last_workflow,
    highlight_stability,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (
    get_value,
    get_value_or_default,
    create_branch,
)

from cpacspy.utils import PARAMS_COEFS
from ceasiompy.utils.commonpaths import DEFAULT_PARAVIEW_STATE 
from ceasiompy.utils.ceasiompyutils import get_conditions_from_aeromap

from scipy.optimize import minimize
import io
import tempfile

from CEASIOMpy import section_select_cpacs, section_3D_view, clean_toolspecific
from ceasiompy.SMTrain.func.config import (
    get_xpath_for_param,
)

from SALib.sample import saltelli
from SALib.analyze import sobol
import altair as alt


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
            print(f'{child=}')
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
        
            elif child.name == "ranges_for_gui.csv":

                csv_rmse_path = Path(f"{results_dir}/rmse_model.csv")
                rmse_df = None
                if csv_rmse_path.exists():
                    rmse_df = pd.read_csv(csv_rmse_path)
                    rmse_value = rmse_df["rmse"].iloc[0]
                    st.markdown(f"##### Root Mean Square Error of the trained model: {rmse_value:.6f}")

                df_range = pd.read_csv(child)
                sliders_values = {}
                sliders_bounds = {}

                csv_path_sampling = Path(f"{results_dir}/avl_simulations_results.csv")
                df_samples = None
                if csv_path_sampling.exists():
                    df_samples = pd.read_csv(csv_path_sampling)
                

                for _, row in df_range.iterrows():
                    param = row["Parameter"]
                    min_val = float(row["Min"])
                    max_val = float(row["Max"])
                    sliders_bounds[param] = [min_val, max_val]
                    sliders_values[param] = min_val
                
                cpacs_in = Path(st.session_state.cpacs.cpacs_file)
                tmp_cpacs = CPACS(cpacs_in)
                tixi = tmp_cpacs.tixi

                model_path = results_dir / "surrogateModel.pkl"
                model, param_order = None, None

                if model_path.exists():
                    with open(model_path, "rb") as file:
                        data = joblib.load(file)
                    model = data["model"]
                    param_order = data["param_order"]

                else:
                    st.warning("⚠️ Surrogate model not found. Only geometry sliders will be available.")
                
                if model is not None and param_order:
                    # with st.expander("Sobol Global Sensitivity Analysis"):
                    st.subheader("Sobol Global Sensitivity Analysis")
                    
                    # ---- DEFINE PROBLEM ----
                    problem = {
                        "num_vars": len(param_order),
                        "names": param_order,
                        "bounds": [sliders_bounds[p] for p in param_order]
                    }

                    # ---- GENERATE SAMPLES ----
                    N = 256
                    sample_set = saltelli.sample(problem, N)

                    # ---- RUN MODEL ----
                    Y = []
                    for s in sample_set:
                        pred = model.predict_values(np.array(s).reshape(1,-1))[0]
                        Y.append(pred)

                    Y = np.array(Y).flatten()

                    # ---- SOBOL ANALYSIS ----
                    Si = sobol.analyze(problem, Y)

                    # ---- CONVERT TO DATAFRAME ----
                    sens_df = pd.DataFrame({
                        "Parameter": param_order,
                        "Single effect index Si": Si["S1"],
                        "Total-effect index ST": Si["ST"]
                    })

                    sens_df[["Single effect index Si", "Total-effect index ST"]] = sens_df[["Single effect index Si", "Total-effect index ST"]].clip(lower=0)

                    sens_df = sens_df.sort_values(by="Total-effect index ST", ascending=False)

                    # ---- SHOW RESULTS ----
                    sens_df_melted = sens_df.melt(
                        id_vars="Parameter",
                        value_vars=["Single effect index Si", "Total-effect index ST"],
                        var_name="Type",
                        value_name="Sensitivity"
                    )

                    chart = alt.Chart(sens_df_melted).mark_bar().encode(
                        x=alt.X("Parameter:N", sort=None, title="Parameter"),
                        y=alt.Y("Sensitivity:Q", title="Sobol Index"),
                        color=alt.Color("Type:N", scale=alt.Scale(scheme="category10")),
                        xOffset="Type:N",  
                        tooltip=["Parameter", "Type", "Sensitivity"]
                    ).properties(width=600, height=400)

                    st.altair_chart(chart)

                if model is not None and len(param_order) >= 2:
                    st.subheader("Response Surface Visualization")

                    # Let user select 2 params to visualize
                    selected_params = st.multiselect(
                        "Select exactly 2 parameters to visualize:",
                        options=param_order,
                        default=param_order[:2],
                        key="rsm_param_select"
                    )

                    if len(selected_params) == 2:
                        p1_min, p1_max = sliders_bounds.get(selected_params[0], (-5, 15))
                        p2_min, p2_max = sliders_bounds.get(selected_params[1], (-5, 15))

                        p1_range = st.slider(f"Range for {selected_params[0]}", float(p1_min), float(p1_max), (float(p1_min), float(p1_max)), key="rsm_slider_1")
                        p2_range = st.slider(f"Range for {selected_params[1]}", float(p2_min), float(p2_max), (float(p2_min), float(p2_max)), key="rsm_slider_2")

                        st.markdown("**Fix values for other parameters:**")
                        fixed_param_values = {}
                        for p in param_order:
                            if p not in selected_params:
                                min_val, max_val = sliders_bounds.get(p, (0, 0))
                                fixed_param_values[p] = st.slider(
                                    f"{p}",
                                    float(min_val),
                                    float(max_val),
                                    float((min_val + max_val) / 2),
                                    key=f"fixed_slider_{p}"
                                )

                        if st.button("Generate response surface"):
                            with st.spinner("Calculating response surface..."):
                                param1 = np.linspace(p1_range[0], p1_range[1], 50)
                                param2 = np.linspace(p2_range[0], p2_range[1], 50)
                                P1, P2 = np.meshgrid(param1, param2)

                                inputs = np.zeros((P1.size, len(param_order)))
                                for i, p in enumerate(param_order):
                                    if p == selected_params[0]:
                                        inputs[:, i] = P1.ravel()
                                    elif p == selected_params[1]:
                                        inputs[:, i] = P2.ravel()
                                    else:
                                        low, high = sliders_bounds.get(p, (0, 0))
                                        inputs[:, i] = (low + high) / 2

                                try:
                                    Z = model.predict_values(inputs).reshape(P1.shape)
                                    fig = go.Figure(data=[go.Surface(z=Z, x=P1, y=P2)])

                                    if df_samples is not None:
                                        
                                        mask = np.ones(len(df_samples), dtype=bool)
                                        tol = 0.1 * (max_val - min_val)
                                        for p, val in fixed_param_values.items():
                                            if p in df_samples.columns:
                                                mask &= np.isclose(df_samples[p], val, atol=tol)
                                        
                                        filtered_samples = df_samples[mask].copy()
                                        
                                        if len(filtered_samples) > 0 and selected_params[0] in filtered_samples.columns and selected_params[1] in filtered_samples.columns:
                                            x_samples = filtered_samples[selected_params[0]].values
                                            y_samples = filtered_samples[selected_params[1]].values
                                            
                                            output_col = filtered_samples.columns[-1]
                                            if output_col in filtered_samples.columns:
                                                z_samples = filtered_samples[output_col].values
                                            else:
                                                z_samples = np.zeros_like(x_samples)
                                            
                                            num_samples = len(x_samples)

                                            fig.add_trace(go.Scatter3d(
                                                x=x_samples,
                                                y=y_samples,
                                                z=z_samples,
                                                mode='markers',
                                                marker=dict(
                                                    size=1,
                                                    color='green',
                                                    line=dict(width=0.5, color='rgba(100, 0, 0, 0.7)'),
                                                    symbol='circle'
                                                ),
                                                name=f"Sampling points (n={num_samples})",
                                                showlegend=True
                                            ))

                                    fig.update_layout(
                                        title='Surrogate Model Response Surface with Sample Points',
                                        scene=dict(
                                            xaxis_title=selected_params[0],
                                            yaxis_title=selected_params[1],
                                            zaxis_title='Predicted Output'
                                        ),
                                        legend=dict(
                                            bgcolor='rgba(255,255,255,0.9)',
                                            bordercolor='green',
                                            borderwidth=1.5,
                                            font=dict(size=12),
                                            yanchor="top",
                                            y=0.99,
                                            xanchor="right",
                                            x=0.99
                                        )
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error predicting response surface: {e}")

                mode = st.radio(
                    "Select mode:",
                    ["Manual exploration", "Target-based exploration"],
                    index=0,
                    horizontal=True,
                )

                if mode == "Manual exploration":
                    col_tuning, col_3d = st.columns(2)
                    with col_tuning:
                        st.subheader('Parameters')
                        for param, (min_val, max_val) in sliders_bounds.items():
                            sliders_values[param] = st.slider(
                                f'{param}',
                                min_val,
                                max_val,
                                min_val,
                                0.01,
                                key=f"slider_{param}"
                            )

                    # update CPACS
                    params_to_update = {}
                    for name, val in sliders_values.items():
                        parts = name.split("_of_")
                        if len(parts) < 3:
                            continue
                        name_parameter, uID_section, uID_wing = parts
                        xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
                        params_to_update[xpath] = {"value": val, "xpath": xpath}

                    for xp, info in params_to_update.items():
                        create_branch(tixi, xp)
                        val = info['value']
                        tixi.updateDoubleElement(xp, float(val), "%g")

                    new_file_name = cpacs_in.stem + "_geometry_from_gui.xml"
                    new_file_path = cpacs_in.with_name(new_file_name)
                    tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

                    with col_3d:
                        st.subheader('| 3D View')
                        section_3D_view(
                            working_dir=Path(results_dir),
                            cpacs=CPACS(new_file_path),
                            aircraft_name="geometry_from_gui",
                        )

                    # if the model exist, show the prediction
                    if model is not None:
                        input_vector = np.array([sliders_values[p] for p in param_order])
                        predicted_value = model.predict_values(input_vector.reshape(1, -1))[0]
                        st.metric("Predicted objective value", f"{predicted_value}")

                    df_config = pd.DataFrame(list(sliders_values.items()), columns=['Parameter', 'Value'])
                    csv_buffer = io.StringIO()
                    df_config.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()
                    file_name_csv = f"configuration_for_obj_{predicted_value}.csv"

                    st.download_button(
                    label="Download configuration in CSV file",
                    data=csv_data,
                    file_name=file_name_csv,
                    mime="text/csv",
                    )

                elif mode == "Target-based exploration":
                    if model is None:
                        st.error("Please train or load a surrogate model first.")
                        st.stop()

                    st.subheader("Target-based exploration")
                    
                    param_order_geom = [p for p in param_order if p in sliders_bounds]
                    # param_order_aero = [p for p in param_order if p in aeromap_data]

                    x0 = np.array([sliders_values[p] for p in param_order_geom])
                    bounds = [sliders_bounds[p] for p in param_order_geom]

                    input_vector = np.array([sliders_values[p] for p in param_order])
                    predicted_value = model.predict_values(input_vector.reshape(1, -1))[0]

                    y_target = st.number_input(
                        "Enter target value", 
                        value=float(predicted_value), 
                        step=0.0001, 
                        format="%0.4f"
                        )

                    def objective_inverse(x):
                        input_dict = {}
                        for i, p in enumerate(param_order_geom):
                            input_dict[p] = x[i]
                        input_vector_full = np.array([input_dict[p] for p in param_order])
                        y_pred = model.predict_values(input_vector_full.reshape(1, -1))[0]
                        return abs(y_pred - y_target)
                    
                    selected_solver = st.selectbox(
                        label="Choose an optimization solver",
                        options=["L-BFGS-B","Powell","COBYLA","TNC","Nelder-Mead"],
                        help="Select the optimization algorithm to be used for minimizing the objective function. " \
                             "Each solver follows a different numerical strategy and may perform better depending on " \
                             "the problem type and constraints."
                    )

                    if st.button("Find parameters for given target value"):
                        result = minimize(objective_inverse, x0, bounds=bounds, method=selected_solver)

                        if result.success:
                            # st.success("✅ completed successfully")

                            input_dict_opt = {}
                            for i, p in enumerate(param_order_geom):
                                input_dict_opt[p] = result.x[i]

                            y_pred_opt = model.predict_values(
                                np.array([input_dict_opt[p] for p in param_order]).reshape(1, -1)
                            )[0]
                            
                            st.session_state["optim_result"] = {
                                "params": input_dict_opt,
                                "y_pred_opt": y_pred_opt,
                                "y_target": y_target,
                            }

                    if "optim_result" in st.session_state:
                        col_tab, col_view = st.columns([0.6,0.4])
                        with col_tab:
                            st.subheader("Parameter values")
                            df_opt_params = pd.DataFrame(
                                {
                                    "Parameter": param_order_geom,
                                    "Value": [st.session_state["optim_result"]["params"][p] for p in param_order_geom]
                                }
                            )
                            st.table(df_opt_params)

                            st.metric(
                                label="Predicted value for optimal parameters",
                                value=f"{st.session_state['optim_result']['y_pred_opt']}"
                            )
                            st.markdown(f"**Absolute error:** {abs(st.session_state['optim_result']['y_pred_opt'] - st.session_state['optim_result']['y_target'])}")
                            
                            csv_buffer = io.StringIO()
                            df_opt_params.to_csv(csv_buffer, index=False)
                            csv_data = csv_buffer.getvalue()
                            file_name_csv = f"optimal_parameters_target_value_{st.session_state['optim_result']['y_target']:.4f}.csv"
                            
                            st.download_button(
                            label="Download parameters in CSV file",
                            data=csv_data,
                            file_name=file_name_csv,
                            mime="text/csv",
                            )

                        tmp_cpacs = CPACS(Path(st.session_state.cpacs.cpacs_file))
                        tixi = tmp_cpacs.tixi

                        for name, val in st.session_state["optim_result"]["params"].items():
                            if "_of_" not in name:
                                continue
                            parts = name.split("_of_")
                            name_parameter, uID_section, uID_wing = parts
                            xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
                            create_branch(tixi, xpath)
                            tixi.updateDoubleElement(xpath, float(val), "%g")
                        
                        new_file_path = Path(results_dir) / "temp_optim_geometry.xml"
                        tmp_cpacs.save_cpacs(new_file_path, overwrite=True)


                        with col_view:
                            st.subheader("| 3D View")
                            
                            section_3D_view(
                                working_dir=Path(results_dir),
                                cpacs=CPACS(new_file_path),
                                aircraft_name="temp_optim_geometry"
                            )

                            with open(new_file_path, "rb") as f:
                                cpacs_data = f.read()

                            st.download_button(
                                label="Download CPACS file",
                                data=cpacs_data,
                                file_name=f"temp_optim_geometry_{y_target}.xml",
                                mime="application/xml"
                            )

            elif child.suffix == ".csv":
                with st.expander("CSV File"):
                    st.markdown(f"**{child.name}**")
                    st.dataframe(pd.read_csv(child))
                

            elif child.name == "best_geometric_configuration.xml":
                with st.expander("Best geometric configuration from AVL simulations"):
                    st.markdown(f"**Best geometric configuration from AVL simulations**")
                    section_3D_view(
                        working_dir=Path(results_dir),
                        cpacs=CPACS(Path(results_dir) / "best_geometric_configuration.xml"),
                        aircraft_name="best_geometric_configuration",
                    )

            # elif "Case" in child.name and child.is_dir():
            elif child.is_dir():
                if child == "Computations":
                    continue
                # with st.expander(child.stem, expanded=False):
                #     display_results(child)

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

    past_result = st.checkbox("Review past results of SMTrain")
    if past_result:
        with st.expander("Upload files"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("##### CPACS file")

                # File uploader widget
                uploaded_cpacs = st.file_uploader(
                    "Select a CPACS file",
                    type=["xml"],
                )

                if uploaded_cpacs:
                    temp_dir = tempfile.mkdtemp()
                    cpacs_path = os.path.join(temp_dir, uploaded_cpacs.name)
                    with open(cpacs_path, "wb") as f:
                        f.write(uploaded_cpacs.getvalue())
                        st.session_state.cpacs_file_path = cpacs_path
                    st.success("CPACS file loaded successfully")
                    st.write(f"The file has been temporarily saved here: {cpacs_path}")

                else:
                    st.error("Please upload a CPACS file or manually enter the file path.")


            with col2:
                st.markdown("##### MODEL file")
                uploaded_model = st.file_uploader("Upload trained surrogate model", type=["pkl"], key='model_uploader')
                if uploaded_model:
                    temp_dir = tempfile.mkdtemp()
                    model_path = os.path.join(temp_dir, uploaded_model.name)
                    with open(model_path, "wb") as f:
                        f.write(uploaded_model.getbuffer())
                    st.session_state.model_file_path = model_path
                    model_data = joblib.load(model_path)
                    st.session_state["model"] = model_data.get("model")
                    st.session_state["param_order"] = model_data.get("param_order")
                    st.success("Model loaded successfully")
                    st.write(f"The model file has been temporarily saved here: {model_path}")
                else:
                    st.error("Please upload a MODEL file or manually enter the file path.")
                

            
            with col3:
                st.markdown("##### Ranges parameter")
                uploaded_ranges = st.file_uploader("Upload ranges_for_gui CSV", type=["csv"], key='ranges')
                if uploaded_ranges:
                    temp_dir = tempfile.mkdtemp()
                    ranges_path = os.path.join(temp_dir, uploaded_ranges.name)
                    with open(ranges_path, "wb") as f:
                        f.write(uploaded_ranges.getbuffer())
                    st.session_state.ranges_file_path = ranges_path

                    df = pd.read_csv(uploaded_ranges)
                    sliders_bounds = {row["Parameter"]: (row["Min"], row["Max"]) for _, row in df.iterrows()}
                    sliders_values = {param: bounds[0] for param, bounds in sliders_bounds.items()}
                    st.session_state["sliders_bounds"] = sliders_bounds
                    st.session_state["sliders_values"] = sliders_values
                    st.success("Ranges loaded successfully")
                    st.write(f"The ranges file has been temporarily saved here: {ranges_path}")

                else:
                    st.error("Please upload a RANGES CSV file or manually enter the file path.")


            with col4:
                st.markdown("##### AVL Dataset")
                uploaded_avl_dataset = st.file_uploader("Upload avl_simulations_results.csv", type=["csv"], key='dataset_avl')
                if uploaded_avl_dataset:
                    temp_dir = tempfile.mkdtemp()
                    avl_dataset_path = os.path.join(temp_dir, uploaded_avl_dataset.name)
                    with open(ranges_path, "wb") as f:
                        f.write(uploaded_avl_dataset.getbuffer())
                    st.session_state.avl_dataset_path = avl_dataset_path
                    st.success("AVL dataset loaded successfully")
                    st.write(f"The dataset file has been temporarily saved here: {avl_dataset_path}")

                else:
                    st.error("Please upload AVL results dataset")



        if "model" not in st.session_state or "sliders_bounds" not in st.session_state:
            st.warning("Please upload model first.")
            st.stop()


        model = st.session_state["model"]
        param_order = st.session_state["param_order"]
        sliders_bounds = st.session_state["sliders_bounds"]
        sliders_values = st.session_state["sliders_values"]
        results_dir = Path(st.session_state.get("results_dir", "."))

        cpacs_in = Path(st.session_state.cpacs_file_path)
        tmp_cpacs = CPACS(cpacs_in)
        tixi = tmp_cpacs.tixi


        if model is not None and len(param_order) >= 2:
                    st.subheader("Response Surface Visualization")

                    # Let user select 2 params to visualize
                    selected_params = st.multiselect(
                        "Select exactly 2 parameters to visualize:",
                        options=param_order,
                        default=param_order[:2],
                        key="rsm_param_select"
                    )

                    if len(selected_params) == 2:
                        p1_min, p1_max = sliders_bounds.get(selected_params[0], (-5, 15))
                        p2_min, p2_max = sliders_bounds.get(selected_params[1], (-5, 15))

                        p1_range = st.slider(f"Range for {selected_params[0]}", float(p1_min), float(p1_max), (float(p1_min), float(p1_max)), key="rsm_slider_1")
                        p2_range = st.slider(f"Range for {selected_params[1]}", float(p2_min), float(p2_max), (float(p2_min), float(p2_max)), key="rsm_slider_2")

                        st.markdown("**Fix values for other parameters:**")
                        fixed_param_values = {}
                        for p in param_order:
                            if p not in selected_params:
                                min_val, max_val = sliders_bounds.get(p, (0, 0))
                                fixed_param_values[p] = st.slider(
                                    f"{p}",
                                    float(min_val),
                                    float(max_val),
                                    float((min_val + max_val) / 2),
                                    key=f"fixed_slider_{p}"
                                )

                        csv_path_sampling = Path(f"{results_dir}/avl_simulations_results.csv")
                        df_samples = None
                        if csv_path_sampling.exists():
                            df_samples = pd.read_csv(csv_path_sampling)

                        if st.button("Generate response surface"):
                            with st.spinner("Calculating response surface..."):
                                param1 = np.linspace(p1_range[0], p1_range[1], 50)
                                param2 = np.linspace(p2_range[0], p2_range[1], 50)
                                P1, P2 = np.meshgrid(param1, param2)

                                inputs = np.zeros((P1.size, len(param_order)))
                                for i, p in enumerate(param_order):
                                    if p == selected_params[0]:
                                        inputs[:, i] = P1.ravel()
                                    elif p == selected_params[1]:
                                        inputs[:, i] = P2.ravel()
                                    else:
                                        low, high = sliders_bounds.get(p, (0, 0))
                                        inputs[:, i] = (low + high) / 2

                                try:
                                    Z = model.predict_values(inputs).reshape(P1.shape)
                                    fig = go.Figure(data=[go.Surface(z=Z, x=P1, y=P2)])

                                    if df_samples is not None:
                                        
                                        mask = np.ones(len(df_samples), dtype=bool)
                                        tol = 0.1 * (max_val - min_val)
                                        for p, val in fixed_param_values.items():
                                            if p in df_samples.columns:
                                                mask &= np.isclose(df_samples[p], val, atol=tol)
                                        
                                        filtered_samples = df_samples[mask].copy()
                                        
                                        if len(filtered_samples) > 0 and selected_params[0] in filtered_samples.columns and selected_params[1] in filtered_samples.columns:
                                            x_samples = filtered_samples[selected_params[0]].values
                                            y_samples = filtered_samples[selected_params[1]].values
                                            
                                            output_col = filtered_samples.columns[-1]
                                            if output_col in filtered_samples.columns:
                                                z_samples = filtered_samples[output_col].values
                                            else:
                                                z_samples = np.zeros_like(x_samples)
                                            
                                            num_samples = len(x_samples)

                                            fig.add_trace(go.Scatter3d(
                                                x=x_samples,
                                                y=y_samples,
                                                z=z_samples,
                                                mode='markers',
                                                marker=dict(
                                                    size=1,
                                                    color='green',
                                                    line=dict(width=0.5, color='rgba(100, 0, 0, 0.7)'),
                                                    symbol='circle'
                                                ),
                                                name=f"Sampling points (n={num_samples})",
                                                showlegend=True
                                            ))

                                    fig.update_layout(
                                        title='Surrogate Model Response Surface with Sample Points',
                                        scene=dict(
                                            xaxis_title=selected_params[0],
                                            yaxis_title=selected_params[1],
                                            zaxis_title='Predicted Output'
                                        ),
                                        legend=dict(
                                            bgcolor='rgba(255,255,255,0.9)',
                                            bordercolor='green',
                                            borderwidth=1.5,
                                            font=dict(size=12),
                                            yanchor="top",
                                            y=0.99,
                                            xanchor="right",
                                            x=0.99
                                        )
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error predicting response surface: {e}")    


        mode = st.radio(
            "Select mode:",
            ["Manual exploration", "Target-based exploration"],
            index=0,
            horizontal=True,
        )

        if mode == "Manual exploration":
            
            col_sliders, col_3d = st.columns(2)
            with col_sliders:
                st.subheader("Parameter sliders")
                for param, (min_val, max_val) in sliders_bounds.items():
                    sliders_values[param] = st.slider(
                        label=f"➤ {param}",
                        min_value=min_val,
                        max_value=max_val,
                        value=sliders_values.get(param, min_val),
                        step=0.01,
                        format="%.2f",
                        help=f"Set the value for {param} between {min_val} and {max_val}.",
                        key=f"slider_{param}",
                        label_visibility="visible",
                    )
                input_vector = np.array([sliders_values[p] for p in param_order])
                predicted_value = model.predict_values(input_vector.reshape(1, -1))[0]
                st.metric("Predicted objective value", f"{predicted_value}")
            
            
            df_params = pd.DataFrame({
                "Parameter": list(sliders_values.keys()),
                "Value": list(sliders_values.values())
            })

            csv_buffer = io.StringIO()
            df_params.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            file_name_csv = f"parameters_for_predicted_value_{predicted_value}.csv"
            
            with col_sliders:
                st.download_button(
                            label="Download parameters in CSV file",
                            data=csv_data,
                            file_name=file_name_csv,
                            mime="text/csv",
                        )

            # update CPACS
            params_to_update = {}
            for name, val in sliders_values.items():
                parts = name.split("_of_")
                if len(parts) < 3:
                    continue
                name_parameter, uID_section, uID_wing = parts
                xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
                params_to_update[xpath] = {"value": val, "xpath": xpath}

            for xp, info in params_to_update.items():
                create_branch(tixi, xp)
                val = info['value']
                tixi.updateDoubleElement(xp, float(val), "%g")

            new_file_name = cpacs_in.stem + f"_objective_{predicted_value}.xml"
            new_file_path = cpacs_in.with_name(new_file_name)
            tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

            with col_3d:
                st.subheader("| 3D View")
                section_3D_view(
                    working_dir=Path(results_dir),
                    cpacs=CPACS(new_file_path),
                    aircraft_name="geometry_from_gui",
                )
                with open(new_file_path, "rb") as f:
                    cpacs_data = f.read()

                st.download_button(
                    label="Download CPACS file",
                    data=cpacs_data,
                    file_name=new_file_name,
                    mime="application/xml"
                )
        

        if mode == "Target-based exploration":
            if model is None:
                st.error("Please train or load a surrogate model first.")
                st.stop()

            st.subheader("Target-based exploration")

            selected_solver = st.selectbox(
                label="Choose an optimization solver",
                options=["L-BFGS-B","Powell","COBYLA","TNC","Nelder-Mead"],
                help="Nelder-Mead is robust for small datasets; L-BFGS-B is efficient with larger datasets."
            )


            param_order_geom = [p for p in param_order if p in sliders_bounds]
            
            x0 = np.array([sliders_values[p] for p in param_order_geom])
            predicted_value = model.predict_values(x0.reshape(1, -1))[0]
            bounds = [sliders_bounds[p] for p in param_order_geom]

            y_target = st.number_input(
                "Enter target value",
                value=float(predicted_value),
                step=0.0001,
                format="%0.4f"
            )

            def objective_inverse(x):
                input_dict = {}
                for i, p in enumerate(param_order_geom):
                    input_dict[p] = x[i]
                input_vector_full = np.array([input_dict[p] for p in param_order])
                y_pred = model.predict_values(input_vector_full.reshape(1, -1))[0]
                return abs(y_pred - y_target)

            if st.button("Find parameters for given target value"):
                
                result = minimize(
                    objective_inverse,
                    x0,
                    bounds=bounds,
                    method=selected_solver,
                )
                if result.success:
                    
                    input_dict_opt = {}
                    for i, p in enumerate(param_order_geom):
                        input_dict_opt[p] = result.x[i]

                    y_pred_opt = model.predict_values(
                        np.array([input_dict_opt[p] for p in param_order]).reshape(1, -1))[0]

                    st.session_state["optim_result"] = {
                        "params": input_dict_opt,
                        "y_pred_opt": y_pred_opt,
                        "y_target": y_target,
                    }

            if "optim_result" in st.session_state:
                col_tab, col_view = st.columns([0.6, 0.4])
                with col_tab:
                    st.subheader("Parameter values")
                    df_opt_params = pd.DataFrame({
                        "Parameter": param_order_geom,
                        "Value": [st.session_state["optim_result"]["params"][p] for p in param_order_geom]
                    })
                    st.table(df_opt_params)

                    st.metric(
                        label="Predicted value for optimal parameters",
                        value=f"{st.session_state['optim_result']['y_pred_opt']}"
                    )
                    st.markdown(
                        f"**Absolute error:** "
                        f"{abs(st.session_state['optim_result']['y_pred_opt'] - st.session_state['optim_result']['y_target'])}"
                    )

                    
                    csv_buffer = io.StringIO()
                    df_opt_params.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()
                    file_name_csv = f"optimal_parameters_target_value_{st.session_state['optim_result']['y_target']}.csv"

                    st.download_button(
                        label="Download parameters in CSV file",
                        data=csv_data,
                        file_name=file_name_csv,
                        mime="text/csv",
                    )

                tmp_cpacs = CPACS(Path(st.session_state.cpacs_file_path))
                tixi = tmp_cpacs.tixi

                for name, val in st.session_state["optim_result"]["params"].items():
                    if "_of_" not in name:
                        continue
                    parts = name.split("_of_")
                    name_parameter, uID_section, uID_wing = parts
                    xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
                    create_branch(tixi, xpath)
                    tixi.updateDoubleElement(xpath, float(val), "%g")

                # new_file_path = Path(results_dir) / "temp_optim_geometry.xml"
                # tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

                new_file_name = cpacs_in.stem + f"_optim_geometry_{y_target}.xml"
                new_file_path = cpacs_in.with_name(new_file_name)
                tmp_cpacs.save_cpacs(new_file_path, overwrite=True)


                with col_view:
                    st.subheader("| 3D View")
                    section_3D_view(
                        working_dir=Path(results_dir),
                        cpacs=CPACS(new_file_path),
                        aircraft_name="geometry_from_gui",
                    )
                    with open(new_file_path, "rb") as f:
                        cpacs_data = f.read()

                    st.download_button(
                        label="Download CPACS file",
                        data=cpacs_data,
                        file_name=new_file_name,
                        mime="application/xml"
                    )
    else: 
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
    
    
    # mode = st.radio(
    #     "**Decide whether to explore existing results or perform current simulation:**",
    #     ["Currently simulation", "Review past results"],
    #     index=0,
    #     horizontal=True,
    # )
    # if mode == "Currently simulation":
    #     current_workflow = get_last_workflow()
    #     if not current_workflow:
    #         return

    #     results_dir = Path(current_workflow, "Results")
    #     results_name = sorted([dir.stem for dir in results_dir.iterdir() if dir.is_dir()])
    #     if not results_name:
    #         st.warning("No results have been found!")
    #         return

    #     st.info(f"All these results can be found in:\n\n{str(current_workflow.resolve())}")

    #     results_tabs = st.tabs(results_name)

    #     for tab, tab_name in zip(results_tabs, results_name):
    #         with tab:
    #             display_results(Path(results_dir, tab_name))
    

    # if mode == "Review past results":
    #     with st.expander("Upload files"):
    #         col1, col2, col3 = st.columns(3)
    #         with col1:
    #             st.markdown("##### CPACS file")

    #             # File uploader widget
    #             uploaded_cpacs = st.file_uploader(
    #                 "Select a CPACS file",
    #                 type=["xml"],
    #             )

    #             if uploaded_cpacs:
    #                 temp_dir = tempfile.mkdtemp()
    #                 cpacs_path = os.path.join(temp_dir, uploaded_cpacs.name)
    #                 with open(cpacs_path, "wb") as f:
    #                     f.write(uploaded_cpacs.getvalue())
    #                     st.session_state.cpacs_file_path = cpacs_path
    #                 st.success("CPACS file loaded successfully")
    #                 st.write(f"The file has been temporarily saved here: {cpacs_path}")

    #             else:
    #                 st.error("Please upload a CPACS file or manually enter the file path.")


    #         with col2:
    #             st.markdown("##### MODEL file")
    #             uploaded_model = st.file_uploader("Upload trained surrogate model", type=["pkl"], key='model_uploader')
    #             if uploaded_model:
    #                 temp_dir = tempfile.mkdtemp()
    #                 model_path = os.path.join(temp_dir, uploaded_model.name)
    #                 with open(model_path, "wb") as f:
    #                     f.write(uploaded_model.getbuffer())
    #                 st.session_state.model_file_path = model_path
    #                 model_data = joblib.load(model_path)
    #                 st.session_state["model"] = model_data.get("model")
    #                 st.session_state["param_order"] = model_data.get("param_order")
    #                 st.success("Model loaded successfully")
    #                 st.write(f"The model file has been temporarily saved here: {model_path}")
    #             else:
    #                 st.error("Please upload a MODEL file or manually enter the file path.")
                

            
    #         with col3:
    #             st.markdown("##### Ranges parameter")
    #             uploaded_ranges = st.file_uploader("Upload ranges_for_gui CSV", type=["csv"], key='ranges')
    #             if uploaded_ranges:
    #                 temp_dir = tempfile.mkdtemp()
    #                 ranges_path = os.path.join(temp_dir, uploaded_ranges.name)
    #                 with open(ranges_path, "wb") as f:
    #                     f.write(uploaded_ranges.getbuffer())
    #                 st.session_state.ranges_file_path = ranges_path

    #                 df = pd.read_csv(uploaded_ranges)
    #                 sliders_bounds = {row["Parameter"]: (row["Min"], row["Max"]) for _, row in df.iterrows()}
    #                 sliders_values = {param: bounds[0] for param, bounds in sliders_bounds.items()}
    #                 st.session_state["sliders_bounds"] = sliders_bounds
    #                 st.session_state["sliders_values"] = sliders_values
    #                 st.success("Ranges loaded successfully")
    #                 st.write(f"The ranges file has been temporarily saved here: {ranges_path}")

    #             else:
    #                 st.error("Please upload a RANGES CSV file or manually enter the file path.")

    #     if "model" not in st.session_state or "sliders_bounds" not in st.session_state:
    #         st.warning("Please upload model first.")
    #         st.stop()


    #     model = st.session_state["model"]
    #     param_order = st.session_state["param_order"]
    #     sliders_bounds = st.session_state["sliders_bounds"]
    #     sliders_values = st.session_state["sliders_values"]
    #     results_dir = Path(st.session_state.get("results_dir", "."))

    #     cpacs_in = Path(st.session_state.cpacs_file_path)
    #     tmp_cpacs = CPACS(cpacs_in)
    #     tixi = tmp_cpacs.tixi

    #     mode = st.radio(
    #         "Select mode:",
    #         ["Manual exploration", "Target-based exploration"],
    #         index=0,
    #         horizontal=True,
    #     )

    #     if mode == "Manual exploration":
            
    #         col_sliders, col_3d = st.columns(2)
    #         with col_sliders:
    #             st.subheader("Parameter sliders")
    #             for param, (min_val, max_val) in sliders_bounds.items():
    #                 sliders_values[param] = st.slider(
    #                     label=f"➤ {param}",
    #                     min_value=min_val,
    #                     max_value=max_val,
    #                     value=sliders_values.get(param, min_val),
    #                     step=0.01,
    #                     format="%.2f",
    #                     help=f"Set the value for {param} between {min_val} and {max_val}.",
    #                     key=f"slider_{param}",
    #                     label_visibility="visible",
    #                 )
    #             input_vector = np.array([sliders_values[p] for p in param_order])
    #             predicted_value = model.predict_values(input_vector.reshape(1, -1))[0]
    #             st.metric("Predicted objective value", f"{predicted_value}")
            
            
    #         df_params = pd.DataFrame({
    #             "Parameter": list(sliders_values.keys()),
    #             "Value": list(sliders_values.values())
    #         })

    #         csv_buffer = io.StringIO()
    #         df_params.to_csv(csv_buffer, index=False)
    #         csv_data = csv_buffer.getvalue()
    #         file_name_csv = f"parameters_for_predicted_value_{predicted_value}.csv"
            
    #         with col_sliders:
    #             st.download_button(
    #                         label="Download parameters in CSV file",
    #                         data=csv_data,
    #                         file_name=file_name_csv,
    #                         mime="text/csv",
    #                     )

    #         # update CPACS
    #         params_to_update = {}
    #         for name, val in sliders_values.items():
    #             parts = name.split("_of_")
    #             if len(parts) < 3:
    #                 continue
    #             name_parameter, uID_section, uID_wing = parts
    #             xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
    #             params_to_update[xpath] = {"value": val, "xpath": xpath}

    #         for xp, info in params_to_update.items():
    #             create_branch(tixi, xp)
    #             val = info['value']
    #             tixi.updateDoubleElement(xp, float(val), "%g")

    #         new_file_name = cpacs_in.stem + f"_objective_{predicted_value}.xml"
    #         new_file_path = cpacs_in.with_name(new_file_name)
    #         tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

    #         with col_3d:
    #             st.subheader("| 3D View")
    #             section_3D_view(
    #                 working_dir=Path(results_dir),
    #                 cpacs=CPACS(new_file_path),
    #                 aircraft_name="geometry_from_gui",
    #             )
    #             with open(new_file_path, "rb") as f:
    #                 cpacs_data = f.read()

    #             st.download_button(
    #                 label="Download CPACS file",
    #                 data=cpacs_data,
    #                 file_name=new_file_name,
    #                 mime="application/xml"
    #             )


    
    # if mode == "Target-based exploration":
    #     if model is None:
    #         st.error("Please train or load a surrogate model first.")
    #         st.stop()

    #     st.subheader("Target-based exploration")

    #     selected_solver = st.selectbox(
    #         label="Choose an optimization solver",
    #         options=["L-BFGS-B","Powell","COBYLA","TNC","Nelder-Mead"],
    #         help="Nelder-Mead is robust for small datasets; L-BFGS-B is efficient with larger datasets."
    #     )


    #     param_order_geom = [p for p in param_order if p in sliders_bounds]
        
    #     x0 = np.array([sliders_values[p] for p in param_order_geom])
    #     predicted_value = model.predict_values(x0.reshape(1, -1))[0]
    #     bounds = [sliders_bounds[p] for p in param_order_geom]

    #     y_target = st.number_input(
    #         "Enter target value",
    #         value=float(predicted_value),
    #         step=0.0001,
    #         format="%0.4f"
    #     )

    #     def objective_inverse(x):
    #         input_dict = {}
    #         for i, p in enumerate(param_order_geom):
    #             input_dict[p] = x[i]
    #         input_vector_full = np.array([input_dict[p] for p in param_order])
    #         y_pred = model.predict_values(input_vector_full.reshape(1, -1))[0]
    #         return abs(y_pred - y_target)

    #     if st.button("Find parameters for given target value"):
            
    #         result = minimize(
    #             objective_inverse,
    #             x0,
    #             bounds=bounds,
    #             method=selected_solver,
    #         )
    #         if result.success:
                
    #             input_dict_opt = {}
    #             for i, p in enumerate(param_order_geom):
    #                 input_dict_opt[p] = result.x[i]

    #             y_pred_opt = model.predict_values(
    #                 np.array([input_dict_opt[p] for p in param_order]).reshape(1, -1))[0]

    #             st.session_state["optim_result"] = {
    #                 "params": input_dict_opt,
    #                 "y_pred_opt": y_pred_opt,
    #                 "y_target": y_target,
    #             }

    #     if "optim_result" in st.session_state:
    #         col_tab, col_view = st.columns([0.6, 0.4])
    #         with col_tab:
    #             st.subheader("Parameter values")
    #             df_opt_params = pd.DataFrame({
    #                 "Parameter": param_order_geom,
    #                 "Value": [st.session_state["optim_result"]["params"][p] for p in param_order_geom]
    #             })
    #             st.table(df_opt_params)

    #             st.metric(
    #                 label="Predicted value for optimal parameters",
    #                 value=f"{st.session_state['optim_result']['y_pred_opt']}"
    #             )
    #             st.markdown(
    #                 f"**Absolute error:** "
    #                 f"{abs(st.session_state['optim_result']['y_pred_opt'] - st.session_state['optim_result']['y_target'])}"
    #             )

                
    #             csv_buffer = io.StringIO()
    #             df_opt_params.to_csv(csv_buffer, index=False)
    #             csv_data = csv_buffer.getvalue()
    #             file_name_csv = f"optimal_parameters_target_value_{st.session_state['optim_result']['y_target']}.csv"

    #             st.download_button(
    #                 label="Download parameters in CSV file",
    #                 data=csv_data,
    #                 file_name=file_name_csv,
    #                 mime="text/csv",
    #             )

    #         tmp_cpacs = CPACS(Path(st.session_state.cpacs_file_path))
    #         tixi = tmp_cpacs.tixi

    #         for name, val in st.session_state["optim_result"]["params"].items():
    #             if "_of_" not in name:
    #                 continue
    #             parts = name.split("_of_")
    #             name_parameter, uID_section, uID_wing = parts
    #             xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
    #             create_branch(tixi, xpath)
    #             tixi.updateDoubleElement(xpath, float(val), "%g")

    #         # new_file_path = Path(results_dir) / "temp_optim_geometry.xml"
    #         # tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

    #         new_file_name = cpacs_in.stem + f"_optim_geometry_{y_target}.xml"
    #         new_file_path = cpacs_in.with_name(new_file_name)
    #         tmp_cpacs.save_cpacs(new_file_path, overwrite=True)


    #         with col_view:
    #             st.subheader("| 3D View")
    #             section_3D_view(
    #                 working_dir=Path(results_dir),
    #                 cpacs=CPACS(new_file_path),
    #                 aircraft_name="geometry_from_gui",
    #             )
    #             with open(new_file_path, "rb") as f:
    #                 cpacs_data = f.read()

    #             st.download_button(
    #                 label="Download CPACS file",
    #                 data=cpacs_data,
    #                 file_name=new_file_name,
    #                 mime="application/xml"
    #             )


    #         # with col_view:
    #         #     st.subheader("| 3D View")
    #         #     section_3D_view(
    #         #         working_dir=Path(results_dir),
    #         #         cpacs=CPACS(new_file_path),
    #         #         aircraft_name="geometry_optimised"
    #         #     )

    #         #     if st.button("Save CPACS file"):
    #         #         cpacs_in = Path(st.session_state.cpacs.cpacs_file)
    #         #         tmp_cpacs = CPACS(cpacs_in)
    #         #         tixi = tmp_cpacs.tixi

    #         #         for name, val in st.session_state["optim_result"]["params"].items():
    #         #             if "_of_" not in name:
    #         #                 continue
    #         #             parts = name.split("_of_")
    #         #             name_parameter, uID_section, uID_wing = parts
    #         #             xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)
    #         #             create_branch(tixi, xpath)
    #         #             tixi.updateDoubleElement(xpath, float(val), "%g")

    #         #         base_name = "cpacs_geometry_gui"
    #         #         existing_files = [f.name for f in Path(results_dir).glob(f"{base_name}_*.xml")]
    #         #         existing_indices = [int(f.stem.split('_')[-1]) for f in Path(results_dir).glob(f"{base_name}_*.xml") if f.stem.split('_')[-1].isdigit()]
    #         #         next_index = max(existing_indices) + 1 if existing_indices else 1
    #         #         new_file_name = f"{base_name}_{next_index}.xml"
    #         #         new_file_path = Path(results_dir) / new_file_name

    #         #         tmp_cpacs.save_cpacs(new_file_path, overwrite=True)
    #         #         st.success(f"CPACS file saved as {new_file_name}")





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
