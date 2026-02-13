"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import signal
import threading

from ceasiompy.utils.progress import progress_update
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.cpacs2gmsh.func.meshing import process_3d_geometry
from ceasiompy.cpacs2gmsh.func.airfoil2d import process_2d_airfoil

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
    if not tixi.checkElement(GEOMETRY_MODE_XPATH):
        raise ValueError("Did not find geometry mode.")

    geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
    log.info(f"Geometry mode found in CPACS: {geometry_mode}")

    # Process 2D if geometry mode is 2D (let exceptions propagate)
    if tixi.getTextElement(GEOMETRY_MODE_XPATH) == "2D":
        log.info("2D airfoil mode detected. Running 2D processing only...")
        progress_update(progress_callback, detail="Processing 2D airfoil...", progress=0.15)
        process_2d_airfoil(
            cpacs=cpacs,
            results_dir=results_dir,
        )
        log.info("2D processing completed, returning without 3D mesh generation.")
        progress_update(progress_callback, detail="2D processing completed.", progress=1.0)
        return None

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
