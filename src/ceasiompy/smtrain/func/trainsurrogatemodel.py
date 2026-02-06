"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.
"""

# Imports
import time
import numpy as np
import pandas as pd

from shutil import copyfile
from skopt import gp_minimize
from ceasiompy.utils.commonpaths import get_wkdir
from ceasiompy.pyavl.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.staticstability.staticstability import main as run_staticstability
from ceasiompy.smtrain.func.hyperparameters import (
    get_hyperparam_space_rbf,
    get_hyperparam_space_kriging,
)
from ceasiompy.smtrain.func.loss import (
    compute_rbf_loss,
    compute_kriging_loss,
)
from ceasiompy.smtrain.func.sampling import (
    split_data,
    new_points_rbf,
    get_high_variance_points,
)
from ceasiompy.smtrain.func.createdata import (
    launch_gmsh_su2_geom,
)
from ceasiompy.smtrain.func.utils import (
    log_params_krg,
    log_params_rbf,
)
from ceasiompy.smtrain.func.config import (
    retrieve_aeromap_data,
    get_xpath_for_param,
    update_geometry_cpacs,
    save_best_surrogate_geometry,
    normalize_dataset,
)
from pathlib import Path
from numpy import ndarray
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

def krg_training(
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
        arrays=[data.x_val for data in data_split],
        axis=0,
    )
    y_val = np.concatenate(
        arrays=[data.y_val for data in data_split],
        axis=0,
    )
    x_test = np.concatenate(
        arrays=[data.x_test for data in data_split],
        axis=0,
    )
    y_test = np.concatenate(
        arrays=[data.y_test for data in data_split],
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
    low_fidelity_dir: Path,
    training_settings: TrainingSettings,
) -> DataFrame:
    """
    Run surrogate model training on first level of fidelity (AVL).
    """
    # Define variables
    # Loop through CPACS files
    final_dfs = []

    for i, cpacs in enumerate(cpacs_list):
        pyavl_local_dir = low_fidelity_dir / f"{PYAVL}_{i + 1}"
        pyavl_local_dir.mkdir(exist_ok=True)

        try:
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
                objective=training_settings.objective,
            )

            if level1_df is None or len(level1_df) == 0:
                log.error(f"No data retrieved for simulation {i + 1}, skipping...")
                continue

            # Duplicate per AeroMap entries (same geometry, different aeromap values)
            n = len(level1_df)
            row_df_geom = lh_sampling.iloc[i]
            local_df_geom = DataFrame([row_df_geom] * n).reset_index(drop=True)

            level1_df_combined = pd.concat(
                objs=[local_df_geom, level1_df.reset_index(drop=True)],
                axis=1,
            )
            final_dfs.append(level1_df_combined)

        except Exception as e:
            log.error(f"Error in AVL simulation {i + 1}: {e=}. Skipping this simulation...")
            continue  # Skip to next iteration, don't add to final_dfs

    # Check if any successful simulations
    if not final_dfs:
        raise ValueError(
            "No successful AVL simulations. Cannot proceed with surrogate model training."
        )

    return pd.concat(final_dfs, axis=0, ignore_index=True)


def run_adapt_refinement_geom(
    cpacs: CPACS,
    unvalid_pts: DataFrame,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    """
    Iterative improvement using SU2 data.
    """

    # Define Variables
    log.info(f"Starting adaptive refinement on {len(unvalid_pts)} points.")

    cpacs_name = cpacs.ac_name
    generated_cpacs_dir = results_dir / "generated_cpacs"
    if not generated_cpacs_dir.is_dir():
        generated_cpacs_dir = results_dir.parent / "generated_cpacs"

    level2_rows = []
    for i, high_var in enumerate(unvalid_pts.iterrows()):
        idx = int(high_var[0])
        cpacs_path = generated_cpacs_dir / f"{cpacs_name}_{idx + 1:03d}.xml"
        cpacs = CPACS(cpacs_path)

        high_fidelity_dir = results_dir / f"{SU2RUN}_{i + 1}"
        high_fidelity_dir.mkdir(exist_ok=True)

        obj_value = launch_gmsh_su2_geom(
            cpacs=cpacs,
            results_dir=high_fidelity_dir,
            training_settings=training_settings
        )

        # Essentially these new level2_df creates a new (high-fidelity dataframe)
        new_row = high_var[1].copy()  # Series of input vars
        new_row[training_settings.objective] = obj_value
        level2_rows.append(new_row)

    return DataFrame(level2_rows).reset_index(drop=True)


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


def rbf_training(
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
        arrays=[data.x_val for data in data_split],
        axis=0,
    )
    y_val = np.concatenate(
        arrays=[data.y_val for data in data_split],
        axis=0,
    )
    x_test = np.concatenate(
        arrays=[data.x_test for data in data_split],
        axis=0,
    )
    y_test = np.concatenate(
        arrays=[data.y_test for data in data_split],
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


def run_adapt_refinement_geom_rbf(
    cpacs: CPACS,
    results_dir: Path,
    model: KRG | MFK,
    level1_sets: dict[str, ndarray],
    rmse_obj: float,
    objective: str,
    aeromap_uid: str,
    ranges_gui: DataFrame,
) -> None:
    """
    Iterative adaptive refinement using RBF LOO-error based sampling.
    """
    df_simulation_path = (
        get_wkdir()
        / "Results"
        / get_results_directory("SMTrain")
        / "Low_Fidelity"
        / "avl_simulations_results.csv"
    )
    normalization_params, _ = normalize_dataset(df_simulation_path)
    poor_pts = []
    rmse = float("inf")

    df_simulation = pd.read_csv(df_simulation_path)
    df = pd.DataFrame(columns=df_simulation.columns)

    n_params = len(df_simulation.columns.drop(objective))

    x_array = level1_sets["x_train"]
    y_array = level1_sets["y_train"]
    nb_iters = len(x_array)

    log.info(f"Starting RBF adaptive refinement with maximum {nb_iters=}.")

    high_fidelity_dir_RBF = results_dir / "High_Fidelity_Results_RBF"
    high_fidelity_dir_RBF.mkdir(exist_ok=True)

    for it in range(nb_iters):

        log.info(f"=== Iteration {it} ===")

        # Generate new points
        new_point_df_norm = new_points_rbf(
            x_array=x_array,
            y_array=y_array,
            model=model,
            ranges_gui=ranges_gui,
            n_local=1,
            perturb_scale=1,
        )

        if new_point_df_norm is None or new_point_df_norm.empty:
            log.warning("No new poor-prediction points found.")
            break

        new_point_df = new_point_df_norm.copy()

        for col in new_point_df.columns:
            if col not in normalization_params:
                log.warning(f"No normalization params for {col}, skipping denorm.")
                continue

            mean = normalization_params[col]["mean"]
            std = normalization_params[col]["std"]

            new_point_df[col] = new_point_df[col] * std + mean

        log.info(
            f"Generated {len(new_point_df)} new points "
            f"(norm range [{new_point_df_norm.min().min():.3f}, "
            f"{new_point_df_norm.max().max():.3f}], "
            f"phys range [{new_point_df.min().min():.3f}, "
            f"{new_point_df.max().max():.3f}])"
        )

        poor_pts.extend(new_point_df.to_numpy().tolist())
        cpacs_file = cpacs.cpacs_file
        cpacs_list = []

        SU2_local_dir = high_fidelity_dir_RBF / SU2RUN
        SU2_local_dir.mkdir(exist_ok=True)

        # Update CPACS for each new point
        for i, geom_row in new_point_df.iterrows():

            cpacs_p = SU2_local_dir / f"CPACS_newpoint_{i+1:03d}_iter{it}.xml"
            copyfile(cpacs_file, cpacs_p)

            cpacs_out_obj = CPACS(cpacs_p)
            tixi = cpacs_out_obj.tixi

            params_to_update = {}

            for col in new_point_df.columns:
                col_parts = col.split("_of_")
                if len(col_parts) != 3:
                    log.warning(f"Skipping unexpected param name format: {col}")
                    continue
                name_parameter, section_uid, wing_uid = col_parts
                val = geom_row[col]

                xpath = get_xpath_for_param(tixi, name_parameter, wing_uid, section_uid)

                if name_parameter not in params_to_update:
                    params_to_update[name_parameter] = {"values": [], "xpath": []}

                params_to_update[name_parameter]["values"].append(val)
                params_to_update[name_parameter]["xpath"].append(xpath)

            cpacs_obj = update_geometry_cpacs(cpacs_file, cpacs_p, params_to_update)
            cpacs_list.append(cpacs_obj)

        # Run SU2 on new points
        new_df_list = []
        for idx, cpacs_ in enumerate(cpacs_list):

            obj_value = launch_gmsh_su2_geom(
                cpacs=cpacs_,
                results_dir=high_fidelity_dir_RBF,
                objective=objective,
                aeromap_uid=aeromap_uid,
                idx=idx,
                it=it,
            )

            new_row = new_point_df.iloc[idx].copy()
            new_row[objective] = obj_value
            new_df_list.append(new_row)

        new_df = pd.DataFrame(new_df_list)
        df_new = pd.concat([df, new_df], ignore_index=True, sort=False)

        # Retrain surrogate
        model, rmse = rbf_training(
            n_params=n_params,
            level1_sets=level1_sets,
            level2_sets=split_data(df_new, objective),
        )
        log.info(f"Iteration {it}: RMSE = {rmse:.6e}")

        # Breaking conditions
        if rmse > rmse_obj:
            log.info("Target RMSE reached. Stopping refinement.")
            rmse_df = pd.DataFrame({"rmse": [rmse]})
            rmse_path = f"{results_dir}/rmse_RBF.csv"
            rmse_df.to_csv(rmse_path, index=False)

            model_name = "RBF"
            param_order = [col for col in df.columns if col != objective]

            save_best_surrogate_geometry(
                surrogate_model=model,
                model_name=model_name,
                objective=objective,
                param_order=param_order,
                normalization_params=normalization_params,
                final_level1_df_c=df_new,
                results_dir=results_dir,
            )
            break