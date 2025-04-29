"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import streamlit as st

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.SU2Run.su2run import run_SU2_multi
from ceasiompy.PyAVL.func.results import get_avl_results
from ceasiompy.SU2Run.func.results import get_su2_results
from ceasiompy.SMTrain.func.config import retrieve_aeromap_data
from ceasiompy.utils.ceasiompyutils import (
    update_cpacs_from_specs,
    get_results_directory,
)
from ceasiompy.SU2Run.func.config import generate_su2_cfd_config
from cpacspy.cpacsfunctions import (
    add_value,
    get_value,
)
from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock

from ceasiompy import log
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.utils.commonxpath import (
    SU2_AEROMAP_UID_XPATH,
    SU2_CONFIG_RANS_XPATH,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def launch_avl(
    cpacs: CPACS,
    lh_sampling_path: Path,
    objective: str,
) -> DataFrame:
    """
    Executes AVL aerodynamic analysis running PyAVL Module

    This function processes a CPACS file, integrates a new aeromap from a previously
    generated dataset, and runs PyAVL module to compute aerodynamic coefficients.

    Args:
        result_dir (str): Directory where AVL results and intermediate files are stored.
        cpacs_path (str): Path to the CPACS XML file.
        objective (str): The aerodynamic coefficient to extract from the AVL results.
            Expected values: ["cl", "cd", "cs", "cmd", "cml", "cms"].

    Returns:
        DataFrame: Contains AVL results for the requested objective.
    """
    tixi = cpacs.tixi
    if not lh_sampling_path.is_file():
        raise FileNotFoundError(f"LHS dataset not found: {lh_sampling_path}")

    # Remove existing aeromap if present
    if tixi.uIDCheckExists("lh_sampling_dataset"):
        cpacs.delete_aeromap("lh_sampling_dataset")

    # Create and save new aeromap from LHS dataset
    aeromap = cpacs.create_aeromap_from_csv(lh_sampling_path)
    aeromap.save()

    # Update CPACS with the new aeromap
    add_value(tixi, AVL_AEROMAP_UID_XPATH, aeromap.uid)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    # Run AVL analysis
    st.session_state = MagicMock()
    update_cpacs_from_specs(cpacs, PYAVL_NAME)
    results_dir = get_results_directory(PYAVL_NAME)
    run_avl(cpacs, results_dir)
    get_avl_results(cpacs, results_dir)

    log.info(f"----- End of {PYAVL_NAME} -----")

    # Reload CPACS file with updated AVL results
    cpacs = CPACS(cpacs.cpacs_file)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    log.info(f"AVL results extracted for {objective}:")
    log.info(dataset)

    return dataset


def launch_su2(
    cpacs: CPACS,
    results_dir: Path,
    results_dir_su2: Path,
    objective: str,
    high_variance_points=None,  # TODO: For sure there is an issue with this argument
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """

    tixi = cpacs.tixi

    # Select dataset based on high-variance points or LHS sampling
    if high_variance_points is None:
        dataset_path = os.path.join(results_dir, "lh_sampling_dataset.csv")
        aeromap_uid = "lh_sampling_dataset"
    else:
        dataset_path = os.path.join(results_dir, "new_points.csv")
        aeromap_uid = "new_points"

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Remove existing aeromap if present
    if tixi.uIDCheckExists(aeromap_uid):
        cpacs.delete_aeromap(aeromap_uid)

    # Create and save new aeromap from the dataset
    aeromap = cpacs.create_aeromap_from_csv(dataset_path)
    if not aeromap:
        raise ValueError(f"Failed to create aeromap '{aeromap_uid}'.")

    aeromap.save()

    add_value(cpacs.tixi, SU2_AEROMAP_UID_XPATH, aeromap.uid)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    log.info(f"Selected aeromap: {aeromap_uid}")

    # Determine SU2 configuration
    cpacs = CPACS(cpacs.cpacs_file)
    # iterations = get_value_or_default(cpacs.tixi, SU2_MAX_ITER_XPATH, 2)
    # nb_proc = get_value_or_default(cpacs.tixi, SU2_NB_CPU_XPATH, get_reasonable_nb_cpu())
    config_file_type = get_value(tixi, SU2_CONFIG_RANS_XPATH)

    # Load default parameters
    st.session_state = MagicMock()
    update_cpacs_from_specs(cpacs, SU2RUN_NAME)

    rans = (config_file_type == "RANS")
    generate_su2_cfd_config(
        cpacs=cpacs,
        wkdir=results_dir_su2,
        su2_mesh_paths=[],
        mesh_markers=[],
        rans=rans,
        dyn_stab=False,
    )

    # Execute SU2 simulation
    run_SU2_multi(results_dir_su2)
    get_su2_results(cpacs, results_dir_su2)

    log.info("----- End of " + "SU2Run" + " -----")

    # Reload CPACS with updated results
    cpacs = CPACS(cpacs.cpacs_file)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs, overwrite=True)

    log.info(f"SU2 results extracted for {objective}:")
    log.info(dataset)

    return dataset
