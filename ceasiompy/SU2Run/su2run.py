"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2018-11-06
| Modified: Leon Deligny
| Date: 24-Feb-2025

TODO:
    * Check platform with -> sys.platform

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.SU2Run.func.results import get_su2_results
from ceasiompy.SU2Run.func.runconfigfiles import run_SU2_multi

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    check_nb_cpu,
)

from ceasiompy.SU2Run.func.config import (
    define_markers,
    load_su2_mesh_paths,
    generate_su2_cfd_config,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log

from ceasiompy.utils.commonxpath import (
    SU2_NB_CPU_XPATH,
    SU2_CONFIG_RANS_XPATH,
    SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
)


from ceasiompy.SU2Run import MODULE_NAME

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    SU2Run module is decomposed into 4 parts.

        1. Retrieve the correct .su2 mesh files to run in SU2 software.
        2. For each .su2 file create a .cfg configuration for SU2.
        3. Run each .cfg file in SU2.
        4. Retrieve SU2 results.

    Args:
        cpacs (CPACS): Input CPACS file.
        wkdir (Path): Results directory (where to store the results).

    Raises:
        ValueError: If .su2 mesh files are not found.

    """

    # Define variable
    tixi = cpacs.tixi

    # Define constants
    nb_proc = get_value(tixi, SU2_NB_CPU_XPATH)
    config_file_type = get_value(tixi, SU2_CONFIG_RANS_XPATH)
    rans = (config_file_type == "RANS")

    #
    # Check that the number of used CPUs is correct
    check_nb_cpu(nb_proc)

    # 1. Load .su2 mesh files
    su2_mesh_paths, dynstab_su2_mesh_paths = load_su2_mesh_paths(tixi, wkdir)
    if not su2_mesh_paths:
        raise ValueError("List of su2 mesh paths is empty.")
    if not dynstab_su2_mesh_paths:
        raise ValueError("List of Dynamic Stability su2 mesh paths is empty.")

    mesh_markers = define_markers(tixi, su2_mesh_paths[0])

    # 2. Create configuration files
    if get_value(tixi, SU2_DYNAMICDERIVATIVES_BOOL_XPATH):
        log.info("----- Generating Dynamic Stability ConfigFile -----")

        generate_su2_cfd_config(
            cpacs=cpacs,
            wkdir=wkdir,
            su2_mesh_paths=dynstab_su2_mesh_paths,
            mesh_markers=mesh_markers,
            dyn_stab=True,
            rans=rans,
        )

    log.info(f"----- Generating {config_file_type} ConfigFile -----")
    generate_su2_cfd_config(
        cpacs=cpacs,
        wkdir=wkdir,
        su2_mesh_paths=su2_mesh_paths,
        mesh_markers=mesh_markers,
        dyn_stab=False,
        rans=rans,
    )

    # 3. Run each configuration file in SU2
    log.info(f"----- Running  {config_file_type} simulations -----")
    run_SU2_multi(wkdir, nb_proc)

    # 4. Retrieve SU2 results
    log.info("----- Updating CPACS and accessing results -----")
    get_su2_results(cpacs, wkdir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
