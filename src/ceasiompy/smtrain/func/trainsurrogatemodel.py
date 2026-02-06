"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.
"""

# Imports
import time
import joblib
import numpy as np
import pandas as pd

from pandas import concat
from shutil import copyfile
from skopt import gp_minimize
from sklearn.metrics import r2_score
from smt.utils.misc import compute_rmse
from ceasiompy.utils.commonpaths import get_wkdir
from ceasiompy.pyavl.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.staticstability.staticstability import main as run_staticstability
from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)
from ceasiompy.smtrain.func.loss import (
    compute_rbf_loss,
    compute_kriging_loss,
)
from ceasiompy.smtrain.func.sampling import (
    split_data,
    new_points,
    new_points_rbf,
    get_high_variance_points,
)
from ceasiompy.smtrain.func.createdata import (
    launch_avl,
    launch_su2,
    launch_gmsh_su2_geom,
)
from ceasiompy.smtrain.func.utils import (
    log_params_krg,
    log_params_rbf,
    unpack_data,
    get_model_typename,
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
from skopt.space import (
    Real,
    Categorical,
)

from ceasiompy import log
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.utils.commonxpaths import SM_XPATH
from ceasiompy.utils.commonpaths import WKDIR_PATH
from ceasiompy.su2run import MODULE_NAME as SU2RUN


# Functions

def get_hyperparam_space_kriging(
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
) -> list[str]:
    """
    Get Hyper-parameters space from the different fidelity datasets.
    Uniquely determined by the training set x_train.
    """

    # Concatenate only non-None arrays
    arrays = [level1_split.x_train]
    if level2_split is not None:
        arrays.append(level2_split.x_train)
    if level3_split is not None:
        arrays.append(level3_split.x_train)

    x_train = np.concatenate(arrays, axis=0)
    n_samples, n_features = x_train.shape

    # Determine allowed polynomial regression types based on sample count
    if n_samples > ((n_features + 1) * (n_features + 2) / 2):
        poly_options = ["constant", "linear", "quadratic"]
        x = (n_features + 1) * (n_features + 2) / 2
        log.info(f"Training points (n_samples): {x}<{n_samples} -> poly_options: {poly_options}")
    elif n_samples > (n_features + 2):
        poly_options = ["constant", "linear"]
        x = (n_features + 1) * (n_features + 2) / 2
        y = n_features + 2
        log.info(
            f"Training points (n_samples): {y}<{n_samples}<={x} -> poly_options: {poly_options}"
        )
    elif n_samples > 2:
        poly_options = ["constant"]
        y = n_features + 2
        log.info(f"Training points (n_samples): {n_samples}<={y} -> poly_options: {poly_options}")
    else:
        raise Warning(
            f"Number of training points must be greater than 2, current size: {n_samples}"
        )

    return [
        Real(0.0001, 10, name="theta0"),
        Categorical(["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"),
        Categorical(poly_options, name="poly"),
        Categorical(["Cobyla", "TNC"], name="opt"),
        Real(1e-12, 1e-4, name="nugget"),
        Categorical(poly_options, name="rho_regr"),
        Real(0.1, 1, name="lambda_penalty"),
    ]


def save_model(
    model: KRG | MFK | RBF,
    columns: list[str],
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    """
    Save trained surrogate model.
    """
    suffix = get_model_typename(model)
    model_path = results_dir / f"sm_{suffix}.pkl"

    with open(model_path, "wb") as file:
        joblib.dump(
            value={
                "model": model,
                "columns": columns,
                "objective": training_settings.objective,
            },
            filename=file,
        )
    log.info(f"Model saved to {model_path}")


def kriging_training(
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


def run_adaptative_refinement(
    cpacs: CPACS,
    results_dir: Path,
    model: KRG | MFK,
    level1_sets: dict[str, ndarray],
    rmse_obj: float,
    objective: str,
) -> None:
    """
    Iterative improvement using SU2 data.
    """
    high_var_pts = []
    rmse = float("inf")
    df = DataFrame({
        "altitude": [],
        "machNumber": [],
        "angleOfAttack": [],
        "angleOfSideslip": [],
        objective: [],
    })

    x_array = level1_sets["x_train"]
    nb_iters = len(x_array)
    log.info(f"Starting adaptive refinement with maximum {nb_iters=}.")

    for _ in range(nb_iters):
        # Find new high variance points based on inputs x_train
        new_point_df = new_points(
            x_array=x_array,
            model=model,
            results_dir=results_dir,
            high_var_pts=high_var_pts,
        )

        # 1st Breaking condition
        if new_point_df.empty or (new_point_df is None):
            log.warning("No new high-variance points found.")
            break
        high_var_pts.append(new_point_df.values[0])

        # Get data from SU2 at the high variance points
        new_df = launch_su2(
            cpacs=cpacs,
            results_dir=results_dir,
            objective=objective,
            high_variance_points=high_var_pts,
        )

        # Stack new with old
        df = concat([new_df, df], ignore_index=True)

        model, rmse = train_surrogate_model(
            level1_sets=level1_sets,
            level2_sets=split_data(df, objective),
        )

        # 2nd Breaking condition
        if rmse > rmse_obj:
            break


def run_adapt_refinement_geom_krg(
    cpacs: CPACS,
    model: KRG | MFK,
    level1_df: DataFrame,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    """
    Iterative improvement using SU2 data.
    """

    # Define Variables
    high_var_pts = []
    nb_iters = len(level1_df)
    log.info(f"Starting adaptive refinement with maximum {nb_iters=}.")

    level1_df_norm = normalize_dataset(level1_df)

    high_var_pts: DataFrame = get_high_variance_points(
        model=model,
        level1_df_norm=level1_df_norm,
        training_settings=training_settings,
    )

    cpacs_name = cpacs.ac_name
    generated_cpacs_dir = results_dir / "generated_cpacs"
    if not generated_cpacs_dir.is_dir():
        generated_cpacs_dir = results_dir.parent / "generated_cpacs"

    for i, high_var in enumerate(high_var_pts.iterrows()):
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


def training_existing_db(
    results_dir: Path,
    split_ratio: float,
    KRG_model_bool: bool,
    RBF_model_bool: bool
):
    simulation_csv_path = WKDIR_PATH / 'avl_simulations_results.csv'
    df_new_path = results_dir / "avl_simulations_results.csv"
    copyfile(simulation_csv_path, df_new_path)
    df1 = pd.read_csv(df_new_path)
    objective = df1.columns[-1]
    best_geometry_idx = df1[objective].idxmax()
    best_geometries_df = df1.loc[[best_geometry_idx]]
    best_geometries_df.to_csv(results_dir / "best_geometric_configurations.csv", index=False)

    n_params = df1.columns.drop(objective).size

    normalization_params, df_norm = normalize_dataset(df_new_path)

    krg_model = None
    krg_rmse = None
    rbf_model = None
    rbf_rmse = None
    level1_sets = split_data(df_norm, objective, split_ratio)
    param_order = [col for col in df_norm.columns if col != objective]

    if KRG_model_bool:
        log.info("\n\n")
        log.info("--------------Star training KRG model.--------------\n")
        krg_model, krg_rmse = train_surrogate_model(level1_sets)
        rmse_df = pd.DataFrame({"rmse": [krg_rmse]})
        rmse_path = f"{results_dir}/rmse_KRG.csv"
        rmse_df.to_csv(rmse_path, index=False)
        log.info("--------------KRG model trained.--------------\n")
        model_name = "RBF"
        save_best_surrogate_geometry(
            surrogate_model=rbf_model,
            model_name=model_name,
            objective=objective,
            param_order=param_order,
            normalization_params=normalization_params,
            final_level1_df_c=df1,
            results_dir=results_dir,
        )

    if RBF_model_bool:
        log.info("\n\n")
        log.info("--------------Star training RBF model.--------------\n")
        rbf_model, rbf_rmse = rbf_training(n_params, level1_sets)
        rmse_df = pd.DataFrame({"rmse": [rbf_rmse]})
        rmse_path = f"{results_dir}/rmse_RBF.csv"
        rmse_df.to_csv(rmse_path, index=False)
        log.info("--------------RBF model trained.--------------\n")
        model_name = "RBF"
        save_best_surrogate_geometry(
            surrogate_model=rbf_model,
            model_name=model_name,
            objective=objective,
            param_order=param_order,
            normalization_params=normalization_params,
            final_level1_df_c=df1,
            results_dir=results_dir,
        )

    return krg_model, rbf_model, level1_sets, param_order


def run_adapt_refinement_geom_krg_existing_db(
    cpacs: CPACS,
    results_dir: Path,
    model: KRG | MFK | RBF,
    level1_sets: dict[str, ndarray],
    rmse_obj: float,
    objective: str,
    aeromap_uid: str,
    ranges_gui: DataFrame,
) -> None:
    """
    Iterative improvement using SU2 data.
    """
    high_var_pts = []
    rmse = float("inf")
    df_old_simulation_path = WKDIR_PATH / 'avl_simulations_results.csv'
    df_new_simulation_path = results_dir / 'avl_simulations_results.csv'
    copyfile(df_old_simulation_path, df_new_simulation_path)
    df_simulation_new = pd.read_csv(df_new_simulation_path)
    df_simulation = pd.DataFrame(columns=df_simulation_new.columns)

    x_array = level1_sets["x_train"]
    nb_iters = len(x_array)
    log.info(f"Starting adaptive refinement with maximum {nb_iters=}.")

    normalization_params, _ = normalize_dataset(df_new_simulation_path)

    cpacs_list = []

    for it in range(nb_iters):
        # Find new high variance points based on inputs x_train
        new_point_df = new_points_geom(
            x_array=x_array,
            model=model,
            results_dir=results_dir,
            high_var_pts=high_var_pts,
            ranges_gui=ranges_gui,
        )

        # 1st Breaking condition
        if new_point_df is None:
            log.warning("No new high-variance points found.")
            break
        elif new_point_df.empty:
            log.warning("No new high-variance points found.")
            break
        high_var_pts.append(new_point_df.values[0])

        cpacs_file = cpacs.cpacs_file

        for i, geom_row in new_point_df.iterrows():

            cpacs_p = SU2RUN / f"CPACS_newpoint_{i+1:03d}_iter{it}.xml"
            copyfile(cpacs_file, cpacs_p)
            cpacs_out_obj = CPACS(cpacs_p)
            tixi = cpacs_out_obj.tixi
            params_to_update = {}
            for col in new_point_df.columns:
                # SINTAX: {comp}_of_{section}_of_{param}
                col_parts = col.split('_of_')
                wing_uid = col_parts[2]
                section_uid = col_parts[1]
                name_parameter = col_parts[0]
                val = geom_row[col]

                xpath = get_xpath_for_param(tixi, name_parameter, wing_uid, section_uid)

                if name_parameter not in params_to_update:
                    params_to_update[name_parameter] = {'values': [], 'xpath': []}

                params_to_update[name_parameter]['values'].append(val)
                params_to_update[name_parameter]['xpath'].append(xpath)
            # Update CPACS file
            cpacs_obj = update_geometry_cpacs(cpacs_file, cpacs_p, params_to_update)
            cpacs_list.append(cpacs_obj)
            # Get data from SU2 at the high variance points
        new_df_list = []
        for idx, cpacs_ in enumerate(cpacs_list):

            dir_res = SU2RUN / f"{SU2RUN}_{idx}_iter{it}"
            dir_res.mkdir(exist_ok=True)
            obj_value = launch_gmsh_su2_geom(
                cpacs=cpacs_,
                results_dir=dir_res,
                objective=objective,
                aeromap_uid=aeromap_uid,
                idx=idx,
                it=it,
            )
            new_row = new_point_df.iloc[idx].copy()
            new_row[objective] = obj_value
            new_df_list.append(new_row)

        new_df = pd.DataFrame(new_df_list)
        df = pd.concat([new_df, df_simulation], ignore_index=True)

        model, rmse = train_surrogate_model(
            level1_sets=level1_sets,
            level2_sets=split_data(df, objective),
        )

        model_name = "KRG"
        param_order = [col for col in df_simulation.columns if col != objective]
        save_best_surrogate_geometry(
            surrogate_model=model,
            model_name=model_name,
            objective=objective,
            param_order=param_order,
            normalization_params=normalization_params,
            final_level1_df_c=df,
            results_dir=results_dir,
        )

        cpacs_list.clear()

        # 2nd Breaking condition
        if rmse > rmse_obj:
            rmse_df = pd.DataFrame({"rmse": [rmse]})
            rmse_path = f"{results_dir}/rmse_model.csv"
            rmse_df.to_csv(rmse_path, index=False)
            break

# -------- RBF ----------


def get_hyperparam_space_rbf(
    level1_sets: dict[str, ndarray],
    level2_sets: dict[str, ndarray] | None,
    level3_sets: dict[str, ndarray] | None,
    n_params: int,
) -> list:
    """
    Get Hyper-parameters space
    Uniquely determined by the training set x_train.
    """
    arrays = [level1_sets["x_train"]]
    if level2_sets is not None:
        arrays.append(level2_sets["x_train"])
    if level3_sets is not None:
        arrays.append(level3_sets["x_train"])

    x_train = np.concatenate(arrays, axis=0)
    n_samples, _ = x_train.shape

    n_sat = 7
    N_eff = min(n_params, n_sat)
    r = n_samples / 3**N_eff

    if 0.8 <= r < 1:
        return [
            Real(1, 25, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    elif 0.3 <= r < 0.8:
        return [
            Real(1, 250, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    elif 0.0 <= r < 0.3:
        return [
            Real(1, 1000, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    else:
        return [
            Real(1, 10, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]


def compute_loss_RBF(
    model: KRG | MFK,
    lambda_penalty: float,
    x_: ndarray,
    y_: ndarray,
) -> float:
    return compute_rmse(model, x_, y_)


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


def optimize_hyper_parameters_RBF(
    objective: Callable,
    param_space,
    n_calls: int,
    random_state: int,
) -> ndarray:
    """Bayesian optimization generica, compatibile con RBF e altri modelli"""
    start_time = time.time()
    result: OptimizeResult = gp_minimize(
        objective, param_space, n_calls=n_calls, random_state=random_state
    )
    total_time = time.time() - start_time
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    log.info("Best hyperparameters found:")
    log_params_RBF(result)
    return result.x


def compute_first_level_loss_RBF(
    params: tuple,
    x_train: ndarray,
    y_train: ndarray,
    x_: ndarray,
    y_: ndarray
):
    d0, poly_degree, reg, lambda_penalty = params + (0.0,)
    model = RBF(
        d0=d0,
        poly_degree=int(poly_degree),
        reg=reg,
        print_global=False
    )
    model.set_training_values(x_train, y_train)
    model.train()
    return model, compute_loss_RBF(model, lambda_penalty, x_, y_)


def rbf_model(
    param_space: list,
    sets: dict[str, ndarray],
    n_calls: int = 50,
    random_state: int = 42
) -> tuple[RBF, float]:
    x_train, x_test, x_val, y_train, y_test, y_val = unpack_data(sets)

    def objective(params) -> float:
        d0, poly_degree, reg = params
        log.info(f"Trying: d0={d0:.2f}, poly={poly_degree}, reg={reg:.2e}")

        model = RBF(
            d0=d0,
            poly_degree=int(poly_degree),
            reg=reg,
            print_global=False
        )
        model.set_training_values(x_train, y_train)
        model.train()
        return compute_rmse(model, x_val, y_val)

    best_params = optimize_hyper_parameters_RBF(objective, param_space, n_calls, random_state)

    # Final model
    x_final = np.vstack([x_train, x_val])
    y_final = np.hstack([y_train, y_val])
    d0, poly_degree, reg = best_params
    best_model = RBF(d0=d0, poly_degree=int(poly_degree), reg=reg, print_global=False)
    best_model.set_training_values(x_final, y_final)
    best_model.train()

    y_pred = best_model.predict_values(x_test)
    log.info(f"y_test:  [{y_test.min():.4f}, {y_test.max():.4f}]")
    log.info(f"y_pred:  [{y_pred.min():.4f}, {y_pred.max():.4f}]")
    log.info(f"R²:      {r2_score(y_test, y_pred):.4f}")

    best_loss = compute_rmse(best_model, x_test, y_test)
    log.info(f"Final first level RMSE on test set: {best_loss:.6f}")
    return best_model, best_loss


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


def train_first_level_sm(
    level1_df: DataFrame,
    low_fidelity_dir: Path,
    training_settings: TrainingSettings,
) -> DataSplit:
    # Unpack
    objective = training_settings.objective
    data_repartition = training_settings.data_repartition

    # Normalize
    level1_df_norm = normalize_dataset(level1_df)

    # Split
    level1_split: DataSplit = split_data(
        df=level1_df_norm,
        objective=objective,
        train_fraction=data_repartition,
    )

    if "KRG" in training_settings.sm_models:
        best_krg_model, best_krg_rmse = kriging_training(level1_split)

        save_best_surrogate_geometry(
            df_norm=level1_df_norm,
            best_rmse=best_krg_rmse,
            best_model=best_krg_model,
            results_dir=low_fidelity_dir,
            training_settings=training_settings,
        )

    if "RBF" in training_settings.sm_models:
        best_rbf_model, best_rbf_rmse = rbf_training(level1_split)

        save_best_surrogate_geometry(
            best_rmse=best_rbf_rmse,
            best_model=best_rbf_model,
            results_dir=low_fidelity_dir,
            training_settings=training_settings,
        )

    return level1_split
