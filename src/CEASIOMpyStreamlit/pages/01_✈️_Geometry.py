"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.

| Author : Aidan Jungo
| Creation: 2022-09-09
| Author: Leon Deligny
| Modified: 16th April 2025

"""

# Futures
from __future__ import annotations

# =================================================================================================
#    IMPORTS
# =================================================================================================

import os
import sys
import hashlib
import subprocess
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from urllib.parse import urlparse

from ceasiompy.utils import get_wkdir
from ceasiompy.utils.ceasiompyutils import parse_bool
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH, GEOM_XPATH
from ceasiompy.utils.cpacs_utils import create_minimal_cpacs_2d
from CEASIOMpyStreamlit.streamlitutils import create_sidebar

# Airfoil generation functions (optional)
try:
    from gmshairfoil2d.airfoil_func import NACA_4_digit_geom, get_airfoil_points
    GMSHAIRFOIL2D_AVAILABLE = True
except ImportError:
    GMSHAIRFOIL2D_AVAILABLE = False
    NACA_4_digit_geom = None
    get_airfoil_points = None

from stl import mesh
from typing import Final
from pathlib import Path
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import create_branch
from tixi3.tixi3wrapper import Tixi3
from tigl3.tigl3wrapper import Tigl3
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.VSP2CPACS import (
    SOFTWARE_PATH as OPENVSP_PATH,
    MODULE_STATUS as VSP2CPACS_MODULE_STATUS,
)

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT: Final[str] = (
    "### How to use CEASIOMpy?\n"
    "1. Design your geometry\n"
    "1. Or upload an existing geometry\n"
    "1. Go to *Workflow* page (with menu above)\n"
)

PAGE_NAME: Final[str] = "Geometry"

_VSP2CPACS_OUT_TOKEN: Final[str] = "__CEASIOMPY_VSP2CPACS_OUT__="


def _resolve_frontend_portal_url() -> str | None:
    """Return the first configured frontend origin so we can link back to the portal."""
    raw_origins = os.environ.get("VITE_FRONTEND_ORIGINS") or ""
    for origin in raw_origins.split(","):
        candidate = origin.strip()
        if not candidate:
            continue
        parsed = urlparse(candidate)
        if parsed.scheme and parsed.netloc:
            return candidate
        return f"http://{candidate}"
    frontend_url = os.environ.get("VITE_STREAMLIT_URL")
    if frontend_url:
        parsed = urlparse(frontend_url)
        if parsed.scheme and parsed.netloc:
            return frontend_url
        return f"http://{frontend_url}"
    return None


# =================================================================================================
#    SESSION GUARD
# =================================================================================================


def _enforce_session_token() -> None:
    """Ensure the Streamlit UI is accessed only via a matching session token."""
    expected_token = os.environ.get("CEASIOMPY_SESSION_TOKEN")
    if not expected_token:
        return
    params = st.query_params
    provided_values = params.get("session_token")
    provided_token = (provided_values or [""])[0]
    if provided_token != expected_token:
        st.error(
            "Unauthorized access. Launch CEASIOMpy from the web portal to continue your session."
        )
        portal_url = _resolve_frontend_portal_url()
        if portal_url:
            st.markdown(
                f"[Return to the web portal →]({portal_url})",
                unsafe_allow_html=True,
            )
        st.stop()


# _enforce_session_token()

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def save_airfoil_and_create_cpacs(
    airfoil_name: str,
    airfoil_x: list[float],
    airfoil_y: list[float],
    wkdir: Path,
) -> CPACS:
    """
    Save airfoil coordinates to a .dat file and create/update a CPACS file.

    Args:
        airfoil_name: Name of the airfoil (e.g., "0012", "e211")
        airfoil_x: List of x coordinates
        airfoil_y: List of y coordinates
        wkdir: Working directory path

    Returns:
        CPACS object with the airfoil profile reference
    """
    # Create profiles directory if it doesn't exist
    profiles_dir = wkdir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Save airfoil coordinates to .dat file
    airfoil_filename = f"airfoil_{airfoil_name}.dat"
    airfoil_path = profiles_dir / airfoil_filename

    with open(airfoil_path, "w") as f:
        f.write(f"{airfoil_name}\n")
        for x, y in zip(airfoil_x, airfoil_y):
            f.write(f"{x:.8f} {y:.8f}\n")

    # Create or update CPACS file
    cpacs_path = wkdir / "ToolInput.xml"

    if cpacs_path.exists():
        # Update existing CPACS - open with TIXI for 2D
        tixi = Tixi3()
        tixi.open(str(cpacs_path))
    else:
        # Create minimal CPACS structure for 2D airfoil
        tixi = create_minimal_cpacs_2d(cpacs_path, f"2D Airfoil Analysis - {airfoil_name}")

    # Add airfoil profile to CPACS
    airfoil_uid = f"airfoil_{airfoil_name}"

    # Create airfoil node
    airfoils_xpath = "/cpacs/vehicles/profiles/wingAirfoils"
    create_branch(tixi, airfoils_xpath)

    # Check if airfoil already exists, if so remove it
    try:
        existing_idx = 1
        while True:
            test_xpath = f"{airfoils_xpath}/wingAirfoil[{existing_idx}]"
            try:
                existing_uid = tixi.getTextAttribute(test_xpath, "uID")
                if existing_uid == airfoil_uid:
                    tixi.removeElement(test_xpath)
                    break
                existing_idx += 1
            except Exception:
                break
    except Exception:
        pass

    # Add new airfoil
    airfoil_xpath = f"{airfoils_xpath}/wingAirfoil"
    tixi.createElement(airfoils_xpath, "wingAirfoil")

    # Get the index of the newly created airfoil
    n_airfoils = tixi.getNamedChildrenCount(airfoils_xpath, "wingAirfoil")
    airfoil_xpath = f"{airfoils_xpath}/wingAirfoil[{n_airfoils}]"

    tixi.addTextAttribute(airfoil_xpath, "uID", airfoil_uid)

    create_branch(tixi, airfoil_xpath + "/name")
    tixi.updateTextElement(airfoil_xpath + "/name", airfoil_name)

    create_branch(tixi, airfoil_xpath + "/description")
    tixi.updateTextElement(airfoil_xpath + "/description", f"2D airfoil profile {airfoil_name}")

    # Add point list with file reference
    create_branch(tixi, airfoil_xpath + "/pointList")
    point_list_xpath = airfoil_xpath + "/pointList"

    # Reference to external file
    create_branch(tixi, point_list_xpath + "/file")
    tixi.updateTextElement(point_list_xpath + "/file", str(airfoil_path))

    # Set geometry mode to 2D
    create_branch(tixi, GEOMETRY_MODE_XPATH)
    tixi.updateTextElement(GEOMETRY_MODE_XPATH, "2D")

    # Save CPACS file using TIXI
    tixi.save(str(cpacs_path), True)
    tixi.close()

    # Return the path for reference
    return cpacs_path


def convert_vsp3_to_cpacs(vsp3_path: Path, *, output_dir: Path) -> Path:
    """Convert a VSP3 file to CPACS in a separate process.

    OpenVSP Python bindings may segfault; running conversion out-of-process prevents the Streamlit
    server from crashing and allows reporting the error.
    """

    env = os.environ.copy()
    cmd = [
        sys.executable,
        "-c",
        (
            "import sys\n"
            "from pathlib import Path\n"
            "from ceasiompy.VSP2CPACS.vsp2cpacs import main\n"
            "out = main(sys.argv[1], output_dir=sys.argv[2])\n"
            f"print('{_VSP2CPACS_OUT_TOKEN}' + str(Path(out)))\n"
        ),
        str(vsp3_path),
        str(output_dir),
    ]

    completed = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        details = "\n".join([s for s in [stderr, stdout] if s])
        if "ModuleNotFoundError" in details and "openvsp" in details:
            raise RuntimeError(
                "Cannot convert VSP3 files because the `openvsp` Python bindings are missing."
            )
        raise RuntimeError(
            "VSP3 conversion failed"
            + (f" (exit code {completed.returncode})." if completed.returncode > 0 else ".")
            + (f"\n\n{details}" if details else "")
        )

    combined_output_lines = []
    if completed.stdout:
        combined_output_lines.extend(completed.stdout.splitlines())
    if completed.stderr:
        combined_output_lines.extend(completed.stderr.splitlines())

    for line in reversed(combined_output_lines):
        token_idx = line.find(_VSP2CPACS_OUT_TOKEN)
        if token_idx == -1:
            continue
        reported_path = line[token_idx + len(_VSP2CPACS_OUT_TOKEN) :].strip()
        if reported_path:
            return Path(reported_path)

    raise RuntimeError(
        "VSP3 conversion finished but did not report the output CPACS path."
        "\n\n--- stdout ---\n"
        + (completed.stdout or "")
        + "\n--- stderr ---\n"
        + (completed.stderr or "")
    )


def close_cpacs_handles(cpacs: CPACS | None, *, detach: bool = True) -> None:
    """Best-effort close of CPACS (TIXI/TIGL) resources.

    Some CPACS wrappers close underlying C handles again in their destructor; to
    avoid double-close heap corruption, this helper can optionally detach the
    closed handles from the CPACS instance.
    """

    if cpacs is None:
        return

    tixi: Tixi3 | None = getattr(cpacs, "tixi", None)
    if tixi is not None:
        try:
            tixi.close()
        except Exception:
            pass

    tigl: Tigl3 | None = getattr(cpacs, "tigl", None)
    if tigl is not None:
        try:
            tigl.close()
        except Exception:
            pass

    if detach:
        setattr(cpacs, "tixi", None)
        setattr(cpacs, "tigl", None)


def launch_openvsp() -> None:
    """Launch OpenVSP from the detected executable."""

    if OPENVSP_PATH is None or not OPENVSP_PATH.exists():
        st.error("OpenVSP path is not correctly set.")
        return

    wrapper = OPENVSP_PATH.with_name("openvsp")
    exec_path = wrapper if wrapper.exists() else OPENVSP_PATH

    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        st.error(
            "OpenVSP was found, but no graphical display is available for launching the GUI "
            "from this process."
        )
        st.caption(
            "If you are connected via SSH, enable X11 forwarding (`ssh -X`) or run OpenVSP on a "
            "machine with a desktop session."
        )
        return

    # OpenVSP is sensitive to polluted environments (e.g., HPC toolchains adding Intel/MPI libs to
    # LD_LIBRARY_PATH). Launch it with a minimal environment to avoid loading incompatible X11/GL
    # libraries.
    home_dir = os.environ.get("HOME", str(Path.home()))
    xauthority = os.environ.get("XAUTHORITY", str(Path(home_dir) / ".Xauthority"))
    display = os.environ.get("DISPLAY", "")
    vsp_lib_dir = OPENVSP_PATH.with_name("lib")
    env = {
        "HOME": home_dir,
        "USER": os.environ.get("USER", ""),
        "PATH": "/usr/bin:/bin",
        "DISPLAY": display,
        "XAUTHORITY": xauthority,
        # Bundle libstdc++/libgcc when needed; keep LD_LIBRARY_PATH minimal on purpose.
        "LD_LIBRARY_PATH": str(vsp_lib_dir) if vsp_lib_dir.is_dir() else "",
        # Preserve locale if set (can affect font rendering).
        "LANG": os.environ.get("LANG", ""),
        "LC_ALL": os.environ.get("LC_ALL", ""),
    }
    subprocess.Popen(
        args=[str(exec_path)],
        cwd=str(exec_path.parent),
        stderr=subprocess.STDOUT,
        env=env,
    )


def render_openvsp_panel() -> None:
    """Render the OpenVSP status/launch controls."""

    with st.container(border=True):
        st.markdown("#### Create or update geometries with OpenVSP")

        button_disabled = True
        status_col, button_col = st.columns([4, 1])
        with status_col:
            if not VSP2CPACS_MODULE_STATUS:
                st.info(
                    "OpenVSP is not enabled for this installation. "
                    "Install it inside `INSTALLDIR/OpenVSP` to use the geometry converter."
                )
            elif OPENVSP_PATH is None or not OPENVSP_PATH.exists():
                st.error("OpenVSP executable could not be located.")
                st.caption(
                    "Expected to find the `vsp` binary inside `INSTALLDIR/OpenVSP`. "
                    "Use the platform specific installer inside the `installation/` folder."
                )
            else:
                st.success("OpenVSP detected and ready to launch")
                st.caption("Use OpenVSP to edit your geometry, then re-import the CPACS.")
                button_disabled = False

        with button_col:
            if st.button("Launch OpenVSP", disabled=button_disabled):
                try:
                    launch_openvsp()
                except Exception as e:
                    st.error(f"Could not open OpenVSP: {e}")


def clean_toolspecific(cpacs: CPACS) -> CPACS:
    air_name = cpacs.ac_name

    if "ac_name" not in st.session_state or st.session_state.ac_name != air_name:
        # Remove selected_cpacs.xml if it exists
        gui_xml = get_wkdir() / "selected_cpacs.xml"
        if gui_xml.exists():
            os.remove(gui_xml)

        st.session_state.new_file = True

        # Clean input CPACS file
        tixi = cpacs.tixi
        if tixi.checkElement("/cpacs/toolspecific/CEASIOMpy"):
            tixi.removeElement("/cpacs/toolspecific/CEASIOMpy")

        # Reload CPACS file to apply changes
        # Specific to CPACS-VSP3 conversion files
        cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

        st.session_state["ac_name"] = cpacs.ac_name
        return cpacs
    else:
        st.session_state["new_file"] = False
        return cpacs


def section_select_cpacs() -> None:
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    if not parse_bool(os.environ.get("CEASIOMPY_CLOUD", False)):
        render_openvsp_panel()

    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir

    # Conversion container
    with st.container(border=True):
        st.markdown("#### Load a CPACS or VSP3 file")

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
                st.session_state.cpacs = clean_toolspecific(st.session_state.cpacs)
            else:
                st.session_state.cpacs = None

        # File uploader widget
        uploaded_file = st.file_uploader(
            "Load a CPACS (.xml) or VSP3 (.vsp3) file",
            type=["xml", "vsp3"],
            key="geometry_file_uploader",
        )

        if uploaded_file:
            uploaded_bytes = uploaded_file.getbuffer()
            uploaded_digest = hashlib.sha256(uploaded_bytes).hexdigest()
            last_digest = st.session_state.get("last_uploaded_digest")
            last_name = st.session_state.get("last_uploaded_name")

            # Streamlit reruns the script on any state change; prevent re-processing the
            # exact same uploaded file over and over making an infinite-loop.

            # CONDITION 1: same file content (digest)
            # CONDITION 2: same file name (to avoid re-processing different files with same content
            is_same_upload = (uploaded_digest == last_digest) and (uploaded_file.name == last_name)

            wkdir = st.session_state.workflow.working_dir
            uploaded_path = Path(wkdir, uploaded_file.name)

            if not is_same_upload:
                with open(uploaded_path, "wb") as f:
                    f.write(uploaded_bytes)
                st.session_state["last_uploaded_digest"] = uploaded_digest
                st.session_state["last_uploaded_name"] = uploaded_file.name

            if uploaded_path.suffix == ".vsp3":
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
                    st.session_state["cpacs"] = CPACS(str(new_cpacs_path))

                # No conversion
                else:
                    # Same file re-uploaded: reuse the last generated CPACS path.
                    previous_cpacs_path = st.session_state.get("last_converted_cpacs_path")
                    if previous_cpacs_path and Path(previous_cpacs_path).exists():
                        # Use the last generated CPACS path
                        new_cpacs_path = Path(previous_cpacs_path)
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
                        st.session_state["cpacs"] = CPACS(str(new_cpacs_path))

            elif uploaded_path.suffix == ".xml":
                new_cpacs_path = uploaded_path
                st.session_state["last_converted_cpacs_path"] = str(uploaded_path)
                st.session_state["cpacs"] = CPACS(str(uploaded_path))
            else:
                st.warning(f"Unsupported file suffix {uploaded_path.suffix=}")
                return None

        # Display the file uploader widget with the previously uploaded file
        if "cpacs" in st.session_state and st.session_state.cpacs:
            st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
            with st.container(border=True):
                section_3D_view(force_regenerate=True)


def section_3D_view(*, force_regenerate: bool = False) -> None:
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    """

    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")
    if not force_regenerate and stl_file.exists():
        pass
    elif hasattr(st.session_state.cpacs, "aircraft") and hasattr(
        st.session_state.cpacs.aircraft, "tigl"
    ):
        with st.spinner("Meshing geometry (STL export)..."):
            st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
    else:
        st.error("Cannot generate 3D preview (missing TIGL geometry handle).")
        return
    your_mesh = mesh.Mesh.from_file(stl_file)
    triangles = your_mesh.vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T

    # Compute bounds and cube size
    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)
    min_z, max_z = np.min(z), np.max(z)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    max_range = max(max_x - min_x, max_y - min_y, max_z - min_z) / 2

    # Set axis limits so the mesh is centered in a cube
    x_range = [center_x - max_range, center_x + max_range]
    y_range = [center_y - max_range, center_y + max_range]
    z_range = [center_z - max_range, center_z + max_range]

    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color="orange", opacity=0.5)])
    fig.update_layout(
        width=900,
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode="cube",
        ),
    )
    st.plotly_chart(fig, width="content")


def plot_airfoil_2d(x_coords, y_coords, title="Airfoil Profile"):
    """
    Plot 2D airfoil coordinates using plotly.

    Args:
        x_coords: Array or list of X coordinates
        y_coords: Array or list of Y coordinates
        title: Plot title
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=3, color='blue'),
        fill='toself',
        fillcolor='rgba(0, 100, 200, 0.2)',
        name='Airfoil'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="x/c",
        yaxis_title="y/c",
        width=900,
        height=500,
        showlegend=False,
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)


def section_2d_airfoil() -> None:
    """
    Section for 2D airfoil selection and loading.
    """

    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)

    # Check if gmshairfoil2d is available
    if not GMSHAIRFOIL2D_AVAILABLE:
        st.error(
            "**gmshairfoil2d module not found!**\n\n"
            "The 2D airfoil functionality requires the gmshairfoil2d package. "
            "Please install it using:\n\n"
            "```bash\n"
            "pip install gmshairfoil2d\n"
            "```\n\n"
            "Or update your conda environment:\n\n"
            "```bash\n"
            "conda env update -f environment.yml\n"
            "```"
        )
        return

    with st.container(border=True):
        st.markdown("#### Select or Load Airfoil Profile")

        # Radio button to choose between predefined or custom airfoil
        airfoil_option = st.radio(
            "Choose airfoil source:",
            ["Predefined Airfoil", "Upload Custom Profile"],
            horizontal=True
        )

        if airfoil_option == "Predefined Airfoil":
            # NACA airfoil selection
            col1, col2 = st.columns([3, 1])

            with col1:
                naca_code = st.text_input(
                    "Enter NACA code (e.g., 0012, 2412, 4415) or airfoil name (e.g., e211, dae11):",
                    value="0012",
                    help="Display all airfoil available in the database : https://m-selig.ae.illinois.edu/ads/coord_database.html"
                )

            with col2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                generate_clicked = st.button("✔ Generate", help="Generate airfoil from NACA code")

            # Display success message full width outside columns
            if generate_clicked:
                if naca_code:
                    try:
                        # Check if it's a NACA 4-digit code
                        if len(naca_code) == 4 and naca_code.isdigit():
                            # Generate NACA 4-digit airfoil
                            coords_list = NACA_4_digit_geom(naca_code, nb_points=200)
                            coords = np.array(coords_list)
                            st.session_state["airfoil_type"] = "NACA"
                            st.session_state["airfoil_code"] = naca_code
                        else:
                            # Try to get airfoil from database
                            coords_list = get_airfoil_points(naca_code)
                            coords = np.array(coords_list)
                            st.session_state["airfoil_type"] = "Predefined"
                            st.session_state["airfoil_code"] = naca_code

                        # Extract x and y coordinates (coords is [N, 3] with z=0)
                        airfoil_x = coords[:, 0].tolist()
                        airfoil_y = coords[:, 1].tolist()

                        st.session_state["airfoil_x"] = airfoil_x
                        st.session_state["airfoil_y"] = airfoil_y

                        # Save airfoil to .dat file and create/update CPACS
                        cpacs_path = save_airfoil_and_create_cpacs(
                            airfoil_name=naca_code,
                            airfoil_x=airfoil_x,
                            airfoil_y=airfoil_y,
                            wkdir=wkdir,
                        )

                        # Store path in session state
                        st.session_state["cpacs_path"] = str(cpacs_path)

                        # Also save geometry mode and airfoil type to CPACS
                        tixi = Tixi3()
                        tixi.open(str(cpacs_path))

                        create_branch(tixi, GEOM_XPATH + "/airfoilType")
                        if st.session_state["airfoil_type"] == "NACA":
                            tixi.updateTextElement(GEOM_XPATH + "/airfoilType", "NACA")
                            create_branch(tixi, GEOM_XPATH + "/airfoilCode")
                            tixi.updateTextElement(GEOM_XPATH + "/airfoilCode", naca_code)
                        else:
                            tixi.updateTextElement(GEOM_XPATH + "/airfoilType", "Custom")
                            create_branch(tixi, GEOM_XPATH + "/airfoilName")
                            tixi.updateTextElement(GEOM_XPATH + "/airfoilName", naca_code)

                        tixi.save(str(cpacs_path), True)
                        tixi.close()

                        st.success(
                            f"✓ Airfoil '{naca_code}' generated with {len(coords)} points\n\n"
                            f"📄 Saved to: `profiles/airfoil_{naca_code}.dat`\n\n"
                            f"📋 CPACS updated: `ToolInput.xml`"
                        )
                    except Exception as e:
                        st.error(f"Failed to generate airfoil: {str(e)}")
                        st.info("For NACA airfoils, use 4 digits (e.g., 0012, 2412). "
                               "For database airfoils, check the available names at: "
                               "https://m-selig.ae.illinois.edu/ads/coord_database.html")
                else:
                    st.warning("Please enter a valid NACA code")

        else:  # Upload Custom Profile
            uploaded_file = st.file_uploader(
                "Upload airfoil coordinate file",
                type=["dat", "txt", "csv"],
                help="Upload a file containing airfoil coordinates (x, y)"
            )

            if uploaded_file is not None:
                try:
                    # Save uploaded file
                    airfoil_path = Path(wkdir, uploaded_file.name)
                    with open(airfoil_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Read and parse the airfoil coordinates
                    # Try to read as space/tab separated values, skipping header lines
                    coords_data = []
                    with open(airfoil_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            # Skip empty lines and lines that don't start with a number
                            if not line or not line[0].replace('-', '').replace('.', '').isdigit():
                                continue
                            # Split by whitespace and take first two values
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    x = float(parts[0])
                                    y = float(parts[1])
                                    coords_data.append([x, y])
                                except ValueError:
                                    continue

                    if len(coords_data) > 0:
                        coords = np.array(coords_data)
                        airfoil_x = coords[:, 0].tolist()
                        airfoil_y = coords[:, 1].tolist()

                        st.session_state["airfoil_x"] = airfoil_x
                        st.session_state["airfoil_y"] = airfoil_y
                        st.session_state["airfoil_type"] = "Custom"
                        st.session_state["airfoil_file"] = str(airfoil_path)

                        # Extract airfoil name from filename
                        airfoil_name = uploaded_file.name.split('.')[0]

                        # Save airfoil to .dat file and create/update CPACS
                        cpacs_path = save_airfoil_and_create_cpacs(
                            airfoil_name=airfoil_name,
                            airfoil_x=airfoil_x,
                            airfoil_y=airfoil_y,
                            wkdir=wkdir,
                        )

                        # Store path in session state
                        st.session_state["cpacs_path"] = str(cpacs_path)

                        # Also save geometry mode and airfoil type to CPACS
                        tixi = Tixi3()
                        tixi.open(str(cpacs_path))

                        create_branch(tixi, GEOM_XPATH + "/airfoilType")
                        tixi.updateTextElement(GEOM_XPATH + "/airfoilType", "Custom")
                        create_branch(tixi, GEOM_XPATH + "/airfoilName")
                        tixi.updateTextElement(GEOM_XPATH + "/airfoilName", airfoil_name)

                        tixi.save(str(cpacs_path), True)
                        tixi.close()

                    # Display success message full width outside nested context
                    if len(coords_data) > 0:
                        st.success(
                            f"✓ Airfoil profile '{uploaded_file.name}' loaded with {len(coords)} points\n\n"
                            f"📄 Saved to: `profiles/airfoil_{airfoil_name}.dat`\n\n"
                            f"📋 CPACS updated: `ToolInput.xml`"
                        )
                    else:
                        st.error("No valid coordinate data found in the file")
                except Exception as e:
                    st.error(f"Failed to read airfoil file: {str(e)}")
                    st.info("File should contain x y coordinates, one point per line")

    # Display current selection and plot
    if "airfoil_type" in st.session_state:
        st.markdown("---")
        st.markdown("#### Current Airfoil Selection")

        if st.session_state["airfoil_type"] == "NACA":
            st.info(f"**NACA {st.session_state.get('airfoil_code', 'N/A')}** airfoil selected")
        elif st.session_state["airfoil_type"] == "Predefined":
            st.info(f"**Predefined airfoil:** {st.session_state.get('airfoil_code', 'N/A')}")
        elif st.session_state["airfoil_type"] == "Custom":
            st.info(f"**Custom profile:** {Path(st.session_state.get('airfoil_file', '')).name}")

        # Display plot if coordinates are available
        if "airfoil_x" in st.session_state and "airfoil_y" in st.session_state:
            st.markdown("#### Airfoil Visualization")
            with st.container(border=True):
                airfoil_name = st.session_state.get('airfoil_code', 'Custom')
                plot_airfoil_2d(
                    st.session_state["airfoil_x"],
                    st.session_state["airfoil_y"],
                    title=f"Airfoil: {airfoil_name}"
                )
        else:
            st.warning("Airfoil coordinates will be displayed here once generated/loaded")


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    create_sidebar(HOW_TO_TEXT)
    st.markdown(
        """
        <style>
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

    # Mode selection buttons
    st.markdown("### Select Geometry Mode")
    col1, col2, _ = st.columns([3, 3, 6])

    with col1:
        if st.button("📐 2D Airfoil", use_container_width=True):
            st.session_state["geometry_mode"] = "2D"
            # Save mode to CPACS if available
            if "cpacs" in st.session_state:
                cpacs = st.session_state["cpacs"]
                create_branch(cpacs.tixi, GEOMETRY_MODE_XPATH)
                cpacs.tixi.updateTextElement(GEOMETRY_MODE_XPATH, "2D")
                cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    with col2:
        if st.button("✈️ 3D Geometry", use_container_width=True):
            st.session_state["geometry_mode"] = "3D"
            # Save mode to CPACS if available
            if "cpacs" in st.session_state:
                cpacs = st.session_state["cpacs"]
                create_branch(cpacs.tixi, GEOMETRY_MODE_XPATH)
                cpacs.tixi.updateTextElement(GEOMETRY_MODE_XPATH, "3D")
                cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    # Initialize mode if not set
    if "geometry_mode" not in st.session_state:
        # Try to load mode from CPACS
        if "cpacs" in st.session_state:
            cpacs = st.session_state["cpacs"]
            try:
                mode = cpacs.tixi.getTextElement(GEOMETRY_MODE_XPATH)
                st.session_state["geometry_mode"] = mode
            except Exception:
                st.session_state["geometry_mode"] = "3D"
        else:
            st.session_state["geometry_mode"] = "3D"

    st.markdown("---")

    # Display appropriate section based on mode
    if st.session_state["geometry_mode"] == "3D":
        st.markdown("**Mode:** 3D Geometry")
        section_select_cpacs()
    else:
        st.markdown("**Mode:** 2D Airfoil")
        section_2d_airfoil()
