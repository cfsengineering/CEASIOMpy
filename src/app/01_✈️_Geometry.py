"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.
"""

# Futures
from __future__ import annotations

# Imports
import os
import hashlib
import numpy as np
import streamlit as st

from ceasiompy.utils import get_wkdir
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.guiobjects import update_value
from gmshairfoil2d.airfoil_func import get_airfoil_points
from ceasiompy.utils.referencevalues import (
    compute_airfoil_ref_length,
    compute_aircraft_ref_values,
)
from ceasiompy.utils.ceasiompyutils import (
    parse_bool,
    safe_remove,
    update_xpath_at_xyz,
)
from streamlitutils import (
    scroll_down,
    create_sidebar,
    section_3D_view,
    close_cpacs_handles,
    build_default_upload,
)
from openvspgui import (
    render_openvsp_panel,
    convert_vsp3_to_cpacs,
)

from typing import Final
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy import log
from constants import BLOCK_CONTAINER
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    LENGTH_XPATH,
    AIRFOILS_XPATH,
    GEOMETRY_MODE_XPATH,
)

# Constants

HOW_TO_TEXT: Final[str] = (
    "### Select a Geometry \n"
    "1. Design a new one\n"
    "1. Upload an existing\n"
    "1. Go to *Workflow* page \n"
)

PAGE_NAME: Final[str] = "Geometry"


# Methods
def _clean_toolspecific(cpacs: CPACS) -> CPACS:
    air_name = cpacs.ac_name

    if "ac_name" not in st.session_state or st.session_state.ac_name != air_name:
        # Clean input CPACS file
        tixi = cpacs.tixi
        geometry_mode = None
        if tixi.checkElement(GEOMETRY_MODE_XPATH):
            geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        if tixi.checkElement("/cpacs/toolspecific/CEASIOMpy"):
            tixi.removeElement("/cpacs/toolspecific/CEASIOMpy")
        update_value(
            tixi=tixi,
            xpath=GEOMETRY_MODE_XPATH,
            value=geometry_mode if geometry_mode in {"2D", "3D"} else "3D",
        )

        st.session_state["ac_name"] = cpacs.ac_name
    else:
        st.session_state["new_file"] = False

    return cpacs


def _generate_cpacs_airfoil(naca_code: str) -> CPACS:
    coords = np.array(get_airfoil_points(naca_code))

    return _create_cpacs_from(
        airfoil_x=coords[:, 0].tolist(),
        airfoil_y=coords[:, 1].tolist(),
        airfoil_name=naca_code,
    )


def _create_cpacs_from(
    airfoil_x: list[float],
    airfoil_y: list[float],
    airfoil_name: str | None = None,
) -> CPACS:
    def _vector_to_str(values: list[float]) -> str:
        return ";".join(f"{v:.8f}" for v in values)

    newx_str = _vector_to_str(airfoil_x)
    newy_str = _vector_to_str([0.0] * len(airfoil_x))
    newz_str = _vector_to_str(airfoil_y)

    airfoil_ref_path = Path(CPACS_FILES_PATH, "airfoil.xml")

    cpacs = CPACS(airfoil_ref_path)
    update_value(
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

    st.session_state["uploaded_default_cpacs"] = False
    wkdir = st.session_state.workflow.working_dir
    wkdir.mkdir(parents=True, exist_ok=True)
    if airfoil_name is None:
        airfoil_name = "custom"
    safe_name = "".join(
        char if (char.isalnum() or char in ("-", "_")) else "_" for char in airfoil_name.strip()
    )
    if not safe_name:
        safe_name = "custom"
    new_cpacs_path = Path(wkdir, f"airfoil_{safe_name}.xml")
    cpacs.save_cpacs(new_cpacs_path, overwrite=True)

    st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
    cpacs = CPACS(str(new_cpacs_path))
    st.session_state["cpacs"] = cpacs
    return cpacs


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
                x_val = float(parts[0])
                y_val = float(parts[1])
            except ValueError:
                continue

            x_vals.append(x_val)
            y_vals.append(y_val)

    if len(x_vals) < 3:
        raise ValueError(
            f"Airfoil file '{airfoil_path.name}' must contain at least 3 valid x y points."
        )

    return x_vals, y_vals


def _section_generate_cpacs_airfoil() -> CPACS | None:
    st.markdown("#### Generate an Airfoil Profile")

    # NACA airfoil selection
    col1, col2 = st.columns([3, 1])

    with col1:
        naca_code = st.text_input(
            label="""Enter NACA code (e.g., 0012, 2412, 4415)
            or airfoil name (e.g., e211, dae11): """,
            value="0012",
            help="""All airfoils are available at:
            [Selig Airfoil Database](https://m-selig.ae.illinois.edu/ads/coord_database.html)
            """,
        )
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        generate_clicked = st.button(
            "Generate",
            help="Generate airfoil from NACA code",
            width="stretch",
        )

    # Display success message full width outside columns
    if generate_clicked and naca_code:
        try:
            return _generate_cpacs_airfoil(naca_code)
        except Exception as e:
            st.error(f"Failed to generate airfoil of {naca_code=}: {str(e)}")
            st.info(
                "For NACA airfoils, use 4 digits (e.g., 0012, 2412). "
                "For database airfoils, check the available names at: "
                "[Selig Airfoil Database]"
                "(https://m-selig.ae.illinois.edu/ads/coord_database.html)"
            )
    elif generate_clicked:
        st.warning("Please enter a valid NACA code.")


def _section_load_cpacs() -> CPACS | None:
    st.markdown("#### Load a CPACS (.xml) or VSP3 (.vsp3) file or XY Airfoil (.csv, .dat, .txt)")
    st.markdown("We handle the conversion to the CPACS format.")

    # Check if the CPACS file path is already in session state
    if "cpacs" in st.session_state:
        cpacs: CPACS = st.session_state.cpacs
        if Path(cpacs.cpacs_file).exists():
            # Reload the CPACS file into session state if its path exists
            # and the CPACS object is not already loaded or is different
            if (
                "cpacs" not in st.session_state
                or (
                    Path(getattr(st.session_state.cpacs, "cpacs_file", ""))
                    != Path(cpacs.cpacs_file)
                )
            ):
                close_cpacs_handles(st.session_state.get("cpacs"))
                st.session_state.cpacs = CPACS(cpacs.cpacs_file)
            st.session_state.cpacs = _clean_toolspecific(st.session_state.cpacs)
        else:
            st.session_state.cpacs = None

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Load a CPACS (.xml) or VSP3 (.vsp3) file",
        type=["xml", "vsp3", "csv", "dat", "txt"],
        key="geometry_file_uploader",
        label_visibility="collapsed",
    )

    uploaded_default = st.session_state.get("uploaded_default_cpacs", False)
    pending_default_cpacs = st.session_state.get("pending_default_cpacs")

    if not uploaded_file and pending_default_cpacs:
        default_cpacs_path = Path(pending_default_cpacs)
        uploaded_file = build_default_upload(default_cpacs_path)
        st.session_state["pending_default_cpacs"] = None
        st.session_state["uploaded_default_cpacs"] = False
        if uploaded_file is None:
            return None

    if not uploaded_file and not uploaded_default:
        if st.button(
            label="Load a default CPACS geometry",
            width="stretch",
        ):
            default_cpacs_path = Path(CPACS_FILES_PATH, "onera_m6.xml")
            st.session_state["pending_default_cpacs"] = str(default_cpacs_path)
            st.session_state["uploaded_default_cpacs"] = True
            st.rerun()
        else:
            return None

    if uploaded_file:
        st.session_state["uploaded_default_cpacs"] = False
        uploaded_bytes = uploaded_file.getbuffer()
        uploaded_digest = hashlib.sha256(uploaded_bytes).hexdigest()
        last_digest = st.session_state.get("last_uploaded_digest")
        last_name = st.session_state.get("last_uploaded_name")

        # Streamlit reruns the script on any state change; prevent re-processing the
        # exact same uploaded file over and over making an infinite-loop.

        # CONDITION 1: same file content (digest)
        # CONDITION 2: same file name (to avoid re-processing different files with same content
        is_same_upload = (uploaded_digest == last_digest) and (uploaded_file.name == last_name)

        # Any widget interaction (e.g. radio button) triggers reruns: avoid reloading
        # only when the uploader selection is unchanged. If the user explicitly loads
        # a different file, this condition is false and the file is processed.
        if isinstance(st.session_state.get("cpacs"), CPACS) and is_same_upload:
            return None

        wkdir = st.session_state.workflow.working_dir
        uploaded_path = Path(wkdir, uploaded_file.name)

        if not is_same_upload:
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_bytes)
            st.session_state["last_uploaded_digest"] = uploaded_digest
            st.session_state["last_uploaded_name"] = uploaded_file.name

        if (
            uploaded_path.suffix == ".csv"
            or uploaded_path.suffix == ".dat"
            or uploaded_path.suffix == ".txt"
        ):
            try:
                airfoil_x, airfoil_y = _read_airfoil_xy(uploaded_path)
            except Exception as exc:
                st.error(f"Failed to parse airfoil points from {uploaded_file.name}: {exc}")
                return None

            return _create_cpacs_from(
                airfoil_x=airfoil_x,
                airfoil_y=airfoil_y,
                airfoil_name=uploaded_path.stem,
            )

        elif uploaded_path.suffix == ".vsp3":
            should_convert = (not is_same_upload) or (
                st.session_state.get("last_converted_vsp3_digest") != uploaded_digest
            )

            # Convert VSP3 file to CPACS file
            if should_convert:
                with st.spinner("Converting VSP3 file to CPACS..."):
                    try:
                        new_cpacs_path = convert_vsp3_to_cpacs(
                            uploaded_path,
                            output_dir=wkdir,
                        )
                    except Exception as e:
                        st.error(str(e))
                        return None

                st.session_state["last_converted_vsp3_digest"] = uploaded_digest
                st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
                cpacs = CPACS(str(new_cpacs_path))
                update_value(
                    tixi=cpacs.tixi,
                    xpath=GEOMETRY_MODE_XPATH,
                    value="3D",
                )
                st.session_state["cpacs"] = cpacs
                return cpacs

            # No conversion
            else:
                # Same file re-uploaded: reuse the last generated CPACS path.
                previous_cpacs_path = st.session_state.get("last_converted_cpacs_path")
                if previous_cpacs_path and Path(previous_cpacs_path).exists():
                    # Use the last generated CPACS path
                    new_cpacs_path = Path(previous_cpacs_path)
                    cpacs = CPACS(str(new_cpacs_path))
                else:
                    # If no old generated CPACS found
                    st.warning(
                        "This VSP3 file was already uploaded, but no converted CPACS was "
                        "found in the working directory. Converting again."
                    )
                    with st.spinner("Converting VSP3 file to CPACS..."):
                        try:
                            new_cpacs_path = convert_vsp3_to_cpacs(
                                uploaded_path,
                                output_dir=wkdir,
                            )
                        except Exception as e:
                            st.error(str(e))
                            return None
                    st.session_state["last_converted_vsp3_digest"] = uploaded_digest
                    st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
                    cpacs = CPACS(str(new_cpacs_path))
                update_value(
                    tixi=cpacs.tixi,
                    xpath=GEOMETRY_MODE_XPATH,
                    value="3D",
                )
                st.session_state["cpacs"] = cpacs
                return cpacs

        elif uploaded_path.suffix == ".xml":
            new_cpacs_path = uploaded_path
            st.session_state["last_converted_cpacs_path"] = str(uploaded_path)
            cpacs = CPACS(str(uploaded_path))
            update_value(
                tixi=cpacs.tixi,
                xpath=GEOMETRY_MODE_XPATH,
                value="3D",
            )
            st.session_state["cpacs"] = cpacs
        else:
            st.warning(f"Unsupported file suffix {uploaded_path.suffix=}")
            return None

    return st.session_state.get("cpacs")


# Functions

def section_select_cpacs() -> None:
    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir

    tabs = [
        "Load Geometry",
        "Generate Airfoil",
    ]

    show_openvsp = not parse_bool(os.environ.get("CEASIOMPY_CLOUD", "False"))

    if show_openvsp:
        tabs.append("OpenVSP's UI")

    selected_tab = st.tabs(tabs, width="stretch")
    with selected_tab[0]:
        _section_load_cpacs()
    with selected_tab[1]:
        _section_generate_cpacs_airfoil()
    if show_openvsp:
        with selected_tab[2]:
            render_openvsp_panel()

    # ALWAYS use the session CPACS
    cpacs = st.session_state.get("cpacs")
    if not isinstance(cpacs, CPACS):
        return None

    tixi = cpacs.tixi

    # 2D mode or else; geometry mode is expected to exist.
    geometry_mode = str(get_value(tixi, xpath=GEOMETRY_MODE_XPATH))
    dim_mode = (geometry_mode == "2D")

    st.markdown("---")
    ref_area = None
    try:
        if not dim_mode:
            ref_area, ref_length = compute_aircraft_ref_values(cpacs)

        if dim_mode:
            ref_length = compute_airfoil_ref_length(cpacs)

    except Exception as e:
        ref_area, ref_length = 0.0, 0.0
        log.warning(f"""Could not compute from the CPACS file
            the reference area and length values {e=}
        """)

    title = f"**{cpacs.ac_name}** (Ref Length={float(ref_length):.3e}"
    if ref_area is not None:
        title += f", Ref Area={float(ref_area):.3e}"
    title += ")"
    st.markdown(title)

    section_3D_view(cpacs=cpacs, force_regenerate=True)

    # Once 3D view of CPACS file is done scroll down
    scroll_down()
    st.markdown("---")

    if tixi.checkElement(AREA_XPATH):
        ref_area = get_value(tixi, xpath=AREA_XPATH)

    if tixi.checkElement(LENGTH_XPATH):
        ref_length = get_value(tixi, xpath=LENGTH_XPATH)

    spec = 1 if dim_mode else 2
    cols = st.columns(
        spec=spec,
    )
    with cols[0]:
        new_ref_length = st.number_input(
            label="Reference Length",
            value=ref_length,
            min_value=0.0,
        )
    if not dim_mode:
        with cols[1]:
            new_ref_area = st.number_input(
                label="Reference Area",
                value=ref_area,
                min_value=0.0,
            )

    # 2D update
    if (
        dim_mode
        and np.isfinite(ref_length) and ref_length > 0.0
    ):
        update_value(
            tixi=tixi,
            xpath=LENGTH_XPATH,
            value=new_ref_length,
        )
        safe_remove(tixi, xpath=AREA_XPATH)
        st.info(f"""Updated cpacs file with reference (length={new_ref_length})""")

    # 3D update
    if (
        not dim_mode
        and np.isfinite(ref_area) and ref_area > 0.0
        and np.isfinite(ref_length) and ref_length > 0.0
    ):
        update_value(
            tixi=tixi,
            xpath=AREA_XPATH,
            value=new_ref_area,
        )
        update_value(
            tixi=tixi,
            xpath=LENGTH_XPATH,
            value=new_ref_length,
        )
        st.info(f"""Updated cpacs file with reference
             (length={new_ref_length}, area={new_ref_area})
        """)


# Main
if __name__ == "__main__":

    create_sidebar(HOW_TO_TEXT)
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
        /* Align navigation buttons with selectbox */
        .nav-button-container {
            display: flex;
            align-items: flex-end;
            height: 100%;
            padding-bottom: 5px;
            margin-top: 23px;  /* Matches the label height + spacing */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    # Initialize the workflow object
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    st.markdown("---")

    section_select_cpacs()
