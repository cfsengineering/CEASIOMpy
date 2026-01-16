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

from ceasiompy.utils import get_wkdir
from ceasiompy.utils.ceasiompyutils import parse_bool
from CEASIOMpyStreamlit.streamlitutils import create_sidebar

from stl import mesh
from typing import Final
from pathlib import Path
from cpacspy.cpacspy import CPACS
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

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


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
    section_select_cpacs()
