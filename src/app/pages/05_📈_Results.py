"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy
"""

# Imports
import os
import base64
import pandas as pd
import pyvista as pv
import streamlit as st
import matplotlib.pyplot as plt

from stpyvista import stpyvista
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
from ceasiompy.PyAVL import AVL_TABLE_FILES


# Constants

HOW_TO_TEXT = (
    "### How to check your results\n"
    "1. Check the results for your workflow\n"
)

PAGE_NAME = "Results"
IGNORED_RESULT_FILES: set[str] = {
    "avl_commands.txt",
    "logfile_avl.log",
}


# Functions

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
        try:
            content = path.read_text()
            st.text_area(path.stem, content, height=200)
        except UnicodeDecodeError:
            # File is binary, show message instead
            st.info(f"📄 {path.name} (binary file, cannot display as text)")


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

        for child in sorted(Path(results_dir).iterdir(), key=_results_sort_key):
            if child.name in IGNORED_RESULT_FILES:
                continue

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
                with st.container(border=True):
                    md_text = child.read_text()
                    html = highlight_stability(md_text)
                    st.markdown(html, unsafe_allow_html=True)

            elif child.suffix == ".json":
                _display_json(child)

            elif child.suffix == ".log" or child.suffix == ".txt":
                if child.name in AVL_TABLE_FILES:
                    display_avl_table_file(child)
                    continue
                if "logs_container" not in st.session_state:
                    st.session_state["logs_container"] = st.container()
                    st.session_state.logs_container.markdown("**Logs**")
                log_text = child.read_text()
                if child.name == "logfile_SU2_CFD.log":
                    format_tables = st.session_state.logs_container.checkbox(
                        "Format tables",
                        value=True,
                        key=f"{child}_format_tables",
                    )
                    if format_tables:
                        segments = parse_ascii_tables(log_text)
                        for kind, payload in segments:
                            if kind == "text":
                                if payload.strip():
                                    st.session_state.logs_container.code(payload)
                            else:
                                rows = payload
                                if len(rows) > 1 and len(rows[0]) == len(rows[1]):
                                    df = pd.DataFrame(rows[1:], columns=rows[0])
                                else:
                                    df = pd.DataFrame(rows)
                                st.session_state.logs_container.table(df)
                    else:
                        st.session_state.logs_container.text_area(
                            child.stem, log_text, height=200
                        )
                else:
                    st.session_state.logs_container.text_area(
                        child.stem,
                        log_text,
                        height=200,
                        key=f"{child}_log_text",
                    )

            elif child.suffix == ".csv":
                _display_csv(child)

            elif child.suffix == ".xml":
                _display_xml(child)

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
        log.warning(f"Could not display... {e=}")
        display_results_else(results_dir)


# Methods

def _display_su2(path: Path) -> None:
    """Display SU2 mesh in Streamlit using PyVista."""
    with st.container(border=True):
        st.markdown(f"**{path.name}**")
        try:
            mesh = pv.read(str(path))
        except Exception as exc:
            st.error(f"Failed to read SU2 mesh: {exc}")
            return

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

            skip_first = False
            first_line = path.read_text().splitlines()[:1]
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
                    fig, ax = plt.subplots()
                    ax.plot(df["x"].to_numpy(), df["y"].to_numpy())
                    ax.set_aspect("equal", adjustable="box")
                    ax.set_title(path.stem)
                    ax.set_xlabel("x")
                    ax.set_ylabel("y")
                    st.pyplot(fig)
                    return None

            st.text_area(path.stem, path.read_text(), height=200)


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

            plotter = pv.Plotter()
            if not scalar_options:
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
    st.text_area(path.stem, path.read_text(), height=200)


def _display_csv(path: Path) -> None:
    if path.name == "history.csv":
        st.markdown("**Convergence**")

        df = pd.read_csv(path)
        df.rename(columns=lambda x: x.strip().strip('"'), inplace=True)

        st.line_chart(df[["CD", "CL", "CMy"]])
        st.line_chart(df[["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoW]", "rms[RhoE]"]])
    else:
        st.markdown(f"**{path.name}**")
        st.dataframe(pd.read_csv(path))


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
