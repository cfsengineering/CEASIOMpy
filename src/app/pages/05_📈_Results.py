"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy

| Author : Aidan Jungo
| Creation: 2022-09-16
| Modified : Leon Deligny
| Date: 10-Mar-2025

"""

# Imports
import os
import base64

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from ceasiompy.utils.commonpaths import get_wkdir
from parsefunctions import display_avl_table_file
from streamlitutils import (
    create_sidebar,
    section_3D_view,
    highlight_stability,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from constants import BLOCK_CONTAINER
from ceasiompy.PyAVL import AVL_TABLE_FILES
from ceasiompy.utils.commonpaths import DEFAULT_PARAVIEW_STATE


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

# =================================================================================================
#    FUNCTIONS
# =================================================================================================

# Global counter for unique keys
if 'text_area_counter' not in st.session_state:
    st.session_state.text_area_counter = 0


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
        # Use counter to create unique key for each widget
        st.session_state.text_area_counter += 1
        unique_key = f"text_area_{st.session_state.text_area_counter}_{path.name}"
        try:
            content = path.read_text()
            st.text_area(path.stem, content, height=200, key=unique_key)
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
                with st.container(border=True):
                    st.markdown(f"**{child.name}**")
                    try:
                        import pyvista as pv
                        from stpyvista import stpyvista
                    except ImportError:
                        st.info("pyvista/stpyvista is not available; cannot render VTU files.")
                        continue

                    try:
                        mesh = pv.read(str(child))
                    except Exception as exc:
                        st.error(f"Failed to read VTU file: {exc}")
                        continue

                    surface = mesh.extract_surface()
                    point_arrays = list(surface.point_data.keys())
                    cell_arrays = list(surface.cell_data.keys())
                    scalar_options = [f"point:{name}" for name in point_arrays] + [
                        f"cell:{name}" for name in cell_arrays
                    ]

                    plotter = pv.Plotter()
                    if not scalar_options:
                        plotter.add_mesh(surface, color="lightgray")
                        stpyvista(plotter, key=f"{child}_vtu_geometry")
                        st.caption("No scalar fields found in this VTU file.")
                        continue

                    preferred = ["Mach", "Pressure_Coefficient", "Pressure", "Cp"]
                    default_scalar = None
                    for pref in preferred:
                        if pref in point_arrays:
                            default_scalar = f"point:{pref}"
                            break
                        if pref in cell_arrays:
                            default_scalar = f"cell:{pref}"
                            break
                    if default_scalar is None:
                        default_scalar = scalar_options[0]

                    scalar_choice = st.selectbox(
                        "Field",
                        scalar_options,
                        index=scalar_options.index(default_scalar),
                        key=f"{child}_vtu_field",
                    )
                    _, scalar = scalar_choice.split(":", 1)
                    plotter.add_mesh(surface, scalars=scalar, show_scalar_bar=True)
                    stpyvista(plotter, key=f"{child}_vtu_view")

                    data_array = surface.point_data.get(scalar)
                    if data_array is None:
                        data_array = surface.cell_data.get(scalar)
                    if data_array is not None and len(data_array) > 0:
                        st.caption(
                            f"{scalar} min/max: {float(data_array.min()):.6g} / "
                            f"{float(data_array.max()):.6g}"
                        )


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

                        pdf_bytes = child.read_bytes()
                        b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
                        st.session_state.pdf_container.markdown(
                            f'<iframe src="data:application/pdf;base64,{b64_pdf}" '
                            'width="100%" height="900" style="border:0"></iframe>',
                            unsafe_allow_html=True,
                        )
                        st.session_state.pdf_container.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name=child.name,
                            mime="application/pdf",
                            key=f"{child}_pdf_download",
                        )

            elif child.suffix == ".md":
                with st.container(border=True):
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

            elif child.suffix == ".csv":
                st.markdown(f"**{child.name}**")
                st.dataframe(pd.read_csv(child))

            elif child.suffix == ".xml":
                with st.container(border=True):
                    cpacs = CPACS(child)
                    st.markdown(f"""**CPACS {cpacs.ac_name}**""")
                    section_3D_view(
                        cpacs=cpacs,
                        force_regenerate=True,
                    )
            elif child.is_dir():
                with st.container(border=True):
                    show_dir = st.checkbox(
                        f"**{child.stem}**",
                        value=True,
                        key=f"{child}_dir_toggle",
                    )
                    if show_dir:
                        display_results(child)

    except BaseException:
        display_results_else(results_dir)


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


def get_workflow_module_order(workflow_dir: Path) -> list[str]:
    module_dirs = []
    for module_dir in workflow_dir.iterdir():
        if not module_dir.is_dir():
            continue
        parts = module_dir.name.split("_", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        module_dirs.append((int(parts[0]), parts[1]))
    return [name for _, name in sorted(module_dirs, key=lambda item: item[0])]


def show_results():
    """Display the results of the selected workflow."""

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
    results_dirs = [dir for dir in results_dir.iterdir() if dir.is_dir()]
    results_names = [dir.stem for dir in results_dirs]
    workflow_module_order = get_workflow_module_order(chosen_workflow)
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
