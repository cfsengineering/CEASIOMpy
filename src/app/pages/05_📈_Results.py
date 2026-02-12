"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy
"""

# Imports
import os
import json
import base64
import shutil
import joblib
import hashlib
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
from ceasiompy.smtrain.func.utils import domain_converter
from ceasiompy.smtrain.func.config import update_geometry_cpacs
from ceasiompy.utils.ceasiompyutils import workflow_number
from ceasiompy.utils.geometryfunctions import get_xpath_for_param
from parsefunctions import (
    parse_ascii_tables,
    display_avl_table_file,
    display_forces_breakdown,
)
from streamlitutils import (
    create_sidebar,
    section_3D_view,
    highlight_stability,
)

from pathlib import Path
from SALib.analyze import sobol
from smt.applications import MFK
from cpacspy.cpacspy import CPACS
from SALib.sample import saltelli
from scipy.optimize import Bounds
from smt.surrogate_models import (
    KRG,
    RBF,
)

from ceasiompy import log
from constants import BLOCK_CONTAINER
from ceasiompy.pyavl import AVL_TABLE_FILES
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.smtrain import (
    AEROMAP_FEATURES,
    NORMALIZED_DOMAIN,
)


# Constants

HOW_TO_TEXT = (
    "### Results \n"
    "1. Check each module's outputs"
)

PAGE_NAME = "Results"
NO_DISPLAY_DIR: set[str] = {
    # pyavl
    "Airfoil_files",

    # smtrain
    "computations",
    "generated_cpacs",

}
IGNORED_RESULTS: set[str] = {
    # pyavl
    "avl_commands.txt",
    "logfile_avl.log",

    # su2run
    "restart_flow.dat",
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


@lru_cache(maxsize=8)
def _build_workflow_zip(workflow_path: str, workflow_mtime_ns: int) -> bytes:
    _ = workflow_mtime_ns  # cache invalidation key
    workflow_dir = Path(workflow_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_base = Path(tmp_dir, workflow_dir.name)
        archive_path = shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=workflow_dir.parent,
            base_dir=workflow_dir.name,
        )
        return Path(archive_path).read_bytes()


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

    left_col, right_col = st.columns(
        spec=[2, 1],
        vertical_alignment="bottom",
    )
    with left_col:
        chosen_workflow_name = st.selectbox(
            label="Choose workflow",
            options=workflow_names,
            index=default_index,
            key="results_chosen_workflow",
        )
        chosen_workflow = Path(current_wkdir, chosen_workflow_name)

    with right_col:
        try:
            workflow_zip = _build_workflow_zip(
                str(chosen_workflow),
                chosen_workflow.stat().st_mtime_ns,
            )
            st.download_button(
                label=f"Download {chosen_workflow_name}",
                data=workflow_zip,
                file_name=f"{chosen_workflow_name}.zip",
                mime="application/zip",
                width="stretch",
                key=f"{chosen_workflow}_download",
            )
        except OSError as exc:
            st.warning(f"Unable to prepare workflow download: {exc}")

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

    # Inner constant...
    DISPLAY_BY_SUFFIX = {
        ".dat": _display_dat,
        ".su2": _display_su2,
        ".vtu": _display_vtu,
        ".pkl": _display_pkl,
        ".png": _display_png,
        ".pdf": _display_pdf,
        ".md": _display_md,
        ".json": _display_json,
        ".txt": _display_txt,
        ".log": _display_log,
        ".csv": _display_csv,
        ".xml": _display_xml,
        ".html": _display_html,
        ".json": _display_json,
    }

    for child in sorted(Path(results_dir).iterdir(), key=_results_sort_key):
        if child.name in IGNORED_RESULTS:
            continue
        try:
            handler = DISPLAY_BY_SUFFIX.get(child.suffix.lower())
            if handler is not None:
                handler(child)
            elif child.is_dir():
                _display_dir(child)

        except BaseException as e:
            log.warning(f"Could not display {child}: {e=}")
            display_results_else(child)


# Methods

def _display_json(path: Path) -> None:
    with st.container(border=True):
        show_json = st.checkbox(
            f"**{path.name}**",
            value=True,
            key=f"{path}_json_toggle",
        )
        if not show_json:
            return None

        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
            return None

        text_data = data.decode("utf-8", errors="replace")

        try:
            parsed = json.loads(text_data)
        except json.JSONDecodeError as exc:
            st.warning(f"Invalid JSON in {path.name}: {exc}")
            st.text_area(path.stem, text_data, height=260, key=f"{path}_json_raw_invalid")
            return None

        left_col, right_col = st.columns([3, 1])
        with left_col:
            query = st.text_input(
                "Search key/value",
                value="",
                key=f"{path}_json_search",
                placeholder="e.g. mach, aoa, result",
                label_visibility="collapsed",
            ).strip()
        with right_col:
            expanded = st.toggle(
                "Expand tree",
                value=False,
                key=f"{path}_json_expand",
            )

        def _iter_pairs(obj, prefix=""):
            if isinstance(obj, dict):
                for key, val in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else str(key)
                    yield from _iter_pairs(val, new_prefix)
            elif isinstance(obj, list):
                for idx, val in enumerate(obj):
                    new_prefix = f"{prefix}[{idx}]"
                    yield from _iter_pairs(val, new_prefix)
            else:
                yield prefix or "$", obj

        if query:
            query_lower = query.lower()
            matches = []
            for jpath, value in _iter_pairs(parsed):
                if (query_lower in jpath.lower()) or (query_lower in str(value).lower()):
                    matches.append({"path": jpath, "value": value})
            st.caption(f"{len(matches)} match(es) for '{query}'")
            if matches:
                st.dataframe(pd.DataFrame(matches), width="stretch", hide_index=True)
            else:
                st.info("No matches found.")

        tab_flat, tab_tree, tab_raw = st.tabs(["Flat", "Tree", "Raw"])
        with tab_tree:
            st.json(parsed, expanded=expanded)
        with tab_flat:
            flat_rows = [{"path": jpath, "value": value} for jpath, value in _iter_pairs(parsed)]
            st.dataframe(pd.DataFrame(flat_rows), width="stretch", hide_index=True)
        with tab_raw:
            st.text_area("Raw JSON", text_data, height=260, key=f"{path}_json_raw")
            st.download_button(
                "Download JSON",
                data=text_data,
                file_name=path.name,
                mime="application/json",
                key=f"{path}_json_download",
                width="stretch",
            )


def _display_dir(path: Path) -> None:
    with st.container(border=True):
        show_dir = st.checkbox(
            f"**{path.stem}**",
            value=False,
            key=f"{path}_dir_toggle",
        )
        if show_dir:
            display_results(path)


def _display_pkl(path: Path) -> None:
    with st.container(border=True):
        show_model = st.checkbox(
            label=f"**{path.name}**",
            value=True,
            key=f"{path}_plk_toggle",
        )
        if not show_model:
            return None

        try:
            data = _load_plk_cached(str(path), path.stat().st_mtime)
        except Exception as exc:
            st.error(f"Could not load model from {path.name}: {exc!r}")
            return None

        if not isinstance(data, dict):
            st.error(f"Can not retrieve model info from {data=}")
            return None

        model = data.get("model")
        if not isinstance(model, (KRG, RBF, MFK)):
            st.error(f"Modeltype {model=} is uncorrect.")
            return None

        columns = data.get("columns")
        objective = data.get("objective")

        geom_bounds = data.get("geom_bounds")
        aero_bounds = data.get("aero_bounds")

        if columns and objective in columns:
            columns = [
                col
                for col in columns
                if col != objective
            ]

        if not columns:
            st.info("No parameter metadata found in the model file.")
            return None

        bounds = {}
        bounds_source = {}
        try:
            for idx, name in enumerate(geom_bounds.param_names):
                bounds[name] = (
                    float(geom_bounds.bounds.lb[idx]),
                    float(geom_bounds.bounds.ub[idx]),
                )
                bounds_source[name] = "geom"
        except Exception as e:
            st.error(f"Could not extract geometric bounds from model {e=}")
            return None

        try:
            for idx, name in enumerate(AEROMAP_FEATURES):
                bounds.setdefault(
                    name,
                    (float(aero_bounds.lb[idx]), float(aero_bounds.ub[idx])),
                )
                bounds_source.setdefault(name, "aero")
        except Exception as e:
            st.error(f"Could not extract aerodynamic bounds from model {e=}")
            return None

        st.markdown("**Model Inputs**")

        geom_inputs = [col for col in columns if bounds_source.get(col) == "geom"]
        aero_inputs = [col for col in columns if bounds_source.get(col) == "aero"]
        other_inputs = [
            col for col in columns if col not in geom_inputs and col not in aero_inputs
        ]

        input_values: dict[str, float] = {}

        def _input_widget(col: str, *, key_prefix: str = "", label: str | None = None) -> None:
            display_label = label or col
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            if hi == lo:
                val = st.number_input(
                    display_label,
                    value=float(lo),
                    key=f"{path}_plk_{key_prefix}{col}",
                    disabled=True,
                )
            else:
                step = (hi - lo) / 100.0
                val = st.slider(
                    display_label,
                    min_value=float(lo),
                    max_value=float(hi),
                    value=float((lo + hi) / 2.0),
                    step=float(step),
                    key=f"{path}_plk_{key_prefix}{col}",
                )
            input_values[col] = float(val)

        if geom_inputs:
            st.markdown("**Geometry Inputs**")
            for col in geom_inputs:
                _input_widget(col, key_prefix="geom_")

        if aero_inputs:
            st.markdown("**Aero Inputs**")
            aero_cols = st.columns(2)
            aero_labels = {
                "altitude": "Altitude",
                "machNumber": "Mach",
                "angleOfAttack": "α°",
                "angleOfSideslip": "β°",
            }
            for idx, col in enumerate(aero_inputs):
                with aero_cols[idx % 2]:
                    _input_widget(
                        col,
                        key_prefix="aero_",
                        label=aero_labels.get(col, col),
                    )

        if other_inputs:
            st.markdown("**Other Inputs**")
            for col in other_inputs:
                _input_widget(col, key_prefix="other_")

        st.markdown("**Geometry**")
        preview_cpacs = None
        try:
            workflow_root = _find_workflow_root(path)
            if workflow_root is not None:
                cpacs_in = workflow_root / "00_ToolInput.xml"
                if cpacs_in.exists():
                    base_cpacs = CPACS(cpacs_in)
                    params_to_update: dict[str, dict[str, list[float | str]]] = {}
                    for full_name in geom_inputs:
                        if full_name not in input_values or "_of_" not in full_name:
                            continue

                        parts = full_name.split("_of_")
                        if len(parts) != 3:
                            continue

                        param_name, section_uid, wing_uid = parts
                        xpath = get_xpath_for_param(
                            tixi=base_cpacs.tixi,
                            param=param_name,
                            wing_uid=wing_uid,
                            section_uid=section_uid,
                        )

                        if param_name not in params_to_update:
                            params_to_update[param_name] = {"values": [], "xpath": []}
                        params_to_update[param_name]["values"].append(
                            object=float(input_values[full_name])
                        )
                        params_to_update[param_name]["xpath"].append(xpath)

                    if params_to_update:
                        with tempfile.NamedTemporaryFile(
                            prefix="ceasiompy_smtrain_preview_",
                            suffix=".xml",
                            delete=False,
                        ) as tmp_file:
                            preview_cpacs_path = Path(tmp_file.name)

                        preview_cpacs = update_geometry_cpacs(
                            cpacs_path_in=cpacs_in,
                            cpacs_path_out=preview_cpacs_path,
                            geom_params=params_to_update,
                        )
                    else:
                        preview_cpacs = base_cpacs
        except Exception as exc:
            st.warning(f"Could not generate preview CPACS from geometry inputs: {exc!r}")

        if preview_cpacs is not None:
            section_3D_view(cpacs=preview_cpacs, force_regenerate=True)
        else:
            section_3D_view(force_regenerate=True)

        normalized_values = []
        for col in columns:
            val = input_values.get(col, 0.0)
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            if bounds_source.get(col) in {"geom", "aero"}:
                normalized_values.append(
                    float(domain_converter(float(val), (lo, hi), NORMALIZED_DOMAIN))
                )
            else:
                normalized_values.append(float(val))

        x = np.asarray(normalized_values, dtype=float).reshape(1, -1)

        prediction = None
        try:
            prediction = model.predict_values(x)
        except Exception as exc:
            st.error(f"Model prediction failed: {exc!r}")
            return None

        if prediction is None:
            st.info("Model does not support prediction.")
            return None

        pred_val = float(np.asarray(prediction).ravel()[0])
        label = f"Predicted {objective}" if objective else "Predicted value"
        st.metric(label=label, value=f"{pred_val:.6g}")

        st.markdown("---")
        _compute_sobol_analysis(
            model=model,
            bounds=bounds,
            columns=columns,
            bounds_source=bounds_source,
        )


def _compute_sobol_analysis(
    model: RBF | KRG | MFK,
    bounds: Bounds,
    columns: list[str],
    bounds_source: dict,
) -> None:
    sobol_params = []
    sobol_bounds = []
    for col in columns:
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        if hi == lo:
            continue
        sobol_params.append(col)
        sobol_bounds.append([float(lo), float(hi)])

    if not sobol_params:
        st.info("No variable inputs available for Sobol analysis.")
        return None

    problem = {
        "num_vars": len(sobol_params),
        "names": sobol_params,
        "bounds": sobol_bounds,
    }

    n_base = 256
    sample_set = saltelli.sample(problem, n_base, calc_second_order=False)

    mids = {}
    for col in columns:
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        mids[col] = (float(lo) + float(hi)) / 2.0

    x_rows = np.zeros((sample_set.shape[0], len(columns)), dtype=float)
    for idx, col in enumerate(columns):
        if col in sobol_params:
            values = sample_set[:, sobol_params.index(col)]
        else:
            values = np.full(sample_set.shape[0], mids[col], dtype=float)
        if bounds_source.get(col) in {"geom", "aero"}:
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            values = np.array(
                [domain_converter(v, (lo, hi), NORMALIZED_DOMAIN) for v in values],
                dtype=float,
            )
        x_rows[:, idx] = values

    try:
        y_pred = model.predict_values(x_rows).ravel()
    except Exception as exc:
        st.error(f"Sobol prediction failed: {exc!r}")
        return None

    try:
        si = sobol.analyze(problem, y_pred, calc_second_order=False)
    except Exception as exc:
        st.error(f"Sobol analysis failed: {exc!r}")
        return None

    df_sobol = pd.DataFrame(
        {
            "Parameter": sobol_params,
            "S1": si.get("S1", []),
            "ST": si.get("ST", []),
        }
    )
    df_long = df_sobol.melt(
        id_vars="Parameter",
        value_vars=["S1", "ST"],
        var_name="Index",
        value_name="Value",
    )
    fig = px.bar(
        df_long,
        x="Parameter",
        y="Value",
        color="Index",
        barmode="group",
        title="Sobol Indices",
    )
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": True, "scrollZoom": True},
    )


@lru_cache(maxsize=8)
def _load_plk_cached(path_str: str, mtime: float):
    return joblib.load(path_str)


def _display_html(path: Path) -> None:
    st.markdown("---")
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
                display_forces_breakdown(path)
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


def _display_vtu(path: Path) -> None:
    with st.container(border=True):
        if st.checkbox(
            label=f"**{path.name}**",
            value=True,
        ):
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


def _display_png(path: Path) -> None:
    if "figures_container" not in st.session_state:
        st.session_state["figures_container"] = st.container()
        st.session_state.figures_container.markdown("**Figures**")

    st.session_state.figures_container.markdown(f"{path.stem.replace('_', ' ')}")
    st.session_state.figures_container.image(str(path))


def _display_pdf(path: Path) -> None:
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
        width="stretch",
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
            hidden_cols = [
                col
                for col in df.columns
                if col in {"comment", "color", "Color"} or col.startswith("Unnamed:")
            ]
            if hidden_cols:
                df = df.drop(columns=hidden_cols)
            df_display = df.copy()
            for col in df_display.columns:
                numeric_series = pd.to_numeric(df_display[col], errors="coerce")
                if numeric_series.notna().any():
                    df_display[col] = numeric_series.map(
                        lambda x: "" if pd.isna(x) else np.format_float_positional(x, trim="-")
                    )

            stab_cols = {"long_stab", "dir_stab", "lat_stab"}
            if stab_cols.issubset(set(df.columns)):
                stable_mask = (
                    (df["long_stab"] == "Stable")
                    & (df["dir_stab"] == "Stable")
                    & (df["lat_stab"] == "Stable")
                )

                def _row_style(row):
                    is_stable_row = bool(stable_mask.loc[row.name])
                    if is_stable_row:
                        return [
                            "background-color: #d4edda; "
                            "color: #155724; font-weight: 600;"
                        ] * len(row)
                    return [
                        "background-color: #f8d7da; "
                        "color: #721c24; font-weight: 600;"
                    ] * len(row)

                numeric_cols = [
                    col for col in df.columns
                    if pd.to_numeric(df[col], errors="coerce").notna().any()
                ]

                def _format_scientific_if_needed(value):
                    if pd.isna(value):
                        return ""
                    val = float(value)
                    fixed = f"{val:.12f}".rstrip("0").rstrip(".")
                    if "." in fixed and len(fixed.split(".", 1)[1]) > 4:
                        return f"{val:.3e}"
                    return fixed

                style_formatter = {
                    col: _format_scientific_if_needed
                    for col in numeric_cols
                }

                df_signature = hashlib.md5(
                    (",".join(map(str, df_display.columns)) + f"|{df_display.shape}").encode()
                ).hexdigest()

                displayed_df = (
                    df_display.style
                    .apply(_row_style, axis=1)
                    .format(style_formatter)
                )
                st.dataframe(
                    data=displayed_df,
                    hide_index=True,
                    key=f"results_df_{df_signature}",
                )
            else:
                st.dataframe(
                    data=df_display,
                    hide_index=True,
                )
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
        st.markdown(f"**CPACS {cpacs.ac_name}**")

        # Display the 3D geometry of the CPACS file
        section_3D_view(
            cpacs=cpacs,
            force_regenerate=True,
        )

        # Download button for downloading CPACS file locally
        st.download_button(
            label="Download CPACS file",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/xml",
            width="stretch",
        )


def _results_sort_key(path: Path) -> tuple[int, str]:
    """Priority to files, priority=0 is highest priority."""
    if path.is_dir():
        return 99, path.name  # directories last

    suffix = path.suffix.lower()
    if suffix in {".pdf", ".md"}:
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
