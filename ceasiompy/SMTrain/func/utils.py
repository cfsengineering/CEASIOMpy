"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Improve loop and AVL and SU2 settings
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import streamlit as st

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.SU2Run.su2run import run_SU2_multi
from sklearn.model_selection import train_test_split
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
from numpy import ndarray
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock
from typing import Dict

from ceasiompy import log
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.utils.commonxpath import (
    SU2_AEROMAP_UID_XPATH,
    SU2_CONFIG_RANS_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_val_fraction(train_fraction: float) -> float:
    if not (0 < train_fraction < 1):
        log.warning(
            f"Invalid data_repartition value: {train_fraction}."
            "It should be between 0 and 1."
        )
        train_fraction = max(0.1, min(train_fraction, 0.9))

    # Convert from "% of train" to "% of test"
    test_val_fraction = 1 - train_fraction
    return test_val_fraction


def split_data(
    fidelity_datasets: Dict,
    train_fraction: float = 0.7,
    test_fraction_within_split: float = 0.3,
    random_state: int = 42,
) -> Dict[str, ndarray]:
    """
    Takes a dictionary of datasets with different fidelity levels and:
    1. identifies the highest fidelity dataset,
    2. splits it into training, validation, and test sets based on the specified proportions.

    Args:
        datasets (Dict): Keys represent fidelity levels with (x, y) values.
        data_repartition (float = 0.3):
            Fraction of data reserved for validation and test sets, for example:
            data_repartition=0.3 means 70% train, 15% val, 15% test
        val_test_size (float = 0.3):
            Proportion of validation+test data allocated to the test set.
        random_state (int, optional): Random seed for reproducibility.

    Returns:
        Dictionary containing the split datasets.
    """

    if not fidelity_datasets:
        raise ValueError("Datasets dictionary is empty.")

    test_val_fraction = get_val_fraction(train_fraction)

    try:
        highest_fidelity_level = max(fidelity_datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    except (ValueError, IndexError):
        raise ValueError(
            "Dataset keys are not in expected format (e.g., 'fidelity_1', 'fidelity_2')."
        )

    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    try:
        # Extract X and y from the highest fidelity level dataset
        x: ndarray = fidelity_datasets[highest_fidelity_level][0]
        y: ndarray = fidelity_datasets[highest_fidelity_level][1]
        if x.shape[0] != y.shape[0]:
            raise ValueError(
                "Mismatch between number of samples"
                f"x has {x.shape[0]} samples, but y has {y.shape[0]}."
            )
    except KeyError:
        raise ValueError(f"Dataset '{highest_fidelity_level}' is incorrectly formatted.")

    log.info(f"Dataset shape - x: {x.shape}, y: {y.shape}")

    # Split into train and test/validation
    x_train: ndarray
    x_test: ndarray
    y_train: ndarray
    y_test: ndarray
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_val_fraction, random_state=random_state
    )

    if x_test.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with {train_fraction=}"
            f"At least 1 samples is needed for test: avaiable {x_test.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Train size: {x_train.shape[0]}, Test+Validation size: {x_test.shape[0]}")

    # Split into validation and test
    x_val: ndarray
    y_val: ndarray
    x_val, x_test, y_val, y_test = train_test_split(
        x_test, y_test, test_size=test_fraction_within_split, random_state=random_state
    )

    log.info(f"Validation size: {x_val.shape[0]}, Test size: {x_test.shape[0]}")

    return {
        "x_train": x_train, "x_val": x_val, "x_test": x_test,
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
    }


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
    results_dir = get_results_directory(PYAVL_NAME)
    update_cpacs_from_specs(cpacs, PYAVL_NAME)
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


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
