"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import signal
import threading

from ceasiompy.utils.progress import progress_update
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.cpacs2gmsh.meshing.meshing import process_3d_geometry

from pathlib import Path
from typing import Callable
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.cpacs2gmsh import MODULE_NAME
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# gmsh Signal Patch

def _patch_signal_for_gmsh() -> None:
    """Avoid gmsh signal registration in non-main threads."""

    if threading.current_thread() is threading.main_thread():
        return

    if getattr(signal, "_ceasiompy_gmsh_patched", False):
        return

    def _noop_signal(*_args, **_kwargs):
        return None

    signal.signal = _noop_signal  # type: ignore[assignment]
    signal._ceasiompy_gmsh_patched = True  # type: ignore[attr-defined]
    log.warning("Patched signal.signal for gmsh import in non-main thread.")


_patch_signal_for_gmsh()


# Functions


def main(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """
    Main function.
    Defines setup for gmsh.
    """

    tixi = cpacs.tixi

    progress_update(
        detail="Reading CPACS settings...",
        progress=0.01,
        progress_callback=progress_callback,
    )

    # Check if we are in 2D mode - separate try/except to not catch process_2d_airfoil errors
    geometry_mode = None
    try:
        geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        log.info(f"Geometry mode found in CPACS: {geometry_mode}")
    except Exception:
        # No geometry mode specified or xpath doesn't exist, assume 3D
        log.info("No geometry mode specified in CPACS, defaulting to 3D mode.")

    # Process 2D if geometry mode is 2D (let exceptions propagate)
    if tixi.getTextElement(GEOMETRY_MODE_XPATH) != "3D":
        raise ValueError(f"Can not call {MODULE_NAME} for a airfoil-cpacs file.")

    # If we reach here, we are in 3D mode
    log.info("Proceeding with 3D mesh generation...")
    process_3d_geometry(
        cpacs=cpacs,
        results_dir=results_dir,
        progress_callback=progress_callback,
    )


# Main

if __name__ == "__main__":
    call_main(main, MODULE_NAME)
