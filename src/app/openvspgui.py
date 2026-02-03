"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.
"""

# Futures
from __future__ import annotations

# Imports
import os
import sys
import subprocess
import streamlit as st

from ceasiompy.utils.ceasiompyutils import has_display

from typing import Final
from pathlib import Path

from ceasiompy.VSP2CPACS import (
    SOFTWARE_PATH as OPENVSP_PATH,
    MODULE_STATUS as VSP2CPACS_MODULE_STATUS,
)

# Constants

_VSP2CPACS_OUT_TOKEN: Final[str] = "__CEASIOMPY_VSP2CPACS_OUT__="

# =================================================================================================
#    METHODS
# =================================================================================================


def _launch_openvsp() -> None:
    """Launch OpenVSP from the detected executable."""

    if OPENVSP_PATH is None or not OPENVSP_PATH.exists():
        st.error("OpenVSP path is not correctly set.")
        return

    wrapper = OPENVSP_PATH.with_name("openvsp")
    exec_path = wrapper if wrapper.exists() else OPENVSP_PATH

    if not has_display():
        st.error(
            "OpenVSP was found, but no graphical display is available for launching the GUI "
            "from this process."
        )
        st.caption(
            "If you are connected via SSH, enable X11 forwarding (`ssh -X`) or run OpenVSP on a "
            "machine with a desktop session."
        )
        return None

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


# Functions


def render_openvsp_panel() -> None:
    """Render the OpenVSP status/launch controls."""

    st.markdown("#### Create geometries with OpenVSP's UI")

    button_disabled = True
    status_col, button_col = st.columns([3, 1], vertical_alignment="center")
    with status_col:
        if not VSP2CPACS_MODULE_STATUS:
            st.info(
                "OpenVSP should be installed inside `INSTALLDIR/OpenVSP`."
            )
        elif OPENVSP_PATH is None or not OPENVSP_PATH.exists():
            st.error("OpenVSP executable could not be located.")
            st.caption(
                "Expected to find the `vsp` binary inside `INSTALLDIR/OpenVSP`. "
                "Use the platform specific installer inside the `installation/` folder."
            )
        else:
            st.success("OpenVSP detected and ready to launch")
            button_disabled = False

    with button_col:
        if st.button("Launch OpenVSP", disabled=button_disabled):
            try:
                _launch_openvsp()
            except Exception as e:
                st.error(f"Could not open OpenVSP: {e=}")


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
