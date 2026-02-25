"""
CEASIOMpy: Conceptual Aircraft Design Software

Entry point for the Streamlit UI with explicit page ordering.
"""

# Imports

import asyncio
import os
import json
import streamlit as st

from ceasiompy.utils import get_wkdir
from openvspgui import convert_vsp3_to_cpacs
from ceasiompy.utils.guiobjects import add_value
from ceasiompy.utils.ceasiompyutils import update_xpath_at_xyz

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH, AIRFOILS_XPATH

# VTK web rendering can fail with uvloop event loops.
# Force the stdlib asyncio policy early so spawned subprocesses inherit it.
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


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


def _read_airfoil_xy(airfoil_path: Path) -> tuple[list[float], list[float]]:
    x_vals: list[float] = []
    y_vals: list[float] = []

    with open(airfoil_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("#", "!", "%", "//")):
                continue

            line = line.replace(",", " ")
            parts = [p for p in line.split() if p]
            if len(parts) < 2:
                continue

            try:
                x_vals.append(float(parts[0]))
                y_vals.append(float(parts[1]))
            except ValueError:
                continue

    if len(x_vals) < 3:
        raise ValueError(
            f"Airfoil file '{airfoil_path.name}' must contain at least 3 valid x y points."
        )

    return x_vals, y_vals


def _create_cpacs_from_airfoil(airfoil_path: Path, wkdir: Path) -> Path:
    airfoil_x, airfoil_y = _read_airfoil_xy(airfoil_path)

    def _vector_to_str(values: list[float]) -> str:
        return ";".join(f"{v:.8f}" for v in values)

    newx_str = _vector_to_str(airfoil_x)
    newy_str = _vector_to_str([0.0] * len(airfoil_x))
    newz_str = _vector_to_str(airfoil_y)

    cpacs = CPACS(Path(CPACS_FILES_PATH, "airfoil.xml"))
    add_value(
        tixi=cpacs.tixi,
        xpath=GEOMETRY_MODE_XPATH,
        value="2D",
    )

    wingairfoil_xpath = AIRFOILS_XPATH + "/wingAirfoil[1]"
    update_xpath_at_xyz(
        tixi=cpacs.tixi,
        xpath=wingairfoil_xpath + "/pointList",
        x=newx_str,
        y=newy_str,
        z=newz_str,
    )
    cpacs_path = Path(wkdir, f"{airfoil_path.stem}.xml")
    cpacs.save_cpacs(cpacs_path, overwrite=True)
    return cpacs_path


def _load_cli_geometry(geometry_path: Path, wkdir: Path) -> None:
    suffix = geometry_path.suffix.lower()

    if suffix == ".xml":
        cpacs_path = geometry_path
        geometry_mode = "3D"
    elif suffix in {".vsp", ".vsp3"}:
        cpacs_path = convert_vsp3_to_cpacs(geometry_path, output_dir=wkdir)
        geometry_mode = "3D"
    elif suffix in {".csv", ".dat", ".txt"}:
        cpacs_path = _create_cpacs_from_airfoil(geometry_path, wkdir)
        geometry_mode = "2D"
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
