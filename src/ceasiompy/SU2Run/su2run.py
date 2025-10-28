"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

| Author : Aidan Jungo
| Creation: 2018-11-06
| Modified: Leon Deligny
| Date: 24-Feb-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.SU2Run.func.results import get_su2_results
from ceasiompy.SU2Run.func.runconfigfiles import run_SU2_multi
from ceasiompy.SU2Run.func.config import (
    define_markers,
    load_su2_mesh_paths,
    generate_su2_cfd_config,
)

from pathlib import Path
from typing import Union
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.CPACS2GMSH import GMSH_SYMMETRY_XPATH
from ceasiompy.SU2Run import (
    SU2_NB_CPU_XPATH,
    SU2_CONFIG_RANS_XPATH,
    SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    geometry: Union[CPACS, Path],
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    SU2Run module is decomposed into 4 parts.

        1. Retrieve the correct geometry: .su2 mesh files.
        2. For each .su2 file create a .cfg configuration file.
        3. Run each .cfg file in SU2_CFD.
        4. Retrieve force files results in configuration directory.
    """

    if isinstance(geometry, CPACS):
        cpacs: CPACS = geometry
    else:
        raise NotImplementedError("DEAL WITH STP")

    # Define constants
    nb_proc = int(get_value(gui_settings.tixi, SU2_NB_CPU_XPATH))
    config_file_type = str(get_value(gui_settings.tixi, SU2_CONFIG_RANS_XPATH))
    rans: bool = config_file_type == "RANS"
    symmetric_mesh = str(get_value(gui_settings.tixi, GMSH_SYMMETRY_XPATH))

    # 1. Load .su2 mesh files
    (
        su2_mesh_paths,
        dynstab_su2_mesh_paths,
    ) = load_su2_mesh_paths(gui_settings.tixi, results_dir)

    # Load only 1 mesh file for the su2 markers
    # Accross all different meshes for the same aircraft,
    # the markers will remain the same.
    mesh_markers = define_markers(gui_settings.tixi, su2_mesh_paths[0])

    # 2. Create configuration files
    if get_value(gui_settings.tixi, SU2_DYNAMICDERIVATIVES_BOOL_XPATH):
        log.info("----- Generating Dynamic Stability ConfigFile -----")

        generate_su2_cfd_config(
            cpacs=cpacs,
            gui_settings=gui_settings,
            wkdir=results_dir,
            su2_mesh_paths=dynstab_su2_mesh_paths,
            mesh_markers=mesh_markers,
            dyn_stab=True,
            rans=rans,
        )

    log.info(f"----- Generating {config_file_type} ConfigFile -----")
    generate_su2_cfd_config(
        cpacs=cpacs,
        gui_settings=gui_settings,
        wkdir=results_dir,
        su2_mesh_paths=su2_mesh_paths,
        mesh_markers=mesh_markers,
        dyn_stab=False,
        rans=rans,
        symmetry=symmetric_mesh,
    )

    # 3. Run each configuration file in SU2
    log.info(f"----- Running  {config_file_type} simulations -----")
    run_SU2_multi(
        wkdir=results_dir,
        nb_proc=nb_proc,
    )

    # 4. Retrieve SU2 results
    log.info("----- Updating CPACS and accessing results -----")
    get_su2_results(
        geometry=geometry,  # Update Aeromap
        results_dir=results_dir,
        gui_settings=gui_settings,
    )
