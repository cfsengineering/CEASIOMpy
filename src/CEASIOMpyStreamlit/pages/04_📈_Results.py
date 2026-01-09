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
import base64
import re

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import joblib
import matplotlib.pyplot as plt

from ceasiompy.utils.commonpaths import get_wkdir
from CEASIOMpyStreamlit.parsefunctions import display_avl_table_file
from CEASIOMpyStreamlit.streamlitutils import (
    create_sidebar,
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

from ceasiompy.PyAVL import AVL_TABLE_FILES

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT = (
    "### How to check your results\n"
    "1. Check the results for your workflow\n"
)

PAGE_NAME = "Results"
IGNORED_RESULT_FILES: set[str] = {
    "avl_commands.txt",
    "logfile_avl.log",
}

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
        # Display results depending on the file type.

        container_list = [
            "logs_container",
            "figures_container",
            "paraview_container",
            "pdf_container",
        ]
        clear_containers(container_list)

        def results_sort_key(path: Path) -> tuple[int, str]:
            '''Priority to files, priority=0 is highest priority.'''
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                priority = 0
            elif suffix == ".txt":
                priority = 2
            else:
                priority = 1
            return priority, path.name

        for child in sorted(Path(results_dir).iterdir(), key=results_sort_key):
            if child.name in IGNORED_RESULT_FILES:
                continue

            if child.suffix == ".smx":
                if st.button(f"Open {child.name} with SUMO", key=f"{child}_sumo_geom"):
                    os.system(f"dwfsumo {str(child)}")

            elif child.suffix == ".dat":
                skip_first = False
                first_line = child.read_text().splitlines()[:1]
                if first_line:
                    parts = first_line[0].strip().split()
                    if len(parts) < 2:
                        skip_first = True
                    else:
                        try:
                            float(parts[0])
                            float(parts[1])
                        except ValueError:
                            skip_first = True
                df = pd.read_csv(
                    child,
                    sep=r"\s+",
                    comment="#",
                    header=None,
                    skiprows=1 if skip_first else 0,
                )
                if df.shape[1] == 2:
                    df = df.apply(pd.to_numeric, errors="coerce")
                    df = df.iloc[:, :2].dropna()
                    if not df.empty:
                        df.columns = ["x", "y"]
                        fig, ax = plt.subplots()
                        ax.plot(df["x"].to_numpy(), df["y"].to_numpy())
                        ax.set_aspect("equal", adjustable="box")
                        ax.set_title(child.stem)
                        ax.set_xlabel("x")
                        ax.set_ylabel("y")
                        st.pyplot(fig)
                        continue
                st.text_area(child.stem, child.read_text(), height=200)

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

            elif child.suffix == ".pdf":
                if "pdf_container" not in st.session_state:
                    st.session_state["pdf_container"] = st.container()
                    st.session_state.pdf_container.markdown("**PDFs**")

                pdf_bytes = child.read_bytes()
                b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
                st.session_state.pdf_container.markdown(f"**{child.name}**")
                st.session_state.pdf_container.download_button(
                    "Download PDF",
                    data=pdf_bytes,
                    file_name=child.name,
                    mime="application/pdf",
                    key=f"{child}_pdf_download",
                )
                st.session_state.pdf_container.markdown(
                    f'<iframe src="data:application/pdf;base64,{b64_pdf}" '
                    'width="100%" height="700" style="border:0"></iframe>',
                    unsafe_allow_html=True,
                )

            elif child.suffix == ".md":
                md_text = child.read_text()
                # Simple table highlighting for "Stable"/"Unstable"

                html = highlight_stability(md_text)
                st.markdown(html, unsafe_allow_html=True)

            elif child.suffix == ".json":
                st.text_area(child.stem, child.read_text(), height=200)

            elif child.suffix == ".log" or child.suffix == ".txt":
                if child.name in AVL_TABLE_FILES:
                    display_avl_table_file(child)
                    continue
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

                csv_rmse_krg_path = Path(f"{results_dir}/rmse_KRG.csv")
                rmse_krg_df = None
                if csv_rmse_krg_path.exists():
                    rmse_krg_df = pd.read_csv(csv_rmse_krg_path)
                    rmse_krg_value = rmse_krg_df["rmse"].iloc[0]
                    st.markdown(f"##### Root Mean Square Error of KRG model: {rmse_krg_value:.6f}")

                csv_rmse_rbf_path = Path(f"{results_dir}/rmse_RBF.csv")
                rmse_rbf_df = None
                if csv_rmse_rbf_path.exists():
                    rmse_rbf_df = pd.read_csv(csv_rmse_rbf_path)
                    rmse_rbf_value = rmse_rbf_df["rmse"].iloc[0]
                    st.markdown(f"##### Root Mean Square Error of RBF model: {rmse_rbf_value:.6f}")

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

                model_selected = st.radio(
                    "Select the model to visualize:",
                    ["KRG", "RBF"],
                    index=0,
                    horizontal=True,
                )

                if model_selected == "KRG":
                    model_path = results_dir / "surrogateModel_krg.pkl"
                else:
                    model_path = results_dir / "surrogateModel_rbf.pkl"

                model, param_order = None, None

                if model_path.exists():
                    with open(model_path, "rb") as file:
                        data = joblib.load(file)
                    model = data["model"]
                    param_order = data["param_order"]

                else:
                    st.warning(
                        "⚠️ Surrogate model not found. Only geometry "
                        "sliders will be available."
                    )

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

                    sens_df[["Single effect index Si", "Total-effect index ST"]] = sens_df[
                        ["Single effect index Si", "Total-effect index ST"]
                    ].clip(lower=0)

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

                        p1_range = st.slider(
                            f"Range for {selected_params[0]}",
                            float(p1_min),
                            float(p1_max),
                            (float(p1_min),
                             float(p1_max)),
                            key="rsm_slider_1"
                        )
                        p2_range = st.slider(
                            f"Range for {selected_params[1]}",
                            float(p2_min),
                            float(p2_max),
                            (float(p2_min),
                             float(p2_max)),
                            key="rsm_slider_2"
                        )

                        if len(param_order) >= 3:
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

                                    if len(param_order) >= 3:
                                        mask = np.ones(len(df_samples), dtype=bool)
                                        tol = 0.1 * (max_val - min_val)
                                        for p, val in fixed_param_values.items():
                                            if p in df_samples.columns:
                                                mask &= np.isclose(df_samples[p], val, atol=tol)

                                        filtered_samples = df_samples[mask].copy()

                                        if (
                                            len(filtered_samples) > 0
                                            and selected_params[0] in filtered_samples.columns
                                            and selected_params[1] in filtered_samples.columns
                                        ):
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
                                                    line=dict(
                                                        width=0.5,
                                                        color='rgba(100, 0, 0, 0.7)'
                                                    ),
                                                    symbol='circle'
                                                ),
                                                name=f"Sampling points (n={num_samples})",
                                                showlegend=True
                                            ))
                                    else:
                                        x_samples = df_samples[selected_params[0]].values
                                        y_samples = df_samples[selected_params[1]].values

                                        output_col = df_samples.columns[-1]
                                        if output_col in df_samples.columns:
                                            z_samples = df_samples[output_col].values
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
                                        title='Surrogate Model Response Surface with '
                                        'Sample Points',
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

                    df_config = pd.DataFrame(
                        list(sliders_values.items()),
                        columns=['Parameter', 'Value']
                    )
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
                        help="Select the optimization algorithm to be used for minimizing"
                        "the objective function. Each solver follows a different numerical"
                        "strategy and may perform better depending on the problem type"
                        "and constraints."
                    )

                    if st.button("Find parameters for given target value"):
                        result = minimize(
                            objective_inverse,
                            x0,
                            bounds=bounds,
                            method=selected_solver
                        )

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
                                    "Value": [
                                        st.session_state["optim_result"]["params"][p]
                                        for p in param_order_geom
                                    ]
                                }
                            )
                            st.table(df_opt_params)

                            st.metric(
                                label="Predicted value for optimal parameters",
                                value=f"{st.session_state['optim_result']['y_pred_opt']}"
                            )

                            abs_error = abs(
                                st.session_state['optim_result']['y_pred_opt']
                                - st.session_state['optim_result']['y_target']
                            )
                            st.markdown(f"**Absolute error:** {abs_error}")

                            csv_buffer = io.StringIO()
                            df_opt_params.to_csv(csv_buffer, index=False)
                            csv_data = csv_buffer.getvalue()
                            file_name_csv = (
                                "optimal_parameters_target_value"
                                f"_{st.session_state['optim_result']['y_target']:.4f}.csv"
                            )

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
                            xpath = get_xpath_for_param(
                                tixi,
                                name_parameter,
                                uID_wing,
                                uID_section
                            )
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
                    st.markdown("**Best geometric configuration from AVL simulations**")
                    section_3D_view(
                        working_dir=Path(results_dir),
                        cpacs=CPACS(Path(results_dir) / "best_geometric_configuration.xml"),
                        aircraft_name="best_geometric_configuration",
                    )

            elif child.is_dir():
                with st.expander(child.stem, expanded=True):
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
                uploaded_model = st.file_uploader(
                    "Upload trained surrogate model",
                    type=["pkl"],
                    key='model_uploader'
                )
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
                uploaded_ranges = st.file_uploader(
                    "Upload ranges_for_gui CSV",
                    type=["csv"],
                    key='ranges'
                )
                if uploaded_ranges:
                    temp_dir = tempfile.mkdtemp()
                    ranges_path = os.path.join(temp_dir, uploaded_ranges.name)
                    with open(ranges_path, "wb") as f:
                        f.write(uploaded_ranges.getbuffer())
                    st.session_state.ranges_file_path = ranges_path

                    df = pd.read_csv(uploaded_ranges)
                    sliders_bounds = {
                        row["Parameter"]: (row["Min"],row["Max"]) for _, row in df.iterrows()
                    }
                    sliders_values = {
                        param: bounds[0] for param, bounds in sliders_bounds.items()
                    }
                    st.session_state["sliders_bounds"] = sliders_bounds
                    st.session_state["sliders_values"] = sliders_values
                    st.success("Ranges loaded successfully")
                    st.write(f"The ranges file has been temporarily saved here: {ranges_path}")

                else:
                    st.error("Please upload a RANGES CSV file or manually enter the file path.")

            with col4:
                st.markdown("##### AVL Dataset")
                uploaded_avl_dataset = st.file_uploader(
                    "Upload avl_simulations_results.csv",
                    type=["csv"],
                    key='dataset_avl'
                )
                if uploaded_avl_dataset:
                    temp_dir = tempfile.mkdtemp()
                    avl_dataset_path = os.path.join(temp_dir, uploaded_avl_dataset.name)
                    with open(avl_dataset_path, "wb") as f:
                        f.write(uploaded_avl_dataset.getbuffer())
                    st.session_state.avl_dataset_path = avl_dataset_path
                    st.success("AVL dataset loaded successfully")
                    st.write(
                        f"The dataset file has been temporarily saved here: {avl_dataset_path}"
                    )

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

                p1_range = st.slider(
                    f"Range for {selected_params[0]}",
                    float(p1_min),
                    float(p1_max),
                    (float(p1_min), float(p1_max)),
                    key="rsm_slider_1"
                )
                p2_range = st.slider(
                    f"Range for {selected_params[1]}",
                    float(p2_min),
                    float(p2_max),
                    (float(p2_min), float(p2_max)),
                    key="rsm_slider_2"
                )

                if len(param_order) >= 3:
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

                df_samples = pd.read_csv(avl_dataset_path)

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

                            if len(param_order) >= 3:

                                mask = np.ones(len(df_samples), dtype=bool)
                                tol = 0.1 * (max_val - min_val)
                                for p, val in fixed_param_values.items():
                                    if p in df_samples.columns:
                                        mask &= np.isclose(df_samples[p], val, atol=tol)

                                filtered_samples = df_samples[mask].copy()

                                if (
                                    len(filtered_samples) > 0
                                    and selected_params[0] in filtered_samples.columns
                                    and selected_params[1] in filtered_samples.columns
                                ):
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
                            else:
                                x_samples = df_samples[selected_params[0]].values
                                y_samples = df_samples[selected_params[1]].values

                                output_col = df_samples.columns[-1]
                                if output_col in df_samples.columns:
                                    z_samples = df_samples[output_col].values
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
                help="Nelder-Mead is robust for small datasets; L-BFGS-B is "
                "efficient with larger datasets."
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
                        "Value": [
                            st.session_state["optim_result"]["params"][p]
                            for p in param_order_geom
                        ]
                    })
                    st.table(df_opt_params)

                    st.metric(
                        label="Predicted value for optimal parameters",
                        value=f"{st.session_state['optim_result']['y_pred_opt']}"
                    )
                    abs_error1 = abs(
                        st.session_state['optim_result']['y_pred_opt']
                        - st.session_state['optim_result']['y_target']
                    )
                    st.markdown(f"**Absolute error:** {abs_error1}")

                    csv_buffer = io.StringIO()
                    df_opt_params.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()
                    file_name_csv = "optimal_parameters_target_"
                    f"value_{st.session_state['optim_result']['y_target']}.csv"

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
        current_wkdir = get_wkdir()
        if not current_wkdir or not current_wkdir.exists():
            st.warning("No Workflow working directory found.")
            return

        workflow_dirs = get_workflow_dirs(current_wkdir)
        if not workflow_dirs:
            st.warning("No workflows have been found in the working directory.")
            return

        workflow_names = [wkflow.name for wkflow in workflow_dirs][::-1]
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

        st.tabs(results_name)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    # Define interface
    create_sidebar(HOW_TO_TEXT)

    st.title("Results")
    show_results()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
