"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy
"""

# Imports
import os
import base64
import tempfile
import numpy as np
import pandas as pd
import pyvista as pv
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components

from stpyvista import stpyvista
from functools import lru_cache
from ceasiompy.utils.commonpaths import get_wkdir
from ceasiompy.utils.ceasiompyutils import workflow_number
from parsefunctions import (
    parse_ascii_tables,
    display_avl_table_file,
)
from streamlitutils import (
    create_sidebar,
    section_3D_view,
    highlight_stability,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from constants import BLOCK_CONTAINER
from ceasiompy.pyavl import AVL_TABLE_FILES
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# Constants

HOW_TO_TEXT = (
    "### Results \n"
    "1. Check each module's outputs"
)

PAGE_NAME = "Results"
IGNORED_RESULT_FILES: set[str] = {
    # AVL
    "avl_commands.txt",
    "logfile_avl.log",

    # SU2
    "restart_flow.dat",
    "rmse_RBF.csv",
    "rmse_KRG.csv",
    "New_CPACS",
    "Validation_plot_RBF",
    "Validation_plot_KRG",
}


# Functions

def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:4096]
    if b"\x00" in sample:
        return True
    text_chars = b"\t\n\r\f\b" + bytes(range(32, 127))
    nontext = sum(byte not in text_chars for byte in sample)
    return nontext / len(sample) > 0.3


def show_results():
    """Display the results of the selected workflow."""

    current_wkdir = get_wkdir()
    if not current_wkdir or not current_wkdir.exists():
        st.warning("No Workflow working directory found.")
        return

    workflow_dirs = _get_workflow_dirs(current_wkdir)
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
    results_dirs = [dir for dir in results_dir.iterdir() if dir.is_dir()]
    results_names = [dir.stem for dir in results_dirs]
    workflow_module_order = _get_workflow_module_order(chosen_workflow)
    ordered_results = [name for name in workflow_module_order if name in results_names]
    unordered_results = sorted([name for name in results_names if name not in ordered_results])
    results_name = ordered_results + unordered_results
    if not results_name:
        st.warning("No results have been found!")
        return

    results_tabs = st.tabs(results_name)

    for tab, tab_name in zip(results_tabs, results_name):
        with tab:
            display_results(Path(results_dir, tab_name))


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
        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
        else:
            content = data.decode("utf-8", errors="replace")
            st.text_area(path.stem, content, height=200, key=f"{path}_text_fallback")


def display_results(results_dir):
    if not Path(results_dir).is_dir():
        display_results_else(results_dir)
        return

    # Display results depending on the file type.
    container_list = [
        "logs_container",
        "figures_container",
        "paraview_container",
        "pdf_container",
    ]
    clear_containers(container_list)

    for child in sorted(Path(results_dir).iterdir(), key=_results_sort_key):
        if child.name in IGNORED_RESULT_FILES:
            continue
        try:
            if child.suffix == ".dat":
                _display_dat(child)

            elif child.suffix == ".su2":
                _display_su2(child)

            elif child.suffix == ".vtu":
                _display_vtu(child)

            elif child.suffix == ".png":
                _display_png(child)

            elif child.suffix == ".pdf":
                _display_pdf(child)

            elif child.suffix == ".md":
                _display_md(child)

            elif child.suffix == ".json":
                _display_json(child)

            elif child.suffix == ".txt":
                _display_txt(child)

            elif child.suffix == ".log":
                _display_log(child)

            elif child.suffix == ".csv":
                _display_csv(child)

            elif child.suffix == ".xml":
                _display_xml(child)

            elif child.suffix == ".html":
                _display_html(child)

            elif child.is_dir():
                with st.container(border=True):
                    show_dir = st.checkbox(
                        f"**{child.stem}**",
                        value=True,
                        key=f"{child}_dir_toggle",
                    )
                    if show_dir:
                        display_results(child)
        except BaseException as e:
            log.warning(f"Could not display {child}: {e=}")
            display_results_else(child)


# Methods


# def _display_plk(path: Path) -> None:
#     csv_rmse_krg_path = Path(f"{results_dir}/rmse_KRG.csv")
#     if csv_rmse_krg_path.exists():
#         rmse_krg_df = pd.read_csv(csv_rmse_krg_path)
#         rmse_krg_value = rmse_krg_df["rmse"].iloc[0]
#         st.markdown(f"##### Root Mean Square Error of KRG model: {rmse_krg_value:.6f}")

#     csv_rmse_rbf_path = Path(f"{results_dir}/rmse_RBF.csv")
#     rmse_rbf_df = None
#     if csv_rmse_rbf_path.exists():
#         rmse_rbf_df = pd.read_csv(csv_rmse_rbf_path)
#         rmse_rbf_value = rmse_rbf_df["rmse"].iloc[0]
#         st.markdown(f"##### Root Mean Square Error of RBF model: {rmse_rbf_value:.6f}")

#     cpacs_in = Path(chosen_workflow, "00_ToolInput.xml")
#     tmp_cpacs = CPACS(cpacs_in)
#     tixi = tmp_cpacs.tixi

#     (_, _, _, ranges_gui, _) = get_elements_to_optimise(tmp_cpacs)

#     sliders_values = {}
#     sliders_bounds = {}

#     csv_path_sampling = (
#         chosen_workflow
#         / "Results"
#         / "SMTrain"
#         / "Low_Fidelity"
#         / "avl_simulations_results.csv"
#     )

#     df_samples = None
#     if csv_path_sampling.exists():
#         df_samples = pd.read_csv(csv_path_sampling)
#     if df_samples is None:
#         st.warning("No sampling data available.")

#     for param, bounds in ranges_gui.items():
#         min_val = float(bounds[0])
#         max_val = float(bounds[1])
#         sliders_bounds[param] = [min_val, max_val]
#         sliders_values[param] = min_val

#     krg_model_path = results_dir / "surrogateModel_krg.pkl"
#     rbf_model_path = results_dir / "surrogateModel_rbf.pkl"

#     if krg_model_path.exists() and rbf_model_path.exists():
#         model_selected = st.radio(
#             "Select the model to visualize:",
#             ["RBF" , "KRG"],
#             index=0,
#             horizontal=True,
#             key="model_select_radio",
#         )

#         model_path = rbf_model_path if model_selected == "RBF" else krg_model_path
#     elif krg_model_path.exists():
#         model_path = krg_model_path
#     elif rbf_model_path.exists():
#         model_path = rbf_model_path

#     model, param_order = None, None
#     if model_path.exists():
#         with open(model_path, "rb") as file:
#             data = joblib.load(file)
#         model = data["model"]
#         param_order = data["param_order"]
#     else:
#         st.warning(
#             "⚠️ Surrogate model not found. Only geometry "
#             "sliders will be available."
#         )

#     final_level1_df = pd.read_csv(csv_path_sampling)
#     param_cols = final_level1_df.columns[:-1]

#     df_norm = final_level1_df.copy()
#     normalization_params = {}

#     for col in param_cols:
#         col_mean = final_level1_df[col].mean()
#         col_std = final_level1_df[col].std()
#         if col_std == 0:
#             df_norm[col] = 0.0
#         else:
#             df_norm[col] = (final_level1_df[col] - col_mean) / col_std
#         normalization_params[col] = {"mean": col_mean, "std": col_std}

#     norm_df = pd.DataFrame.from_dict(
#         normalization_params,
#         orient="index"
#     ).reset_index()

#     norm_df.columns = ["Parameter", "mean", "std"]

#     # normalization_params = load_normalization_params(results_dir)
#     missing = [p for p in param_order if p not in normalization_params]
#     if missing:
#         log.error(f"Missing normalization parameters for: {missing}")
#         st.error(f"Missing normalization parameters for: {missing}")
#         st.stop()

#     if model is not None and len(param_order) >= 2:
#         st.subheader("Sobol Global Sensitivity Analysis")
#         sobol_params = []
#         sobol_bounds = []

#         for p in param_order:
#             min_val, max_val = sliders_bounds[p]
#             if max_val > min_val:
#                 sobol_params.append(p)
#                 sobol_bounds.append([min_val, max_val])

#         # ---- DEFINE PROBLEM ----
#         problem = {
#             "num_vars": len(sobol_params),
#             "names": sobol_params,
#             "bounds": sobol_bounds,
#         }

#         # ---- GENERATE SAMPLES ----
#         N = 256
#         sample_set = saltelli.sample(problem, N)

#         # ---- RUN MODEL ----
#         Y = []
#         for s in sample_set:
#             x_phys = np.zeros(len(param_order))
#             for i, p in enumerate(param_order):
#                 if p in sobol_params:
#                     x_phys[i] = s[sobol_params.index(p)]
#                 else:
#                     x_phys[i] = sliders_bounds[p][0]
#             x_norm = normalize_input_from_gui(
#                 {p: x_phys[i] for i, p in enumerate(param_order)},
#                 param_order,
#                 normalization_params
#             )
#             Y.append(model.predict_values(x_norm.reshape(1, -1))[0])

#         Y = np.array(Y).flatten()

#         # ---- SOBOL ANALYSIS ----
#         Si = sobol.analyze(problem, Y)

#         # ---- CONVERT TO DATAFRAME ----
#         sens_df = pd.DataFrame({
#             "Parameter": param_order,
#             "Single effect index Si": Si["S1"],
#             "Total-effect index ST": Si["ST"]
#         })

#         sens_df[["Single effect index Si", "Total-effect index ST"]] = sens_df[
#             ["Single effect index Si", "Total-effect index ST"]
#         ].clip(lower=0)

#         sens_df = sens_df.sort_values(by="Total-effect index ST", ascending=False)

#         # ---- SHOW RESULTS ----
#         sens_df_melted = sens_df.melt(
#             id_vars="Parameter",
#             value_vars=["Single effect index Si", "Total-effect index ST"],
#             var_name="Type",
#             value_name="Sensitivity"
#         )

#         chart = alt.Chart(sens_df_melted).mark_bar().encode(
#             x=alt.X("Parameter:N", sort=None, title="Parameter"),
#             y=alt.Y("Sensitivity:Q", title="Sobol Index"),
#             color=alt.Color("Type:N", scale=alt.Scale(scheme="category10")),
#             xOffset="Type:N",
#             tooltip=["Parameter", "Type", "Sensitivity"]
#         ).properties(width=600, height=400)

#         st.altair_chart(chart)

#         st.subheader("Response Surface Visualization")
#         # Let user select 2 params to visualize
#         selected_params = st.multiselect(
#             "Select exactly 2 parameters to visualize:",
#             options=param_order,
#             default=param_order[:2],
#             key="rsm_param_select"
#         )

#         if len(selected_params) == 2:
#             p1_min, p1_max = sliders_bounds.get(selected_params[0], (-5, 15))
#             p2_min, p2_max = sliders_bounds.get(selected_params[1], (-5, 15))

#             p1_range = st.slider(
#                 f"Range for {selected_params[0]}",
#                 float(p1_min),
#                 float(p1_max),
#                 (float(p1_min), float(p1_max)),
#                 key="rsm_slider_1"
#             )
#             p2_range = st.slider(
#                 f"Range for {selected_params[1]}",
#                 float(p2_min),
#                 float(p2_max),
#                 (float(p2_min), float(p2_max)),
#                 key="rsm_slider_2"
#             )

#             fixed_param_values = {}
#             if len(param_order) >= 3:
#                 st.markdown("**Fix values for other parameters:**")
#                 for p in param_order:
#                     if p not in selected_params:
#                         low, high = sliders_bounds.get(p, (0, 0))
#                         fixed_param_values[p] = st.slider(
#                             f"{p}",
#                             float(low),
#                             float(high),
#                             float((low + high) / 2),
#                             key=f"fixed_slider_{p}"
#                         )

#             if st.button("Generate response surface"):
#                 with st.spinner("Calculating response surface..."):
#                     # Create meshgrid for the two selected parameters
#                     param1_lin = np.linspace(p1_range[0], p1_range[1], 50)
#                     param2_lin = np.linspace(p2_range[0], p2_range[1], 50)
#                     P1, P2 = np.meshgrid(param1_lin, param2_lin)

#                     # Prepare full input matrix
#                     inputs_norm = np.zeros((P1.size, len(param_order)))
#                     for i, p in enumerate(param_order):
#                         if p == selected_params[0]:
#                             inputs_norm[:, i] = (
# P1.ravel() - normalization_params[p]["mean"]) / normalization_params[p]["std"]
#                         elif p == selected_params[1]:
#                             inputs_norm[:, i] = (
# P2.ravel() - normalization_params[p]["mean"]) / normalization_params[p]["std"]
#                         else:
#                             val = fixed_param_values.get(p, sliders_bounds[p][0])
#                             mean = normalization_params[p]["mean"]
#                             std  = normalization_params[p]["std"]
#                             inputs_norm[:, i] = 0.0 if std == 0 else (val - mean) / std

#                     # Predict on normalized inputs
#                     try:
#                         Z = model.predict_values(inputs_norm).reshape(P1.shape)

#                         fig = go.Figure(data=[go.Surface(
# x=P1, y=P2, z=Z, colorscale="RdBu", showscale=True)])

#                         # Add sample points if available
#                         if df_samples is not None:
#                             mask = np.ones(len(df_samples), dtype=bool)
#                             for p, val in fixed_param_values.items():
#                                 if p in df_samples.columns:
#                                     tol = 0.01 * (sliders_bounds[p][1] - sliders_bounds[p][0])
#                                     mask &= np.isclose(df_samples[p], val, atol=tol)

#                             filtered_samples = df_samples[mask] if mask.any() else df_samples
#                             x_samples = filtered_samples[selected_params[0]].values
#                             y_samples = filtered_samples[selected_params[1]].values
#                             z_samples = filtered_samples[df_samples.columns[-1]].values

#                             fig.add_trace(go.Scatter3d(
#                                 x=x_samples, y=y_samples, z=z_samples,
#                                 mode='markers',
#                                 marker=dict(size=1, color='green'),
#                                 name=f"🟢 Training Samples (n={len(x_samples)})",
#                                 showlegend=True,
#                                 legendgroup="samples",
#                             ))

#                         fig.update_layout(
#                             showlegend=True,
#                             legend=dict(
#                                 yanchor="top",
#                                 y=0.99,
#                                 xanchor="left",
#                                 x=0.5
#                             ),
#                             title='Surrogate Model Response Surface',
#                             scene=dict(
#                                 xaxis_title=selected_params[0],
#                                 yaxis_title=selected_params[1],
#                                 zaxis_title='Predicted Output'
#                             )
#                         )

#                         st.plotly_chart(fig, width="stretch")

#                     except Exception as e:
#                         st.error(f"Error predicting response surface: {e}")

#         else:
#             st.error("Please select 2 parameters.")

#     mode = st.radio(
#         "Select mode:",
#         ["Manual exploration", "Target-based exploration"],
#         index=0,
#         horizontal=True,
#     )

#     if mode == "Manual exploration":
#         col_tuning, col_3d = st.columns(2)
#         with col_tuning:
#             st.subheader('Parameters')
#             for param, (min_val, max_val) in sliders_bounds.items():
#                 sliders_values[param] = st.slider(
#                     f'{param}',
#                     min_val,
#                     max_val,
#                     min_val,
#                     0.01,
#                     key=f"slider_{param}"
#                 )

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

#         new_file_path = Path(results_dir) / "temp_manual_geom_from_gui.xml"
#         tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

#         with col_3d:
#             st.subheader('| 3D View')
#             section_3D_view(
#                 results_dir=results_dir,
#                 cpacs=CPACS(new_file_path),
#                 force_regenerate=True,
#                 file_name = "temp_manual_geom_from_gui",
#             )

#         # Normalize GUI input
#         x_norm = normalize_input_from_gui(
#             sliders_values,
#             param_order,
#             normalization_params
#         )

#         # Predict
#         raw_predicted_value = model.predict_values(
#             x_norm.reshape(1, -1)
#         )[0]
#         predicted_value = float(raw_predicted_value.item())
#         st.metric("Predicted objective value", f"{predicted_value:.2f}")

#         with col_3d:
#             with open(new_file_path, "rb") as f:
#                 cpacs_data = f.read()

#             st.download_button(
#                     label="Download CPACS file",
#                     data=cpacs_data,
#                     file_name=f"configuration_predicted_value_{predicted_value}.xml",
#                     mime="application/xml"
#                 )

#         df_config = pd.DataFrame(
#             list(sliders_values.items()),
#             columns=['Parameter', 'Value']
#         )
#         csv_buffer = io.StringIO()
#         df_config.to_csv(csv_buffer, index=False)
#         csv_data = csv_buffer.getvalue()
#         file_name_csv = f"configuration_for_obj_{predicted_value}.csv"

#         st.download_button(
#             label="Download configuration in CSV file",
#             data=csv_data,
#             file_name=file_name_csv,
#             mime="text/csv",
#         )

#     elif mode == "Target-based exploration":

#         st.subheader("Target-based exploration")
#         param_order_geom = [p for p in param_order if p in sliders_bounds]

#         x0_phys = np.array([sliders_values[p] for p in param_order_geom])
#         x0 = phys_to_norm(x0_phys, param_order_geom, normalization_params)

#         bounds = []
#         for p in param_order_geom:
#             lo, hi = sliders_bounds[p]
#             mean = normalization_params[p]["mean"]
#             std  = normalization_params[p]["std"]
#             if std == 0:
#                 bounds.append((0.0, 0.0))
#             else:
#                 bounds.append(((lo - mean) / std, (hi - mean) / std))

#         # input target
#         y_pred_init = model.predict_values(x0.reshape(1, -1))[0]
#         y_target = st.number_input(
#             "Enter target value",
#             value=float(y_pred_init[0]),
#             step=0.0001,
#             format="%0.2f"
#         )
#         selected_solver = st.selectbox(
#             label="Choose the solver",
#             options=["L-BFGS-B","Powell","COBYLA","TNC","Nelder-Mead"],
#             help="Select the algorithm to be used for minimizing"
#             "the objective function. Each solver follows a different numerical"
#             "strategy and may perform better depending on the problem type"
#             "and constraints."
#         )

#         def objective_inverse(x_norm):
#             x_full = []
#             for p in param_order:
#                 if p in param_order_geom:
#                     i = param_order_geom.index(p)
#                     x_full.append(x_norm[i])
#                 else:
#                     val_phys = sliders_values[p]
#                     mean = normalization_params[p]["mean"]
#                     std  = normalization_params[p]["std"]
#                     x_full.append(0.0 if std == 0 else (val_phys - mean) / std)
#             x_full = np.array(x_full)
#             y_pred = float(model.predict_values(x_full.reshape(1, -1))[0, 0])
#             return abs(y_pred - y_target)

#         if st.button("Find parameters for given target value"):
#             result = minimize(
#                 objective_inverse,
#                 x0,
#                 bounds=bounds,
#                 method=selected_solver
#             )

#             if not result.success:
#                 st.error(f"Optimization failed: {result.message}")
#                 st.write("Last x:", result.x)
#                 st.write("Objective value:", result.fun)
#                 return

#             if result.success:
#                 x_opt_phys = norm_to_phys(
#                     result.x,
#                     param_order_geom,
#                     normalization_params
#                 )

#                 input_dict_opt = dict(zip(param_order_geom, x_opt_phys))

#                 x_full_norm = []
#                 for p in param_order:
#                     if p in input_dict_opt:
#                         val = input_dict_opt[p]
#                     else:
#                         val = sliders_values[p]
#                     mean = normalization_params[p]["mean"]
#                     std  = normalization_params[p]["std"]
#                     x_full_norm.append(0.0 if std == 0 else (val - mean)/std)

#                 y_pred_opt = float(
#                     model.predict_values(np.array(x_full_norm).reshape(1, -1))[0, 0]
#                 )

#                 st.session_state.optim_result = {
#                     "params": input_dict_opt,
#                     "y_pred_opt": y_pred_opt,
#                     "y_target": y_target,
#                 }

#         if "optim_result" in st.session_state:
#             col_tab, col_view = st.columns([0.6,0.4])
#             with col_tab:
#                 st.subheader("Parameter values")
#                 df_opt_params = pd.DataFrame(
#                     {
#                         "Parameter": param_order_geom,
#                         "Value": [
#                             st.session_state["optim_result"]["params"][p]
#                             for p in param_order_geom
#                         ]
#                     }
#                 )
#                 st.table(df_opt_params)

#                 st.metric(
#                     label="Predicted value for optimal parameters",
#                     value=f"{st.session_state['optim_result']['y_pred_opt']:.2f}"
#                 )

#                 abs_error = abs(
#                     st.session_state['optim_result']['y_pred_opt']
#                     - st.session_state['optim_result']['y_target']
#                 )
#                 st.markdown(f"**Absolute error:** {abs_error:.6f}")

#                 csv_buffer = io.StringIO()
#                 df_opt_params.to_csv(csv_buffer, index=False)
#                 csv_data = csv_buffer.getvalue()
#                 file_name_csv = (
#                     "optimal_parameters_target_value"
#                     f"_{st.session_state['optim_result']['y_target']:.2f}.csv"
#                 )

#                 st.download_button(
#                     label="Download parameters in CSV file",
#                     data=csv_data,
#                     file_name=file_name_csv,
#                     mime="text/csv",
#                 )

#             tmp_cpacs = CPACS(Path(chosen_workflow, "00_ToolInput.xml"))
#             tixi = tmp_cpacs.tixi

#             for name, val in st.session_state["optim_result"]["params"].items():
#                 if "_of_" not in name:
#                     continue
#                 parts = name.split("_of_")
#                 name_parameter, uID_section, uID_wing = parts
#                 xpath = get_xpath_for_param(
#                     tixi,
#                     name_parameter,
#                     uID_wing,
#                     uID_section
#                 )
#                 create_branch(tixi, xpath)
#                 tixi.updateDoubleElement(xpath, float(val), "%g")

#             new_file_path = Path(results_dir) / "temp_target_geometry_from_gui.xml"
#             tmp_cpacs.save_cpacs(new_file_path, overwrite=True)

#             with col_view:
#                 st.subheader("| 3D View")

#                 section_3D_view(
#                     results_dir=Path(results_dir),
#                     cpacs=CPACS(new_file_path),
#                     force_regenerate=True,
#                     file_name="temp_optim_geometry",
#                 )

#                 with open(new_file_path, "rb") as f:
#                     cpacs_data = f.read()

#                 st.download_button(
#                     label="Download CPACS file",
#                     data=cpacs_data,
#                     file_name=f"temp_optim_geometry_{y_target}.xml",
#                     mime="application/xml"
#                 )


def _display_html(path: Path) -> None:
    with st.container(border=True):
        show_html = st.checkbox(
            label=f"**{path.name}**",
            value=True,
            key=f"{path}_html_toggle",
        )
        if not show_html:
            return None
        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
            return None
        html_text = data.decode("utf-8", errors="replace")
        components.html(html_text, height=500, scrolling=True)


def _display_md(path: Path) -> None:
    with st.container(border=True):
        md_data = path.read_bytes()
        if _looks_binary(md_data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
            return None

        md_text = md_data.decode("utf-8", errors="replace")
        html = highlight_stability(md_text)
        st.markdown(html, unsafe_allow_html=True)


def _display_log(path: Path) -> None:
    if "logs_container" not in st.session_state:
        st.session_state["logs_container"] = st.container()

    log_data = path.read_bytes()
    if _looks_binary(log_data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None

    log_text = log_data.decode("utf-8", errors="replace")
    if path.name == "logfile_SU2_CFD.log":
        with st.session_state.logs_container:
            with st.container(border=True):
                if st.checkbox(
                    label=f"**{path.name}**",
                    value=False,
                ):
                    segments = parse_ascii_tables(log_text)
                    for kind, payload in segments:
                        if kind == "text":
                            if payload.strip():
                                st.code(payload)
                        else:
                            rows = payload
                            if len(rows) > 1 and len(rows[0]) == len(rows[1]):
                                df = pd.DataFrame(rows[1:], columns=rows[0])
                            else:
                                df = pd.DataFrame(rows)
                            st.table(df)
        return None

    with st.session_state.logs_container:
        st.text_area(
            path.stem,
            log_text,
            height=200,
            key=f"{path}_log_text",
        )


def _display_txt(path: Path) -> None:
    if path.name in AVL_TABLE_FILES:
        display_avl_table_file(path)
        return None

    with st.container(border=True):
        show_txt = st.checkbox(
            label=f"**{path.name}**",
            value=True,
            key=f"{path}_txt_toggle",
        )
        if not show_txt:
            return None
        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
            return None
        text_data = data.decode("utf-8", errors="replace")
        st.text_area(
            path.stem,
            text_data,
            height=200,
            key=f"{path}_txt_raw",
        )


def _display_su2(path: Path) -> None:
    """Display SU2 mesh in Streamlit using PyVista."""
    with st.container(border=True):
        st.markdown(f"**{path.name}**")
        try:
            st.download_button(
                label="Download SU2 mesh",
                data=path.read_bytes(),
                file_name=path.name,
                mime="application/octet-stream",
                width="stretch",
                key=f"{path}_su2_download",
            )
        except OSError as exc:
            st.warning(f"Unable to prepare download: {exc}")
        try:
            marker_map: dict[str, int] = {}
            with path.open() as handle:
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w",
                    delete=False,
                    suffix=".su2",
                )
                with temp_file as temp:
                    for line in handle:
                        if line.startswith("MARKER_TAG="):
                            tag = line.split("=", 1)[1].strip()
                            marker_map.setdefault(tag, len(marker_map) + 1)
                            line = f"MARKER_TAG= {marker_map[tag]}\n"
                        temp.write(line)
            mesh = pv.read(temp_file.name)
        except Exception as exc:
            st.error(f"Failed to read SU2 mesh: {exc}")
            return
        finally:
            if "temp_file" in locals():
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass

        surface = mesh.extract_surface()
        plotter = pv.Plotter()
        plotter.add_mesh(surface, color="lightgray", show_edges=True)
        plotter.reset_camera()
        stpyvista(plotter, key=f"{path}_su2_view")


def _display_dat(path: Path) -> None:
    with st.container(
        border=True,
    ):
        if st.checkbox(
            label=f"**{path.name}**",
            value=True,
        ):
            if path.name == "forces_breakdown.dat":
                _display_forces_breakdown(path)
                return None

            skip_first = False
            data = path.read_bytes()
            if _looks_binary(data):
                st.info(f"📄 {path.name} (binary file, cannot display as text)")
                return None
            text_data = data.decode("utf-8", errors="replace")
            first_line = text_data.splitlines()[:1]
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
            try:
                df = pd.read_csv(
                    path,
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
                        fig = px.line(
                            df,
                            x="x",
                            y="y",
                            title=path.stem,
                        )
                        fig.update_traces(mode="lines")
                        fig.update_layout(
                            xaxis_title="x",
                            yaxis_title="y",
                            yaxis_scaleanchor="x",
                            yaxis_scaleratio=1,
                        )
                        st.plotly_chart(fig, width="stretch")
                        return None

            except Exception as exc:
                st.warning(f"Could not parse {path.name} as DAT: {exc}")

            st.text_area(
                path.stem,
                text_data,
                height=200,
                key=f"{path}_dat_raw",
            )


def _display_forces_breakdown(path: Path) -> None:
    text = path.read_text(errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    rows = []
    current_section = "Total"
    for line in lines:
        if not line:
            continue
        if line.startswith("Surface name:"):
            current_section = line.replace("Surface name:", "").strip() or "Surface"
            continue
        if not line.startswith("Total "):
            continue
        if "|" not in line:
            continue
        left, right = line.split("|", 1)
        metric_part = left.strip()
        if ":" not in metric_part:
            continue
        metric_label, value_text = metric_part.split(":", 1)
        try:
            value = float(value_text.strip())
        except ValueError:
            continue

        pressure = None
        friction = None
        momentum = None
        for part in right.split("|"):
            part = part.strip()
            if part.startswith("Pressure"):
                try:
                    pressure = float(part.split(":", 1)[1].strip())
                except ValueError:
                    pressure = None
            elif part.startswith("Friction"):
                try:
                    friction = float(part.split(":", 1)[1].strip())
                except ValueError:
                    friction = None
            elif part.startswith("Momentum"):
                try:
                    momentum = float(part.split(":", 1)[1].strip())
                except ValueError:
                    momentum = None

        rows.append(
            {
                "Section": current_section,
                "Metric": metric_label.replace("Total ", "").strip(),
                "Total": value,
                "Pressure": pressure,
                "Friction": friction,
                "Momentum": momentum,
            }
        )

    if rows:
        st.table(pd.DataFrame(rows))
    else:
        st.text_area(path.stem, text, height=200, key=f"{path}_dat_raw")


def _display_vtu(path: Path) -> None:
    with st.container(border=True):
        if st.checkbox(
            label=f"**{path.name}**",
            value=True,
        ):
            try:
                st.download_button(
                    label="Download VTU file",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="application/octet-stream",
                    width="stretch",
                    key=f"{path}_vtu_download",
                )
            except OSError as exc:
                st.warning(f"Unable to prepare download: {exc}")

            try:
                mesh = pv.read(str(path))
            except Exception as exc:
                st.error(f"Failed to read VTU file: {exc}")
                return None

            surface = mesh.extract_surface()
            point_arrays = list(surface.point_data.keys())
            cell_arrays = list(surface.cell_data.keys())
            scalar_map: dict[str, str] = {name: "point" for name in point_arrays}
            for name in cell_arrays:
                scalar_map.setdefault(name, "cell")
            scalar_options = list(scalar_map.keys())

            workflow_root = None
            if path.name == "surface_flow.vtu":
                workflow_root = _find_workflow_root(path)
            geometry_mode = _get_geometry_mode(workflow_root) if workflow_root else None
            show_vtu_view = not (path.name == "surface_flow.vtu" and geometry_mode == "2D")

            plotter = pv.Plotter()
            if not scalar_options:
                if show_vtu_view:
                    plotter.add_mesh(surface, color="lightgray")
                    plotter.reset_camera()
                    stpyvista(plotter, key=f"{path}_vtu_geometry")
                st.caption("No scalar fields found in this VTU file.")
                return None

            preferred = ["Mach", "Pressure_Coefficient", "Pressure", "Cp"]
            default_scalar = None
            for pref in preferred:
                if pref in point_arrays:
                    default_scalar = f"{pref}"
                    break
                if pref in cell_arrays:
                    default_scalar = f"{pref}"
                    break

            if default_scalar is None:
                default_scalar = scalar_options[0]

            location = None
            scalar_choice = None
            if show_vtu_view:
                scalar_choice = st.selectbox(
                    "Field",
                    scalar_options,
                    index=scalar_options.index(default_scalar),
                    key=f"{path}_vtu_field",
                )
                location = scalar_map.get(scalar_choice, "point")

                plotter.add_mesh(surface, scalars=scalar_choice, show_scalar_bar=True)
                plotter.reset_camera()
                stpyvista(plotter, key=f"{path}_vtu_view_{scalar_choice}")

            _display_surface_flow_cp_xc(path, surface)

            if location == "point":
                data_array = surface.point_data.get(scalar_choice)
            else:
                data_array = surface.cell_data.get(scalar_choice)
            if data_array is not None and len(data_array) > 0:
                st.caption(
                    f"{scalar_choice} min/max: {float(data_array.min()):.6g} / "
                    f"{float(data_array.max()):.6g}"
                )


def _display_png(path: Path) -> None:
    if "figures_container" not in st.session_state:
        st.session_state["figures_container"] = st.container()
        st.session_state.figures_container.markdown("**Figures**")

    st.session_state.figures_container.markdown(f"{path.stem.replace('_', ' ')}")
    st.session_state.figures_container.image(str(path))


def _display_pdf(path: Path) -> None:
    with st.container(border=True):
        show_pdf = st.checkbox(
            f"**{path.stem}**",
            value=True,
            key=f"{path}_dir_toggle",
        )
        if show_pdf:
            if "pdf_container" not in st.session_state:
                st.session_state["pdf_container"] = st.container()

            pdf_bytes = path.read_bytes()
            b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
            st.session_state.pdf_container.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_pdf}" '
                'width="100%" height="900" style="border:0"></iframe>',
                unsafe_allow_html=True,
            )
            st.session_state.pdf_container.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=path.name,
                mime="application/pdf",
                key=f"{path}_pdf_download",
            )


def _display_json(path: Path) -> None:
    data = path.read_bytes()
    if _looks_binary(data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None
    text_data = data.decode("utf-8", errors="replace")
    st.text_area(
        path.stem,
        text_data,
        height=200,
        key=f"{path}_json",
    )


def _display_csv(path: Path) -> None:
    if path.name == "history.csv":
        with st.container(
            border=True,
        ):
            if st.checkbox(
                label="**Convergence**",
                value=True,
            ):
                try:
                    df = pd.read_csv(path)
                    df.rename(columns=lambda x: x.strip().strip('"'), inplace=True)

                    coef_cols = [col for col in ["CD", "CL", "CMy"] if col in df.columns]
                    if coef_cols:
                        st.line_chart(df[coef_cols])

                    rms_cols = [
                        col
                        for col in ["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoW]", "rms[RhoE]"]
                        if col in df.columns
                    ]
                    if rms_cols:
                        st.line_chart(df[rms_cols])

                except Exception as exc:
                    st.warning(f"Could not parse {path.name} as CSV: {exc}")
                    data = path.read_bytes()
                    if _looks_binary(data):
                        st.info(f"📄 {path.name} (binary file, cannot display as text)")
                        return None
                    text_data = data.decode("utf-8", errors="replace")
                    st.text_area(path.stem, text_data, height=200, key=f"{path}_csv_raw")
    else:
        st.markdown(f"**{path.name}**")
        try:
            df = pd.read_csv(path, engine="python", on_bad_lines="skip")
            st.dataframe(df)
        except Exception as exc:
            st.warning(f"Could not parse {path.name} as CSV: {exc}")
            data = path.read_bytes()
            if _looks_binary(data):
                st.info(f"📄 {path.name} (binary file, cannot display as text)")
                return None
            text_data = data.decode("utf-8", errors="replace")
            st.text_area(path.stem, text_data, height=200, key=f"{path}_csv_raw")


def _display_xml(path: Path) -> None:
    with st.container(border=True):
        cpacs = CPACS(path)
        st.markdown(f"""**CPACS {cpacs.ac_name}**""")
        section_3D_view(
            cpacs=cpacs,
            force_regenerate=True,
        )


def _results_sort_key(path: Path) -> tuple[int, str]:
    '''Priority to files, priority=0 is highest priority.'''
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        priority = 0
    elif suffix == ".txt":
        priority = 2
    else:
        priority = 1
    return priority, path.name


def _get_workflow_dirs(current_wkdir: Path) -> list[Path]:
    if not current_wkdir.exists():
        return []
    workflow_dirs = [
        wkflow
        for wkflow in current_wkdir.iterdir()
        if wkflow.is_dir() and wkflow.name.startswith("Workflow_")
    ]
    return sorted(workflow_dirs, key=workflow_number)


def _get_workflow_module_order(workflow_dir: Path) -> list[str]:
    module_dirs = []
    for module_dir in workflow_dir.iterdir():
        if not module_dir.is_dir():
            continue
        parts = module_dir.name.split("_", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        module_dirs.append((int(parts[0]), parts[1]))
    return [name for _, name in sorted(module_dirs, key=lambda item: item[0])]


def _display_surface_flow_cp_xc(path: Path, surface: pv.PolyData) -> None:
    if path.name != "surface_flow.vtu":
        return None

    workflow_root = _find_workflow_root(path)
    if workflow_root is None:
        return

    geometry_mode = _get_geometry_mode(workflow_root)
    if geometry_mode != "2D":
        return

    cp_field, location = _find_cp_field(surface)
    if cp_field is None:
        st.info("No pressure coefficient field found to plot Cp vs x/c.")
        return

    coords, cp_values = _get_scalar_with_coords(surface, cp_field, location)
    if coords is None or cp_values is None or len(cp_values) == 0:
        return

    x_axis = 0
    axis_ranges = np.ptp(coords, axis=0)
    if axis_ranges[1] >= axis_ranges[2]:
        y_axis = 1
    else:
        y_axis = 2

    x_vals = coords[:, x_axis]
    y_vals = coords[:, y_axis]
    x_min = float(np.min(x_vals))
    x_max = float(np.max(x_vals))
    chord = x_max - x_min
    if chord <= 0:
        return

    x_over_c = (x_vals - x_min) / chord

    df = pd.DataFrame(
        {
            "x_over_c": x_over_c,
            "y_coord": y_vals,
            "cp": cp_values,
        }
    )
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    if df.empty:
        return

    bins = np.linspace(0.0, 1.0, 81)
    df["bin"] = np.digitize(df["x_over_c"], bins, right=True)
    y_mid = df.groupby("bin")["y_coord"].mean()
    df["y_mid"] = df["bin"].map(y_mid)
    df["surface"] = np.where(df["y_coord"] >= df["y_mid"], "Upper", "Lower")

    grouped = (
        df.groupby(["surface", "bin"], as_index=False)
        .agg(
            x_over_c=("x_over_c", "mean"),
            cp=("cp", "mean"),
        )
        .sort_values(["surface", "x_over_c"])
    )
    if grouped.empty:
        return

    fig = px.line(
        grouped,
        x="x_over_c",
        y="cp",
        color="surface",
        markers=True,
        title="Pressure Coefficient vs x/c",
    )
    fig.update_layout(
        xaxis_title="x/c",
        yaxis_title="Cp",
        legend_title_text="Surface",
    )
    st.plotly_chart(fig, width="stretch")


def _find_cp_field(surface: pv.PolyData) -> tuple[str | None, str | None]:
    candidates = ["Pressure_Coefficient", "Cp", "C_p", "cp"]
    for name in candidates:
        if name in surface.point_data:
            return name, "point"
        if name in surface.cell_data:
            return name, "cell"
    return None, None


def _get_scalar_with_coords(
    surface: pv.PolyData, scalar_name: str, location: str
) -> tuple[np.ndarray | None, np.ndarray | None]:
    if location == "point":
        return surface.points, surface.point_data.get(scalar_name)
    if location == "cell":
        return surface.cell_centers().points, surface.cell_data.get(scalar_name)
    return None, None


def _find_workflow_root(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.name.startswith("Workflow_"):
            return parent
    return None


@lru_cache(maxsize=8)
def _get_geometry_mode(workflow_root: Path) -> str | None:
    cpacs_path = workflow_root / "00_ToolInput.xml"
    if not cpacs_path.exists():
        return None
    try:
        cpacs = CPACS(cpacs_path)
        tixi = cpacs.tixi
        if tixi.checkElement(GEOMETRY_MODE_XPATH):
            return tixi.getTextElement(GEOMETRY_MODE_XPATH)
    except Exception as exc:
        log.warning(f"Could not read geometry mode from {cpacs_path}: {exc}")
    return None


# Main
if __name__ == "__main__":

    # Define interface
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

    st.markdown("---")

    show_results()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
