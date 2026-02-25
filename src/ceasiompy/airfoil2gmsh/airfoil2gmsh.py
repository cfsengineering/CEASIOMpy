# Imports
from ceasiompy.airfoil2gmsh.func.utils import process_2d_airfoil

from pathlib import Path
from typing import Callable
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.airfoil2gmsh import MODULE_NAME
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# Methods

def _progress_update(
    progress_callback: Callable[..., None] | None,
    *,
    detail: str | None = None,
    progress: float | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(detail=detail, progress=progress)


# Main

def main(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """Mesh a airfoil-CPACS."""
    tixi = cpacs.tixi

    # Check if we are in 2D mode - separate try/except to not catch process_2d_airfoil errors
    geometry_mode = None
    try:
        geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        log.info(f"Geometry mode found in CPACS: {geometry_mode}")
    except Exception:
        # No geometry mode specified or xpath doesn't exist, assume 3D
        log.info("No geometry mode specified in CPACS, defaulting to 3D mode.")

    # Process 2D if geometry mode is 2D (let exceptions propagate)
    if tixi.getTextElement(GEOMETRY_MODE_XPATH) != "2D":
        raise ValueError(f"Can not call {MODULE_NAME} for a 3D-cpacs file.")

    log.info("2D airfoil mode detected. Running 2D processing only...")
    _progress_update(progress_callback, detail="Processing 2D airfoil...", progress=0.15)
    process_2d_airfoil(
        cpacs=cpacs,
        results_dir=results_dir,
    )
    log.info("2D processing completed, returning without 3D mesh generation.")
    _progress_update(progress_callback, detail="2D processing completed.", progress=1.0)
