"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

| Author : Aidan Jungo
| Creation: 2018-11-06
| Modified: Leon Deligny
| Date: 24-Feb-2025

"""

# Imports

from cpacspy.cpacsfunctions import get_value
from ceasiompy.su2run.func.results import get_su2_results
from ceasiompy.utils.ceasiompyutils import get_sane_max_cpu
from ceasiompy.su2run.func.runconfigfiles import run_SU2_multi
from ceasiompy.su2run.func.config import (
    define_markers,
    load_su2_mesh_paths,
    generate_su2_cfd_config,
)

from pathlib import Path
from typing import Callable, Optional
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.cpacs2gmsh import GMSH_SYMMETRY_XPATH
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.su2run import (
    SU2_CONFIG_RANS_XPATH,
    SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
)


# Main

def _progress_update(
    progress_callback: Optional[Callable[..., None]],
    *,
    detail: str | None = None,
    progress: float | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(detail=detail, progress=progress)


def main(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Optional[Callable[..., None]] = None,
) -> None:
    """
    SU2Run module is decomposed into 4 parts.

        1. Retrieve the correct geometry: .su2 mesh files.
        2. For each .su2 file create a .cfg configuration file.
        3. Run each .cfg file in SU2_CFD.
        4. Retrieve force files results in configuration directory.
    """

    # Define variable
    tixi = cpacs.tixi

    _progress_update(progress_callback, detail="Reading CPACS settings...", progress=0.02)

    # Check if we are in 2D mode
    geometry_mode = None
    try:
        geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        log.info(f"Geometry mode found in CPACS: {geometry_mode}")
    except Exception:
        log.info("No geometry mode specified in CPACS, defaulting to 3D mode.")

    # Define constants
    nb_proc = int(get_sane_max_cpu())

    # In 2D mode, always use 2D template; otherwise read from CPACS
    if geometry_mode == "2D":
        config_file_type = "2D"
        rans = False  # Not applicable for 2D
        symmetric_mesh = "NO"  # No symmetry in 2D mode
        log.info("Using 2D template for 2D geometry mode (no symmetry).")
    else:
        config_file_type = str(get_value(tixi, SU2_CONFIG_RANS_XPATH))
        rans: bool = config_file_type == "RANS"
        symmetric_mesh = str(get_value(tixi, GMSH_SYMMETRY_XPATH))

    # 1. Load .su2 mesh files
    _progress_update(progress_callback, detail="Loading SU2 mesh paths...", progress=0.1)
    su2_mesh_paths, dynstab_su2_mesh_paths = load_su2_mesh_paths(tixi, results_dir)

    # Load only 1 mesh file for the su2 markers
    # Accross all different meshes for the same aircraft,
    # the markers will remain the same.
    _progress_update(progress_callback, detail="Defining mesh markers...", progress=0.2)
    mesh_markers = define_markers(tixi, su2_mesh_paths[0])
    _progress_update(progress_callback, detail="Mesh markers ready.", progress=0.3)

    # 2. Create configuration files
    if get_value(tixi, SU2_DYNAMICDERIVATIVES_BOOL_XPATH):
        log.info("----- Generating Dynamic Stability ConfigFile -----")
        _progress_update(
            progress_callback,
            detail="Generating dynamic stability config files...",
            progress=0.4,
        )

        generate_su2_cfd_config(
            cpacs=cpacs,
            wkdir=results_dir,
            su2_mesh_paths=dynstab_su2_mesh_paths,
            mesh_markers=mesh_markers,
            dyn_stab=True,
            rans=rans,
        )

    log.info(f"----- Generating {config_file_type} ConfigFile -----")
    _progress_update(
        progress_callback,
        detail=f"Generating {config_file_type} config files...",
        progress=0.5,
    )
    generate_su2_cfd_config(
        cpacs=cpacs,
        wkdir=results_dir,
        su2_mesh_paths=su2_mesh_paths,
        mesh_markers=mesh_markers,
        dyn_stab=False,
        rans=rans,
        symmetry=symmetric_mesh,
    )
    _progress_update(progress_callback, detail="Config files ready.", progress=0.6)

    # 3. Run each configuration file in SU2
    log.info(f"----- Running  {config_file_type} simulations -----")
    _progress_update(
        progress_callback,
        detail=f"Running {config_file_type} simulations...",
        progress=0.7,
    )
    run_SU2_multi(results_dir, nb_proc)
    _progress_update(progress_callback, detail="SU2 simulations completed.", progress=0.9)

    # 4. Retrieve SU2 results
    log.info("----- Updating CPACS and accessing results -----")
    _progress_update(progress_callback, detail="Updating CPACS with results...", progress=0.95)
    get_su2_results(cpacs, results_dir)
    _progress_update(progress_callback, detail="SU2 results ready.", progress=1.0)
