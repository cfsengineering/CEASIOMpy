"""
CEASIOMpy: Conceptual Aircraft Design Software

Entry point for the Streamlit UI with explicit page ordering.
"""

# Imports

import os
import json
import streamlit as st

from ceasiompy.utils import get_wkdir
from openvspgui import convert_vsp3_to_cpacs
from ceasiompy.utils.guiobjects import add_value

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# Methods
def _resolve_geometry_path(raw_path: str) -> Path:
    geometry_path = Path(raw_path).expanduser()
    if not geometry_path.is_absolute():
        geometry_path = (Path.cwd() / geometry_path).resolve()
    return geometry_path


def _parse_cli_modules() -> list[str] | None:
    raw_modules = os.environ.get("CEASIOMPY_MODULES")
    if raw_modules is None:
        return None

    raw_modules = raw_modules.strip()
    if not raw_modules:
        return []

    try:
        parsed = json.loads(raw_modules)
        modules = [m.strip() for m in parsed if isinstance(m, str) and m.strip()]
    except json.JSONDecodeError:
        modules = [m.strip() for m in raw_modules.split() if m.strip()]

    return modules


def _load_cli_geometry(geometry_path: Path, wkdir: Path) -> None:
    suffix = geometry_path.suffix.lower()

    if suffix == ".xml":
        cpacs_path = geometry_path
        geometry_mode = "3D"
    elif suffix in {".vsp", ".vsp3"}:
        cpacs_path = convert_vsp3_to_cpacs(geometry_path, output_dir=wkdir)
        geometry_mode = "3D"
    else:
        raise ValueError(f"Unsupported geometry file format: {geometry_path.suffix}")

    cpacs = CPACS(str(cpacs_path))
    add_value(
        tixi=cpacs.tixi,
        xpath=GEOMETRY_MODE_XPATH,
        value=geometry_mode,
    )
    st.session_state["cpacs"] = cpacs
    st.session_state["last_converted_cpacs_path"] = str(cpacs_path)


def _preload_cli_state() -> str:
    """Preload CLI state before navigation and return the default page key."""

    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir

    if not st.session_state.get("_app_cli_preloaded"):
        st.session_state["_app_cli_preloaded"] = True

        raw_geometry = os.environ.get("CEASIOMPY_GEOMETRY", "").strip()
        if raw_geometry:
            geometry_path = _resolve_geometry_path(raw_geometry)
            if not geometry_path.exists():
                st.warning(f"CLI geometry path does not exist: {geometry_path}")
            else:
                try:
                    _load_cli_geometry(geometry_path, wkdir)
                except Exception as exc:
                    st.warning(f"Could not preload CLI geometry '{geometry_path.name}': {exc}")

        modules = _parse_cli_modules()
        if modules is not None:
            st.session_state.workflow_modules = modules
            st.session_state.pop("workflow_flow_state", None)
            st.session_state.pop("workflow_flow_modules", None)

    has_cli_geometry = isinstance(st.session_state.get("cpacs"), CPACS)
    has_cli_modules = os.environ.get("CEASIOMPY_MODULES") is not None

    if has_cli_modules:
        return "settings"
    if has_cli_geometry:
        return "workflow"
    return "geometry"


# Main
def main() -> None:
    """Reorder files pages correctly."""
    default_page = _preload_cli_state()

    page_home = st.Page(
        "pages/00_🏠_Home.py",
        title="Home",
        icon="🏠",
    )
    page_geometry = st.Page(
        "01_✈️_Geometry.py",
        title="Geometry",
        icon="✈️",
        default=(default_page == "geometry"),
    )
    page_workflow = st.Page(
        "pages/02_ ➡_Workflow.py",
        title="Workflow",
        icon="➡️",
        default=(default_page == "workflow"),
    )
    page_settings = st.Page(
        "pages/03_⚙️_Settings.py",
        title="Settings",
        icon="⚙️",
        default=(default_page == "settings"),
    )
    page_run = st.Page(
        "pages/04_▶️_Run_Workflow.py",
        title="Run Workflow",
        icon="▶️",
    )
    page_results = st.Page(
        "pages/05_📈_Results.py",
        title="Results",
        icon="📈",
    )

    pg = st.navigation(
        pages=[
            page_home,
            page_geometry,
            page_workflow,
            page_settings,
            page_run,
            page_results,
        ],
        expanded=True,
    )
    pg.run()


if __name__ == "__main__":
    main()
