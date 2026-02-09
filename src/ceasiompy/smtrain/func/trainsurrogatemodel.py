"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.
"""

# Imports
import time
import numpy as np
import pandas as pd
import concurrent.futures

from skopt import gp_minimize
from ceasiompy.pyavl.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import get_sane_max_cpu
from ceasiompy.staticstability.staticstability import main as run_staticstability
from ceasiompy.smtrain.func.hyperparameters import (
    get_hyperparam_space_rbf,
    get_hyperparam_space_kriging,
)
from ceasiompy.smtrain.func.loss import (
    compute_rbf_loss,
    compute_kriging_loss,
)
from ceasiompy.smtrain.func.createdata import (
    launch_gmsh_su2,
)
from ceasiompy.smtrain.func.utils import (
    log_params_krg,
    log_params_rbf,
)
from ceasiompy.smtrain.func.config import (
    retrieve_aeromap_data,
)
from pathlib import Path
from typing import Callable
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from smt.applications import MFK
from scipy.optimize import OptimizeResult
from ceasiompy.smtrain.func.utils import DataSplit
from ceasiompy.smtrain.func.config import TrainingSettings
from smt.surrogate_models import (
    KRG,
    RBF,
)

from ceasiompy import log
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.su2run import MODULE_NAME as SU2RUN


# Functions

def get_best_krg_model(
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
    n_calls: int = 10,
    random_state: int = 42,
) -> tuple[KRG | MFK, float]:
    """
    Trains a multi-fidelity kriging model (with 2/3 fidelity levels).
    """
    hyperparam_space = get_hyperparam_space_kriging(
        level1_split=level1_split,
        level2_split=level2_split,
        level3_split=level3_split,
    )

    data_split: list[DataSplit] = [level1_split]
    if level2_split is not None:
        data_split.append(level2_split)
    if level3_split is not None:
        data_split.append(level3_split)

    x_val = np.concatenate(
        [data.x_val for data in data_split],
        axis=0,
    )
    y_val = np.concatenate(
        [data.y_val for data in data_split],
        axis=0,
    )
    x_test = np.concatenate(
        [data.x_test for data in data_split],
        axis=0,
    )
    y_test = np.concatenate(
        [data.y_test for data in data_split],
        axis=0,
    )

    def objective(params) -> float:
        _, loss = compute_kriging_loss(
            params=params,
            level1_split=level1_split,
            level2_split=level2_split,
            level3_split=level3_split,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_result = optimize_hyper_parameters(
        objective=objective,
        n_calls=n_calls,
        random_state=random_state,
        hyperparam_space=hyperparam_space,
    )
    log_params_krg(best_result)

    best_model, best_loss = compute_kriging_loss(
        params=best_result.x,
        level1_split=level1_split,
        level2_split=level2_split,
        level3_split=level3_split,
        x_=x_test,
        y_=y_test,
    )

    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def run_first_level_simulations(
    cpacs_list: list[CPACS],
    lh_sampling: DataFrame,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> DataFrame:
    """
    Run surrogate model training on first level of fidelity (AVL).
    """
    final_dfs = []
    max_workers = min(len(cpacs_list), get_sane_max_cpu())

    if max_workers <= 1:
        for i, cpacs in enumerate(cpacs_list):
            result = _run_first_level_simulation_task(
                cpacs_path=cpacs.cpacs_file,
                row_geom=lh_sampling.iloc[i].to_dict(),
                idx=i,
                results_dir=results_dir,
                objective=training_settings.objective,
            )
            if result is not None:
                final_dfs.append(result)

        # Check if any successful simulations
        if not final_dfs:
            raise ValueError(
                "No successful AVL simulations. Cannot proceed with surrogate model training."
            )
        return pd.concat(final_dfs, axis=0, ignore_index=True)

    log.info(f"Running {len(cpacs_list)} AVL simulations with {max_workers} workers.")

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, cpacs in enumerate(cpacs_list):
            futures.append(
                executor.submit(
                    _run_first_level_simulation_task,
                    cpacs.cpacs_file,
                    lh_sampling.iloc[i].to_dict(),
                    i,
                    results_dir,
                    training_settings.objective,
                )
            )

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                log.error(f"Error in parallel AVL simulation: {e=}. Skipping this simulation...")
                continue
            if result is not None:
                final_dfs.append(result)

    # Check if any successful simulations
    if not final_dfs:
        raise ValueError(
            "No successful AVL simulations. Cannot proceed with surrogate model training."
        )

    return pd.concat(final_dfs, axis=0, ignore_index=True)


def _run_first_level_simulation_task(
    cpacs_path: Path,
    row_geom: dict,
    idx: int,
    results_dir: Path,
    objective: str,
) -> DataFrame | None:
    pyavl_local_dir = results_dir / f"{PYAVL}_{idx + 1}"
    pyavl_local_dir.mkdir(exist_ok=True)

    try:
        cpacs = CPACS(cpacs_path)

        run_avl(
            cpacs=cpacs,
            results_dir=pyavl_local_dir,
        )
        run_staticstability(
            cpacs=cpacs,
            results_dir=pyavl_local_dir,
        )

        # Retrieve AeroMap Selected from GUI
        level1_df = retrieve_aeromap_data(
            cpacs=cpacs,
            objective=objective,
        )

        if level1_df is None or len(level1_df) == 0:
            log.error(f"No data retrieved for simulation {idx + 1}, skipping...")
            return None

        # Duplicate per AeroMap entries (same geometry, different aeromap values)
        n = len(level1_df)
        local_df_geom = DataFrame([row_geom] * n).reset_index(drop=True)

        level1_df_combined = pd.concat(
            objs=[local_df_geom, level1_df.reset_index(drop=True)],
            axis=1,
        )
        return level1_df_combined

    except Exception as e:
        log.error(f"Error in AVL simulation {idx + 1}: {e=}. Skipping this simulation...")
        return None


def run_adapt_refinement_geom(
    cpacs: CPACS,
    unvalid_pts: DataFrame,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> DataFrame:
    """
    Iterative improvement using SU2 data.
    """

    # Define Variables
    log.info(f"Starting adaptive refinement on {len(unvalid_pts)} points.")

    cpacs_name = cpacs.ac_name

    # TODO: Extract correctly from the generated cpacs folder
    generated_cpacs_dir = results_dir / "generated_cpacs"

    final_dfs = []
    for i, high_var in enumerate(unvalid_pts.iterrows()):
        try:
            idx = int(high_var[0])
            cpacs_path = generated_cpacs_dir / f"{cpacs_name}_{idx + 1:03d}.xml"
            cpacs = CPACS(cpacs_path)

            high_fidelity_dir = results_dir / f"{SU2RUN}_{i + 1}"
            high_fidelity_dir.mkdir(exist_ok=True)

            level2_df = launch_gmsh_su2(
                cpacs=cpacs,
                results_dir=high_fidelity_dir,
                training_settings=training_settings
            )

            if level2_df is None or len(level2_df) == 0:
                log.error(f"No data retrieved for simulation {i + 1}, skipping...")
                continue

            # Duplicate per AeroMap entries (same geometry, different aeromap values)
            n = len(level2_df)
            row_df_geom = unvalid_pts.iloc[i]
            local_df_geom = DataFrame([row_df_geom] * n).reset_index(drop=True)

            level1_df_combined = pd.concat(
                objs=[local_df_geom, unvalid_pts.reset_index(drop=True)],
                axis=1,
            )
            final_dfs.append(level1_df_combined)
        except Exception as e:
            log.error(f"Error in SU2 simulation {i + 1}: {e=}. Skipping...")
            continue  # Skip to next iteration, don't add to final_dfs

    # Check if any successful simulations
    if not final_dfs:
        raise ValueError(
            "No successful SU2 simulations. Cannot proceed with surrogate model training."
        )

    return pd.concat(final_dfs, axis=0, ignore_index=True)


def optimize_hyper_parameters(
    objective: Callable,
    n_calls: int,
    random_state: int,
    hyperparam_space,
) -> OptimizeResult:
    """
    Using Bayesian Optimization.
    """
    log.info("Starting Bayesian Optimization Algorithm.")

    # Perform Bayesian optimization
    start_time = time.time()
    result: OptimizeResult = gp_minimize(
        func=objective,
        n_calls=n_calls,
        dimensions=hyperparam_space,
        random_state=random_state,
    )
    total_time = time.time() - start_time
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    log.info("Best hyperparameters found:")
    return result


def get_best_rbf_model(
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
    n_calls: int = 10,
    random_state: int = 42,
) -> tuple[RBF, float]:
    """
    Train either single-fidelity or multi-fidelity RBF model.
    """
    hyperparam_space = get_hyperparam_space_rbf(
        level1_split=level1_split,
        level2_split=level2_split,
        level3_split=level3_split,
    )

    data_split: list[DataSplit] = [level1_split]
    if level2_split is not None:
        data_split.append(level2_split)
    if level3_split is not None:
        data_split.append(level3_split)

    x_val = np.concatenate(
        [data.x_val for data in data_split],
        axis=0,
    )
    y_val = np.concatenate(
        [data.y_val for data in data_split],
        axis=0,
    )
    x_test = np.concatenate(
        [data.x_test for data in data_split],
        axis=0,
    )
    y_test = np.concatenate(
        [data.y_test for data in data_split],
        axis=0,
    )

    # Objective function for Bayesian optimization
    def objective(params) -> float:
        _, loss = compute_rbf_loss(
            params=params,
            level1_split=level1_split,
            level2_split=level2_split,
            level3_split=level3_split,
            x_=x_val,
            y_=y_val,
        )
        return loss

    best_result = optimize_hyper_parameters(
        objective=objective,
        n_calls=n_calls,
        random_state=random_state,
        hyperparam_space=hyperparam_space,
    )
    log_params_rbf(best_result)

    best_model, best_loss = compute_rbf_loss(
        params=best_result.x,
        level1_split=level1_split,
        level2_split=level2_split,
        level3_split=level3_split,
        x_=x_test,
        y_=y_test,
    )

    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss
