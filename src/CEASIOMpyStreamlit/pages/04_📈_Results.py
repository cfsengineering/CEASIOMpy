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
    create_branch,
)

from ceasiompy import log
from ceasiompy.utils.commonpaths import DEFAULT_PARAVIEW_STATE
from scipy.optimize import minimize
import io

from CEASIOMpyStreamlit.streamlitutils import section_3D_view
from ceasiompy.SMTrain.func.config import (
    get_xpath_for_param,
    normalize_input_from_gui,
    phys_to_norm,
    norm_to_phys,
    get_elements_to_optimise,
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
    "rmse_RBF.csv",
    "rmse_KRG.csv",
    "New_CPACS",
    "Validation_plot_RBF",
    "Validation_plot_KRG",
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


def display_results(results_dir, chosen_workflow = None):
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

        child = None
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
                        plt.close(fig)
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
                with st.container(border=True):
                    show_pdf = st.checkbox(
                        f"**{child.stem}**",
                        value=True,
                        key=f"{child}_dir_toggle",
                    )
                    if show_pdf:
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
                            'width="100%" height="900" style="border:0"></iframe>',
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

            elif child.suffix == ".pkl":
                csv_rmse_krg_path = Path(f"{results_dir}/rmse_KRG.csv")
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

                cpacs_in = Path(chosen_workflow, "00_ToolInput.xml")
                tmp_cpacs = CPACS(cpacs_in)
                tixi = tmp_cpacs.tixi

                (_, _, _, ranges_gui, _) = get_elements_to_optimise(tmp_cpacs)

                sliders_values = {}
                sliders_bounds = {}

                csv_path_sampling = (
                    chosen_workflow
                    / "Results"
                    / "SMTrain"
                    / "Low_Fidelity"
                    / "avl_simulations_results.csv"
                )

                df_samples = None
                if csv_path_sampling.exists():
                    df_samples = pd.read_csv(csv_path_sampling)
                if df_samples is None:
                    st.warning("No sampling data available.")

                for param, bounds in ranges_gui.items():
                    min_val = float(bounds[0])
                    max_val = float(bounds[1])
                    sliders_bounds[param] = [min_val, max_val]
                    sliders_values[param] = min_val

                krg_model_path = results_dir / "surrogateModel_krg.pkl"
                rbf_model_path = results_dir / "surrogateModel_rbf.pkl"

                if krg_model_path.exists() and rbf_model_path.exists():
                    model_selected = st.radio(
                        "Select the model to visualize:",
                        ["RBF" , "KRG"],
                        index=0,
                        horizontal=True,
                        key="model_select_radio",
                    )

                    model_path = rbf_model_path if model_selected == "RBF" else krg_model_path
                elif krg_model_path.exists():
                    model_path = krg_model_path
                elif rbf_model_path.exists():
                    model_path = rbf_model_path

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

                final_level1_df = pd.read_csv(csv_path_sampling)
                param_cols = final_level1_df.columns[:-1]

                df_norm = final_level1_df.copy()
                normalization_params = {}

                for col in param_cols:
                    col_mean = final_level1_df[col].mean()
                    col_std = final_level1_df[col].std()
                    if col_std == 0:
                        df_norm[col] = 0.0
                    else:
                        df_norm[col] = (final_level1_df[col] - col_mean) / col_std
                    normalization_params[col] = {"mean": col_mean, "std": col_std}

                norm_df = pd.DataFrame.from_dict(
                    normalization_params,
                    orient="index"
                ).reset_index()

                norm_df.columns = ["Parameter", "mean", "std"]

                # normalization_params = load_normalization_params(results_dir)
                missing = [p for p in param_order if p not in normalization_params]
                if missing:
                    log.error(f"Missing normalization parameters for: {missing}")
                    st.error(f"Missing normalization parameters for: {missing}")
                    st.stop()

                if model is not None and len(param_order) >= 2:
                    st.subheader("Sobol Global Sensitivity Analysis")
                    sobol_params = []
                    sobol_bounds = []

                    for p in param_order:
                        min_val, max_val = sliders_bounds[p]
                        if max_val > min_val:
                            sobol_params.append(p)
                            sobol_bounds.append([min_val, max_val])

                    # ---- DEFINE PROBLEM ----
                    problem = {
                        "num_vars": len(sobol_params),
                        "names": sobol_params,
                        "bounds": sobol_bounds,
                    }

                    # ---- GENERATE SAMPLES ----
                    N = 256
                    sample_set = saltelli.sample(problem, N)

                    # ---- RUN MODEL ----
                    Y = []
                    for s in sample_set:
                        x_phys = np.zeros(len(param_order))
                        for i, p in enumerate(param_order):
                            if p in sobol_params:
                                x_phys[i] = s[sobol_params.index(p)]
                            else:
                                x_phys[i] = sliders_bounds[p][0]
                        x_norm = normalize_input_from_gui(
                            {p: x_phys[i] for i, p in enumerate(param_order)},
                            param_order,
                            normalization_params
                        )
                        Y.append(model.predict_values(x_norm.reshape(1, -1))[0])

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

                        fixed_param_values = {}
                        if len(param_order) >= 3:
                            st.markdown("**Fix values for other parameters:**")
                            for p in param_order:
                                if p not in selected_params:
                                    low, high = sliders_bounds.get(p, (0, 0))
                                    fixed_param_values[p] = st.slider(
                                        f"{p}",
                                        float(low),
                                        float(high),
                                        float((low + high) / 2),
                                        key=f"fixed_slider_{p}"
                                    )

                        if st.button("Generate response surface"):
                            with st.spinner("Calculating response surface..."):
                                # Create meshgrid for the two selected parameters
                                param1_lin = np.linspace(p1_range[0], p1_range[1], 50)
                                param2_lin = np.linspace(p2_range[0], p2_range[1], 50)
                                P1, P2 = np.meshgrid(param1_lin, param2_lin)

                                # Prepare full input matrix
                                inputs_norm = np.zeros((P1.size, len(param_order)))
                                for i, p in enumerate(param_order):
                                    if p == selected_params[0]:
                                        inputs_norm[:, i] = (P1.ravel() - normalization_params[p]["mean"]) / normalization_params[p]["std"]
                                    elif p == selected_params[1]:
                                        inputs_norm[:, i] = (P2.ravel() - normalization_params[p]["mean"]) / normalization_params[p]["std"]
                                    else:
                                        val = fixed_param_values.get(p, sliders_bounds[p][0])
                                        mean = normalization_params[p]["mean"]
                                        std  = normalization_params[p]["std"]
                                        inputs_norm[:, i] = 0.0 if std == 0 else (val - mean) / std

                                # Predict on normalized inputs
                                try:
                                    Z = model.predict_values(inputs_norm).reshape(P1.shape)

                                    fig = go.Figure(data=[go.Surface(x=P1, y=P2, z=Z, colorscale="RdBu", showscale=True)])

                                    # Add sample points if available
                                    if df_samples is not None:
                                        mask = np.ones(len(df_samples), dtype=bool)
                                        for p, val in fixed_param_values.items():
                                            if p in df_samples.columns:
                                                tol = 0.01 * (sliders_bounds[p][1] - sliders_bounds[p][0])
                                                mask &= np.isclose(df_samples[p], val, atol=tol)

                                        filtered_samples = df_samples[mask] if mask.any() else df_samples
                                        x_samples = filtered_samples[selected_params[0]].values
                                        y_samples = filtered_samples[selected_params[1]].values
                                        z_samples = filtered_samples[df_samples.columns[-1]].values

                                        fig.add_trace(go.Scatter3d(
                                            x=x_samples, y=y_samples, z=z_samples,
                                            mode='markers',
                                            marker=dict(size=2, color='green'),
                                            name=f"🟢 Training Samples (n={len(x_samples)})",
                                            showlegend=True,
                                            legendgroup="samples",
                                        ))

                                    fig.update_layout(
                                        showlegend=True,
                                        legend=dict(
                                            yanchor="top",
                                            y=0.99,
                                            xanchor="left",
                                            x=0.75
                                        ),
                                        title='Surrogate Model Response Surface',
                                        scene=dict(
                                            xaxis_title=selected_params[0],
                                            yaxis_title=selected_params[1],
                                            zaxis_title='Predicted Output'
                                        )
                                    )

                                    st.plotly_chart(fig, use_container_width=True)

                                except Exception as e:
                                    st.error(f"Error predicting response surface: {e}")

                    else:
                        st.error("Please select 2 parameters.")

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

                    new_file_path = Path(results_dir) / "temp_manual_geom_from_gui.xml"
                    tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

                    with col_3d:
                        st.subheader('| 3D View')
                        section_3D_view(
                            results_dir=results_dir,
                            cpacs=CPACS(new_file_path),
                            force_regenerate=True,
                            file_name = "temp_manual_geom_from_gui",
                        )

                    # Normalize GUI input
                    x_norm = normalize_input_from_gui(
                        sliders_values,
                        param_order,
                        normalization_params
                    )

                    # Predict
                    raw_predicted_value = model.predict_values(
                        x_norm.reshape(1, -1)
                    )[0]
                    predicted_value = float(raw_predicted_value.item())
                    st.metric("Predicted objective value", f"{predicted_value:.2f}")

                    with col_3d:
                        with open(new_file_path, "rb") as f:
                            cpacs_data = f.read()

                        st.download_button(
                                label="Download CPACS file",
                                data=cpacs_data,
                                file_name=f"configuration_predicted_value_{predicted_value}.xml",
                                mime="application/xml"
                            )

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

                    st.subheader("Target-based exploration")
                    param_order_geom = [p for p in param_order if p in sliders_bounds]

                    x0_phys = np.array([sliders_values[p] for p in param_order_geom])
                    x0 = phys_to_norm(x0_phys, param_order_geom, normalization_params)

                    bounds = []
                    for p in param_order_geom:
                        lo, hi = sliders_bounds[p]
                        mean = normalization_params[p]["mean"]
                        std  = normalization_params[p]["std"]
                        if std == 0:
                            bounds.append((0.0, 0.0))
                        else:
                            bounds.append(((lo - mean) / std, (hi - mean) / std))

                    # input target
                    y_pred_init = model.predict_values(x0.reshape(1, -1))[0]
                    y_target = st.number_input(
                        "Enter target value",
                        value=float(y_pred_init[0]),
                        step=0.0001,
                        format="%0.2f"
                    )
                    
                    selected_solver = st.selectbox(
                        label="Choose the solver",
                        options=["L-BFGS-B","Powell","COBYLA","TNC","Nelder-Mead"],
                        help="Select the algorithm to be used for minimizing"
                        "the objective function. Each solver follows a different numerical"
                        "strategy and may perform better depending on the problem type"
                        "and constraints."
                    )

                    def objective_inverse(x_norm):
                        x_full = []
                        for p in param_order:
                            if p in param_order_geom:
                                i = param_order_geom.index(p)
                                x_full.append(x_norm[i])
                            else:
                                val_phys = sliders_values[p]
                                mean = normalization_params[p]["mean"]
                                std  = normalization_params[p]["std"]
                                x_full.append(0.0 if std == 0 else (val_phys - mean) / std)
                        x_full = np.array(x_full)
                        y_pred = float(model.predict_values(x_full.reshape(1, -1))[0, 0])
                        return abs(y_pred - y_target)

                    if st.button("Find parameters for given target value"):
                        result = minimize(
                            objective_inverse,
                            x0,
                            bounds=bounds,
                            method=selected_solver
                        )

                        if not result.success:
                            st.error(f"Optimization failed: {result.message}")
                            st.write("Last x:", result.x)
                            st.write("Objective value:", result.fun)
                            return

                        if result.success:
                            x_opt_phys = norm_to_phys(
                                result.x,
                                param_order_geom,
                                normalization_params
                            )

                            input_dict_opt = dict(zip(param_order_geom, x_opt_phys))

                            x_full_norm = []
                            for p in param_order:
                                if p in input_dict_opt:
                                    val = input_dict_opt[p]
                                else:
                                    val = sliders_values[p]
                                mean = normalization_params[p]["mean"]
                                std  = normalization_params[p]["std"]
                                x_full_norm.append(0.0 if std == 0 else (val - mean)/std)

                            y_pred_opt = float(
                                model.predict_values(np.array(x_full_norm).reshape(1, -1))[0, 0]
                            )

                            st.session_state.optim_result = {
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
                                value=f"{st.session_state['optim_result']['y_pred_opt']:.2f}"
                            )

                            abs_error = abs(
                                st.session_state['optim_result']['y_pred_opt']
                                - st.session_state['optim_result']['y_target']
                            )
                            st.markdown(f"**Absolute error:** {abs_error:.6f}")

                            csv_buffer = io.StringIO()
                            df_opt_params.to_csv(csv_buffer, index=False)
                            csv_data = csv_buffer.getvalue()
                            file_name_csv = (
                                "optimal_parameters_target_value"
                                f"_{st.session_state['optim_result']['y_target']:.2f}.csv"
                            )

                            st.download_button(
                                label="Download parameters in CSV file",
                                data=csv_data,
                                file_name=file_name_csv,
                                mime="text/csv",
                            )

                        tmp_cpacs = CPACS(Path(chosen_workflow, "00_ToolInput.xml"))
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

                        new_file_path = Path(results_dir) / "temp_target_geometry_from_gui.xml"
                        tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

                        with col_view:
                            st.subheader("| 3D View")

                            section_3D_view(
                                results_dir=Path(results_dir),
                                cpacs=CPACS(new_file_path),
                                force_regenerate=True,
                                file_name="temp_optim_geometry",
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
                with st.expander(f"{child.name}"):
                    st.markdown(f"**{child.name}**")
                    st.dataframe(pd.read_csv(child))

            elif child.name == "best_geometric_configuration_low_fidelity.xml":
                with st.expander("Best geometric configuration from AVL simulations"):
                    st.markdown("**Best geometric configuration from AVL simulations**")
                    section_3D_view(
                        results_dir=Path(results_dir),
                        cpacs=CPACS(Path(results_dir) / "best_geometric_configuration_low_fidelity.xml"),
                    )

            elif child.name == "best_surrogate_geometry_RBF.xml":
                with st.expander("Best geometric configuration from surrogate model predictions"):
                    st.markdown("**Best geometric configuration from surrogate model predictions**")
                    section_3D_view(
                        results_dir=Path(results_dir),
                        cpacs=CPACS(Path(results_dir) / "best_surrogate_geometry_RBF.xml"),
                    )
            
            elif child.name == "best_surrogate_geometry_KRG.xml":
                with st.expander("Best geometric configuration from surrogate model predictions"):
                    st.markdown("**Best geometric configuration from surrogate model predictions**")
                    section_3D_view(
                        results_dir=Path(results_dir),
                        cpacs=CPACS(Path(results_dir) / "best_surrogate_geometry_KRG.xml"),
                    )

            elif child.is_dir():
                with st.container(border=True):
                    show_dir = st.checkbox(
                        f"**{child.stem}**",
                        value=False,
                        key=f"{child}_dir_toggle",
                    )
                    if show_dir:
                        display_results(child)

    except BaseException as e:
        log.warning(f'{child=} {e=}')
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

    workflow_names = [wkflow.name for wkflow in workflow_dirs][::-1]
    default_index = 0
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
            display_results(Path(results_dir, tab_name), chosen_workflow)

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
