"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import time
import joblib
from shutil import copyfile
import numpy as np
import pandas as pd
from pathlib import Path
from pandas import concat
from skopt import gp_minimize
from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)
from ceasiompy.SMTrain.func.loss import (
    compute_first_level_loss,
    compute_multi_level_loss,
)
from ceasiompy.SMTrain.func.sampling import (
    split_data,
    new_points,
    new_points_geom,
    new_points_RBF,
)
from ceasiompy.SMTrain.func.createdata import (
    launch_avl,
    launch_su2,
    launch_gmsh_su2_geom,
)
from ceasiompy.SMTrain.func.utils import (
    log_params,
    unpack_data,
    collect_level_data,
    concatenate_if_not_none,
    define_model_type,
    num_flight_conditions,
    num_geom_params,
    drop_constant_columns,
)
from ceasiompy.SaveAeroCoefficients import (
    AEROMAP_FEATURES,
)

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.StaticStability.staticstability import main as run_staticstability
from ceasiompy.SMTrain.func.config import (
    retrieve_aeromap_data,
    get_xpath_for_param,
    update_geometry_cpacs,
    save_best_surrogate_geometry,
    get_elements_to_optimise,
)
from sklearn.metrics import r2_score
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.SU2Run import (
    MODULE_NAME as SU2RUN_NAME,
)
from ceasiompy.StaticStability import (
    MODULE_NAME as STATICSTABILITY_NAME,
)
from ceasiompy.utils.ceasiompyutils import (
    update_cpacs_from_specs,
    get_results_directory,
    get_aeromap_conditions,
)
import sys
from numpy import ndarray
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from smt.applications import MFK
from smt.surrogate_models import KRG
from smt.surrogate_models import RBF
from smt.utils.misc import compute_rmse
from scipy.optimize import (
    OptimizeResult,
)
from skopt.space import (
    Real,
    Categorical,
)
from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Callable,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SM_XPATH
from ceasiompy.utils.commonpaths import WKDIR_PATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_hyperparam_space(
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None],
    level3_sets: Union[Dict[str, ndarray], None],
) -> List[str]:
    """
    Get Hyper-parameters space from the different fidelity datasets.
    Uniquely determined by the training set x_train.
    """

    # Concatenate only non-None arrays
    arrays = [level1_sets["x_train"]]
    if level2_sets is not None:
        arrays.append(level2_sets["x_train"])
    if level3_sets is not None:
        arrays.append(level3_sets["x_train"])

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

    hyperparam_space = [
        Real(0.0001, 10, name="theta0"),
        Categorical(["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"),
        Categorical(poly_options, name="poly"),
        Categorical(["Cobyla", "TNC"], name="opt"),
        Real(1e-12, 1e-4, name="nugget"),
        Categorical(poly_options, name="rho_regr"),
        Real(0.1, 1, name="lambda_penalty"),
    ]

    return hyperparam_space


def train_surrogate_model(
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None] = None,
    level3_sets: Union[Dict[str, ndarray], None] = None,
):
    """
    Train a surrogate model using kriging or Multi-Fidelity kriging:
    1. selects appropriate polynomial basis functions for regression
    2. defines the hyperparameter space accordingly
    3. trains the model

    Polynomial Selection Logic:
        if training samples > (n_features + 1) * (n_features + 2) / 2
            Use ["constant", "linear", "quadratic"]
        elif training samples > (n_features + 1)
            Use ["constant", "linear"]
        else
            Use ["constant"]

    Returns:
        model: Trained surrogate model (kriging or Multi-Fidelity kriging).
        rmse (float): Root Mean Square Error of the trained model.
    """

    hyperparam_space = get_hyperparam_space(level1_sets, level2_sets, level3_sets)
    if level2_sets is not None or level3_sets is not None:
        # It will always be multi-fidelity level if not 1
        return mf_kriging(
            param_space=hyperparam_space,
            level1_sets=level1_sets,
            level2_sets=level2_sets,
            level3_sets=level3_sets,
        )
    else:
        return kriging(
            param_space=hyperparam_space,
            sets=level1_sets,
        )


def save_model(
    cpacs: CPACS,
    model: Union[KRG, MFK, RBF],
    objective: str,
    results_dir: Path,
    param_order: list[str],
) -> None:
    """
    Save multiple trained surrogate models.

    Args:
        cpacs: CPACS file.
        model: Trained surrogate model.
        coefficient_name (str): Name of the aerodynamic coefficient (e.g., "cl" or "cd").
        results_dir (Path): Where the model will be saved.
    """
    tixi = cpacs.tixi

    suffix = define_model_type(model)

    model_path = results_dir / f"surrogateModel_{suffix}.pkl"

    with open(model_path, "wb") as file:
        joblib.dump(
            value={
                "model": model,
                "coefficient": objective,
                "param_order": param_order,
            },
            filename=file,
        )
    log.info(f"Model saved to {model_path}")

    create_branch(tixi, SM_XPATH)
    add_value(tixi, SM_XPATH, model_path)
    log.info("Finished Saving model.")


def optimize_hyper_parameters(
    objective: Callable,
    param_space,
    n_calls: int,
    random_state: int,
) -> ndarray:
    """
    Using Bayesian Optimization.
    """

    # Perform Bayesian optimization
    start_time = time.time()
    result: OptimizeResult = gp_minimize(
        objective, param_space, n_calls=n_calls, random_state=random_state
    )
    total_time = time.time() - start_time
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    log.info("Best hyperparameters found:")
    log_params(result)

    return result.x


def kriging(
    param_space: List,
    sets: Dict[str, ndarray],
    n_calls: int = 50,
    random_state: int = 42,
) -> Tuple[KRG, float]:
    """
    Trains a kriging model using Bayesian optimization.

    Args:
        param_space (list): Hyper-parameters for Bayesian optimization.
        sets (dict): Dictionary containing training, validation, and test datasets.
        n_calls (int = 50):
            Number of iterations for Bayesian optimization.
            The lower the faster.
        random_state (int = 42): Random seed for reproducibility.

    Returns:
        tuple: Trained kriging model and RMSE on the test set.
    """
    x_train, x_test, x_val, y_train, y_test, y_val = unpack_data(sets)

    def objective(params) -> float:
        """
        Needs to have params as an argument (gp_minimize restriction).
        """
        _, loss = compute_first_level_loss(
            params,
            x_train=x_train,
            y_train=y_train,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    log.info("Evaluating on optimized hyper-parameters")
    best_model, best_loss = compute_first_level_loss(
        best_params,
        x_train=x_train,
        y_train=y_train,
        x_=x_test,
        y_=y_test,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def mf_kriging(
    param_space: List,
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None],
    level3_sets: Union[Dict[str, ndarray], None],
    n_calls: int = 10,
    random_state: int = 42,
) -> Tuple[MFK, float]:
    """
    Trains a multi-fidelity kriging model with 2/3 fidelity levels.

    Args:
        param_space (list): List of parameter ranges for Bayesian optimization.
        sets (dict): Training, validation, and test datasets.
        n_calls (int = 30): Number of iterations for Bayesian optimization.
        random_state (int = 42): Random seed for reproducibility.
    """
    x_fl_train, x_val1, x_test1, y_fl_train, y_val1, y_test1 = collect_level_data(level1_sets)
    x_sl_train, x_val2, x_test2, y_sl_train, y_val2, y_test2 = collect_level_data(level2_sets)
    x_tl_train, x_val3, x_test3, y_tl_train, y_val3, y_test3 = collect_level_data(level3_sets)

    # Gather all non-None validation and test sets
    x_val = concatenate_if_not_none([x_val1, x_val2, x_val3])
    y_val = concatenate_if_not_none([y_val1, y_val2, y_val3])
    x_test = concatenate_if_not_none([x_test1, x_test2, x_test3])
    y_test = concatenate_if_not_none([y_test1, y_test2, y_test3])

    def objective(params) -> float:
        _, loss = compute_multi_level_loss(
            params,
            x_fl_train=x_fl_train,
            y_fl_train=y_fl_train,
            x_sl_train=x_sl_train,
            y_sl_train=y_sl_train,
            x_tl_train=x_tl_train,
            y_tl_train=y_tl_train,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    best_model, best_loss = compute_multi_level_loss(
        best_params,
        x_fl_train=x_fl_train,
        y_fl_train=y_fl_train,
        x_sl_train=x_sl_train,
        y_sl_train=y_sl_train,
        x_tl_train=x_tl_train,
        y_tl_train=y_tl_train,
        x_=x_test,
        y_=y_test,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def run_first_level_training(
    cpacs: CPACS,
    lh_sampling_path: Union[Path, None],
    objective: str,
    split_ratio: float,
    result_dir: Path,
) -> Tuple[Union[KRG, MFK], Dict[str, ndarray]]:
    """
    Run surrogate model training on first level of fidelity (AVL).
    """
    level1_df = launch_avl(cpacs, lh_sampling_path, objective, result_dir)
    param_order = [col for col in level1_df.columns if col != objective]
    level1_sets = split_data(level1_df, objective, split_ratio)
    model, _ = train_surrogate_model(level1_sets)
    return model, level1_sets, param_order


def run_first_level_training_geometry(
    cpacs_list: list,
    aeromap_uid: str,
    lh_sampling_geom_path: Union[Path, None],
    objective: str,
    split_ratio: float,
    pyavl_dir: Path,
    results_dir: Path,
    KRG_model_bool: bool,
    RBF_model_bool: bool,
    ranges_gui: DataFrame,
) -> Tuple[Union[KRG, MFK], Dict[str, ndarray]]:
    """
    Run surrogate model training on first level of fidelity (AVL).
    """

    df_geom = pd.read_csv(lh_sampling_geom_path)

    # Loop through CPACS files
    final_dfs = []

    for i, cpacs in enumerate(cpacs_list):
        tixi = cpacs.tixi
        pyavl_local_dir = pyavl_dir / f"PyAVL_{i+1}"
        pyavl_local_dir.mkdir(exist_ok=True)

        update_cpacs_from_specs(cpacs, PYAVL_NAME, test=True)
        update_cpacs_from_specs(cpacs, STATICSTABILITY_NAME, test=True)
        tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap_uid)

        alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(
            cpacs=cpacs,
            uid_xpath=AVL_AEROMAP_UID_XPATH,
        )

        n_flight_cond = num_flight_conditions(
            alt_list, mach_list, aoa_list, aos_list
        )
        n_geom_params = num_geom_params(df_geom)

        if n_flight_cond == 1 and n_geom_params == 1:
            log.error(
                "Simulation aborted: only one flight condition and one geometric parameter."
            )
            sys.exit(1)

        try:
            run_avl(cpacs, pyavl_local_dir)

            # check the static stability of the configuration
            run_staticstability(cpacs, pyavl_local_dir)

            level1_df = retrieve_aeromap_data(cpacs, aeromap_uid, objective)

            if level1_df is None or len(level1_df) == 0:
                print(f"Warning: No data retrieved for simulation {i+1}, skipping...")
                continue

            row_df_geom = df_geom.iloc[i]

            if n_flight_cond >= 2:
                n = len(level1_df)
                local_df_geom = pd.DataFrame([row_df_geom] * n).reset_index(drop=True)

                level1_df_combined = pd.concat(
                    [local_df_geom, level1_df.reset_index(drop=True)],
                    axis=1
                )

                final_dfs.append(level1_df_combined)
            else:
                minimal_df = pd.concat(
                    [
                        pd.DataFrame([row_df_geom]).reset_index(drop=True),
                        level1_df[[objective]].reset_index(drop=True),
                    ],
                    axis=1
                )
                final_dfs.append(minimal_df)

        except Exception as e:
            print(f"Error in AVL simulation {i+1}: {str(e)}. Skipping this simulation...")
            continue  # Skip to next iteration, don't add to final_dfs

    # Check if any successful simulations
    if not final_dfs:
        raise ValueError(
            "No successful AVL simulations. Cannot proceed with surrogate model training."
        )

    # Concatenate the dataframes
    final_level1_df = pd.concat(final_dfs, axis=0, ignore_index=True)

    # delete rows where objective = 0 and constant columns
    final_level1_df = final_level1_df.loc[final_level1_df.iloc[:, -1] != 0].copy()
    final_level1_df_c = drop_constant_columns(final_level1_df)
    final_level1_df_c.to_csv(f"{results_dir}/avl_simulations_results.csv", index=False)

    n_params = final_level1_df_c.columns.drop(objective).size
    df_fc = pd.read_csv(f"{results_dir}/avl_simulations_results.csv")
    flight_cols = [c for c in AEROMAP_FEATURES if c in df_fc.columns]
    df_flight = df_fc[flight_cols]

    ranges_fc = pd.DataFrame({
        "Parameter": flight_cols,
        "Min": [df_flight[c].min() for c in flight_cols],
        "Max": [df_flight[c].max() for c in flight_cols],
    })

    ranges_for_gui = pd.DataFrame([
        {"Parameter": k, "Min": v[0], "Max": v[1]}
        for k, v in ranges_gui.items()
    ])

    final_ranges_for_gui = pd.concat(
        [ranges_for_gui,ranges_fc],
        axis=0,
        ignore_index=True,
    )

    final_ranges_for_gui = final_ranges_for_gui.loc[
    final_ranges_for_gui["Min"] != final_ranges_for_gui["Max"]
    ].copy()

    best_geometry_idx = final_level1_df[objective].idxmax()
    best_geometries_df = final_level1_df.loc[[best_geometry_idx]]
    best_geometries_df.to_csv(f"{results_dir}/best_geometric_configurations.csv", index=False)

    param_cols = final_level1_df_c.columns.drop(objective)

    df_norm = final_level1_df_c.copy()
    normalization_params = {}

    for col in param_cols:
        col_mean = final_level1_df_c[col].mean()
        col_std = final_level1_df_c[col].std()
        if col_std == 0:
            df_norm[col] = 0.0
        else:
            df_norm[col] = (final_level1_df_c[col] - col_mean) / col_std
        normalization_params[col] = {"mean": col_mean, "std": col_std}

    norm_df = pd.DataFrame.from_dict(
        normalization_params,
        orient="index"
    ).reset_index()

    norm_df.columns = ["Parameter", "mean", "std"]

    norm_df.to_csv(
        f"{results_dir}/normalization_params.csv",
        index=False
    )

    krg_model = None
    krg_rmse = None
    rbf_model = None
    rbf_rmse = None
    level1_sets = split_data(df_norm, objective, split_ratio)
    param_order = [col for col in df_norm.columns if col != objective]

    if KRG_model_bool:
        log.info("--------------Star training KRG model.--------------\n")
        krg_model, krg_rmse = train_surrogate_model(level1_sets)
        rmse_df = pd.DataFrame({"rmse": [krg_rmse]})
        rmse_path = f"{results_dir}/rmse_KRG.csv"
        rmse_df.to_csv(rmse_path, index=False)
        log.info("--------------KRG model trained.--------------\n")
        
        model_name = "KRG"
        save_best_surrogate_geometry(
            surrogate_model=krg_model,
            model_name=model_name,
            objective=objective,
            param_order=param_order,
            normalization_params=normalization_params,
            final_level1_df_c=final_level1_df_c,
            results_dir=results_dir,
            )

    if RBF_model_bool:
        log.info("--------------Star training RBF model.--------------\n")
        rbf_model, rbf_rmse = train_surrogate_model_RBF(n_params, level1_sets)
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
            final_level1_df_c=final_level1_df_c,
            results_dir=results_dir,
            )

    return krg_model, rbf_model, level1_sets, best_geometry_idx, param_order


def run_adaptative_refinement(
    cpacs: CPACS,
    results_dir: Path,
    model: Union[KRG, MFK],
    level1_sets: Dict[str, ndarray],
    rmse_obj: float,
    objective: str,
) -> None:
    """
    Iterative improvement using SU2 data.
    """
    high_var_pts = []
    rmse = float("inf")
    df = DataFrame(
        {
            "altitude": [],
            "machNumber": [],
            "angleOfAttack": [],
            "angleOfSideslip": [],
            objective: [],
        }
    )

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


def run_adaptative_refinement_geom(
    cpacs: CPACS,
    results_dir: Path,
    model: Union[KRG, MFK],
    level1_sets: Dict[str, ndarray],
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
    df_old_path = results_dir / "avl_simulations_results.csv"
    df_old = pd.read_csv(df_old_path)
    df = pd.DataFrame(columns=df_old.columns)
    x_array = level1_sets["x_train"]
    nb_iters = len(x_array)
    log.info(f"Starting adaptive refinement with maximum {nb_iters=}.")

    norm_df = pd.read_csv(results_dir / "normalization_params.csv")
    normalization_params = {
        row["Parameter"]: {"mean": row["mean"], "std": row["std"]}
        for _, row in norm_df.iterrows()
    }

    log.info("Loaded normalization parameters:")
    for k, v in normalization_params.items():
        log.debug(f"{k}: mean={v['mean']}, std={v['std']}")


    cpacs_list = []

    for _ in range(nb_iters):
        # Find new high variance points based on inputs x_train
        new_point_df_norm = new_points_geom(
            x_array=x_array,
            model=model,
            results_dir=results_dir,
            high_var_pts=high_var_pts,
            ranges_gui=ranges_gui,
        )

        # 1st Breaking condition
        if new_point_df_norm is None:
            log.warning("No new high-variance points found.")
            break
        elif new_point_df_norm.empty:
            log.warning("No new high-variance points found.")
            break
        high_var_pts.append(new_point_df_norm.values[0])

        cpacs_file = cpacs.cpacs_file
        new_point_df = new_point_df_norm.copy()

        for col in new_point_df.columns:
            if col not in normalization_params:
                log.warning(f"No normalization params for {col}, skipping denorm.")
                continue

            mean = normalization_params[col]["mean"]
            std  = normalization_params[col]["std"]

            new_point_df[col] = new_point_df[col] * std + mean


        for i, geom_row in new_point_df.iterrows():

            cpacs_p = get_results_directory(SU2RUN_NAME) / f"CPACS_newpoint_{i+1:03d}_iter{_}.xml"
            copyfile(cpacs_file, cpacs_p)
            cpacs_out_obj = CPACS(cpacs_p)
            tixi = cpacs_out_obj.tixi
            params_to_update = {}
            for col in new_point_df.columns:
                # SINTAX: {comp}_of_{section}_of_{param}
                col_parts = col.split('_of_')
                uID_wing = col_parts[2]
                uID_section = col_parts[1]
                name_parameter = col_parts[0]
                val = geom_row[col]

                xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)

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
            dir_res = get_results_directory(SU2RUN_NAME) / f"SU2Run_{idx}_iter{_}"
            dir_res.mkdir(exist_ok=True)
            obj_value = launch_gmsh_su2_geom(
                cpacs=cpacs_,
                results_dir=dir_res,
                objective=objective,
                aeromap_uid=aeromap_uid,
            )
            new_row = new_point_df.iloc[idx].copy()
            new_row[objective] = obj_value
            new_df_list.append(new_row)
        new_df = pd.DataFrame(new_df_list)

        # Stack new with old
        df = pd.concat([new_df, df], ignore_index=True)

        df.to_csv(get_results_directory(SU2RUN_NAME) / f"SU2_dataframe_iter_{_}", index=False)

        model, rmse = train_surrogate_model(
            level1_sets=level1_sets,
            level2_sets=split_data(df, objective),
        )

        model_name = "KRG"
        param_order = [col for col in df.columns if col != objective]
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
            rmse_path = f"{results_dir}/rmse_KRG.csv"
            rmse_df.to_csv(rmse_path, index=False)
            break


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

    param_cols = df1.columns.drop(objective)
    n_params = param_cols.size

    df_norm = df1.copy()
    normalization_params = {}

    for col in param_cols:
        col_mean = df1[col].mean()
        col_std = df1[col].std()
        if col_std == 0:
            df_norm[col] = 0.0
        else:
            df_norm[col] = (df1[col] - col_mean) / col_std
        normalization_params[col] = {"mean": col_mean, "std": col_std}

    norm_df = pd.DataFrame.from_dict(
        normalization_params,
        orient="index"
    ).reset_index()

    norm_df.columns = ["Parameter", "mean", "std"]

    norm_df.to_csv(
        f"{results_dir}/normalization_params.csv",
        index=False
    )

    krg_model = None
    krg_rmse = None
    rbf_model = None
    rbf_rmse = None
    level1_sets = split_data(df_norm, objective, split_ratio)
    param_order = [col for col in df_norm.columns if col != objective]

    if KRG_model_bool:
        print("\n\n")
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
        print("\n\n")
        log.info("--------------Star training RBF model.--------------\n")
        rbf_model, rbf_rmse = train_surrogate_model_RBF(n_params, level1_sets)
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


def run_adaptative_refinement_geom_existing_db(
    cpacs: CPACS,
    results_dir: Path,
    model: Union[KRG, MFK, RBF],
    level1_sets: Dict[str, ndarray],
    rmse_obj: float,
    objective: str,
    aeromap_uid,
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

    norm_df = pd.read_csv(results_dir / "normalization_params.csv")
    normalization_params = {
        row["Parameter"]: {"mean": row["mean"], "std": row["std"]}
        for _, row in norm_df.iterrows()
    }

    log.info("Loaded normalization parameters:")
    for k, v in normalization_params.items():
        log.debug(f"{k}: mean={v['mean']}, std={v['std']}")

    cpacs_list = []

    for _ in range(nb_iters):
        # Find new high variance points based on inputs x_train
        new_point_df = new_points_geom(
            x_array=x_array,
            model=model,
            results_dir=results_dir,
            high_var_pts=high_var_pts,
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

            cpacs_p = get_results_directory(SU2RUN_NAME) / f"CPACS_newpoint_{i+1:03d}_iter{_}.xml"
            copyfile(cpacs_file, cpacs_p)
            cpacs_out_obj = CPACS(cpacs_p)
            tixi = cpacs_out_obj.tixi
            params_to_update = {}
            for col in new_point_df.columns:
                # SINTAX: {comp}_of_{section}_of_{param}
                col_parts = col.split('_of_')
                uID_wing = col_parts[2]
                uID_section = col_parts[1]
                name_parameter = col_parts[0]
                val = geom_row[col]

                xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)

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

            dir_res = get_results_directory(SU2RUN_NAME) / f"SU2Run_{idx}_iter{_}"
            dir_res.mkdir(exist_ok=True)
            obj_value = launch_gmsh_su2_geom(
                cpacs=cpacs_,
                results_dir=dir_res,
                objective=objective,
                aeromap_uid=aeromap_uid,
            )
            new_row = new_point_df.iloc[idx].copy()
            new_row[objective] = obj_value
            new_df_list.append(new_row)

        new_df = pd.DataFrame(new_df_list)
        df = pd.concat([new_df, df_simulation], ignore_index=True)
        df.to_csv(get_results_directory(SU2RUN_NAME) / f"SU2_dataframe_iter_{_}", index=False)

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


def get_hyperparam_space_RBF(
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None],
    level3_sets: Union[Dict[str, ndarray], None],
    n_params: int,
) -> List:
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
    model: Union[RBF, MFK],
    lambda_penalty: float,
    x_: ndarray,
    y_: ndarray,
) -> float:
    return compute_rmse(model, x_, y_)


def log_params_RBF(result: OptimizeResult) -> None:
    """Log parametri per RBF SMT (d0, poly_degree, reg)"""
    params = result.x
    log.info(f"d0 (scaling): {params[0]:.3f}")
    log.info(f"poly_degree: {params[1]}")
    log.info(f"reg (regularization): {params[2]:.2e}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")


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
    params: Tuple,
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


def mf_RBF(
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None] = None,
    level3_sets: Union[Dict[str, ndarray], None] = None,
    n_calls: int = 10,
    random_state: int = 42,
) -> Tuple[RBF, float]:
    """
    Train a multi-fidelity RBF model using single/multi-level datasets.
    Debug-enabled version to trace data issues.
    """

    log.info("=== Entered Multi Fidelity RBF ===")

    # Unpack first level
    x_fl_train, x_val1, x_test1, y_fl_train, y_val1, y_test1 = collect_level_data(level1_sets)
    log.info(f"Level 1 shapes: x_train={x_fl_train.shape}, y_train={y_fl_train.shape}, "
             f"x_val={None if x_val1 is None else x_val1.shape}, y_val={None if y_val1 is None else y_val1.shape}, "
             f"x_test={None if x_test1 is None else x_test1.shape}, y_test={None if y_test1 is None else y_test1.shape}")

    # Unpack second level
    if level2_sets:
        x_sl_train, x_val2, x_test2, y_sl_train, y_val2, y_test2 = collect_level_data(level2_sets)
        log.info(f"Level 2 shapes: x_train={x_sl_train.shape}, y_train={y_sl_train.shape}")
    else:
        x_sl_train, x_val2, x_test2, y_sl_train, y_val2, y_test2 = (None,) * 6

    # Unpack third level
    if level3_sets:
        x_tl_train, x_val3, x_test3, y_tl_train, y_val3, y_test3 = collect_level_data(level3_sets)
        log.info(f"Level 3 shapes: x_train={x_tl_train.shape}, y_train={y_tl_train.shape}")
    else:
        x_tl_train, x_val3, x_test3, y_tl_train, y_val3, y_test3 = (None,) * 6

    # Combine validation/test sets across levels
    x_val = concatenate_if_not_none([x_val1, x_val2, x_val3])
    y_val = concatenate_if_not_none([y_val1, y_val2, y_val3])
    x_test = concatenate_if_not_none([x_test1, x_test2, x_test3])
    y_test = concatenate_if_not_none([y_test1, y_test2, y_test3])

    log.info(f"Combined validation shapes: x_val={None if x_val is None else x_val.shape}, y_val={None if y_val is None else y_val.shape}")
    log.info(f"Combined test shapes: x_test={None if x_test is None else x_test.shape}, y_test={None if y_test is None else y_test.shape}")

    # Objective function for Bayesian optimization
    def objective(params) -> float:
        d0, poly_degree, reg, lambda_penalty = params
        log.debug(f"Trying hyperparams: d0={d0}, poly_degree={poly_degree}, reg={reg}, lambda={lambda_penalty}")

        model = RBF(d0=d0, poly_degree=int(poly_degree), reg=reg, print_global=False)
        log.debug(f"Setting Level 1 training values: x_fl_train.shape={x_fl_train.shape}, y_fl_train.shape={y_fl_train.shape}")
        model.set_training_values(x_fl_train, y_fl_train)

        if x_sl_train is not None and y_sl_train is not None:
            log.debug(f"Adding Level 2 training values: x_sl_train.shape={x_sl_train.shape}, y_sl_train.shape={y_sl_train.shape}")
            model.set_training_values(x_sl_train, y_sl_train, name=2)

        if x_tl_train is not None and y_tl_train is not None:
            log.debug(f"Adding Level 3 training values: x_tl_train.shape={x_tl_train.shape}, y_tl_train.shape={y_tl_train.shape}")
            model.set_training_values(x_tl_train, y_tl_train, name=3)

        model.train()
        loss_val = compute_loss_RBF(model, lambda_penalty, x_val, y_val)
        log.debug(f"Validation loss: {loss_val:.6f}")
        return loss_val

    # Hyperparameter search space
    hyperparam_space = [
        Real(1, 500, name="d0"),
        Categorical([-1], name="poly_degree"),
        Real(1e-15, 1e-8, name="reg"),
        Real(0.0, 1.0, name="lambda_penalty")
    ]

    best_params = optimize_hyper_parameters_RBF(objective, hyperparam_space, n_calls, random_state)
    log.info(f"Best hyperparameters found: {best_params}")

    # Train final model on all available data
    x_final = np.vstack([x for x in [x_fl_train, x_sl_train, x_tl_train] if x is not None])
    y_final = np.hstack([y for y in [y_fl_train, y_sl_train, y_tl_train] if y is not None])
    log.info(f"Final training shapes: x_final={x_final.shape}, y_final={y_final.shape}")

    d0, poly_degree, reg, lambda_penalty = best_params
    final_model = RBF(d0=d0, poly_degree=int(poly_degree), reg=reg, print_global=False)
    final_model.set_training_values(x_final, y_final)
    final_model.train()

    # Evaluate on test set
    if x_test is not None and y_test is not None:
        loss_test = compute_loss_RBF(final_model, lambda_penalty, x_test, y_test)
        log.info(f"Final RMSE on test set (multi-fidelity RBF): {loss_test:.6f}")
    else:
        loss_test = 0.0
        log.warning("No test set available for multi-fidelity RBF evaluation.")

    log.info("=== Exiting mf_RBF ===")
    return final_model, loss_test


def RBF_model(
    param_space: List,
    sets: Dict[str, ndarray],
    n_calls: int = 50,
    random_state: int = 42
) -> Tuple[RBF, float]:
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
    print(f"y_test:  [{y_test.min():.4f}, {y_test.max():.4f}]")
    print(f"y_pred:  [{y_pred.min():.4f}, {y_pred.max():.4f}]")
    print(f"R²:      {r2_score(y_test, y_pred):.4f}")

    best_loss = compute_rmse(best_model, x_test, y_test)
    log.info(f"Final first level RMSE on test set: {best_loss:.6f}")
    return best_model, best_loss


def train_surrogate_model_RBF(
    n_params: int,
    level1_sets: Dict[str, ndarray],
    level2_sets: Union[Dict[str, ndarray], None] = None,
    level3_sets: Union[Dict[str, ndarray], None] = None,
) -> Tuple[Union[RBF, MFK], float]:
    """
    Train either single-fidelity or multi-fidelity RBF model.
    """
    n_params_ = n_params
    hyperparam_space = get_hyperparam_space_RBF(level1_sets, level2_sets, level3_sets, n_params_)
    if level2_sets is not None or level3_sets is not None:
        # multi-fidelity RBF
        log.info(f"{level2_sets=}")
        return mf_RBF(
            level1_sets=level1_sets,
            level2_sets=level2_sets,
            level3_sets=level3_sets,
        )
    else:
        # single-fidelity
        return RBF_model(
            param_space=hyperparam_space,
            sets=level1_sets,
        )


def run_adaptative_refinement_geom_RBF(
    cpacs: CPACS,
    results_dir: Path,
    model: Union[KRG, MFK],
    level1_sets: Dict[str, ndarray],
    rmse_obj: float,
    objective: str,
    aeromap_uid: str,
    ranges_gui: DataFrame,
) -> None:
    """
    Iterative adaptive refinement using RBF LOO-error based sampling.
    """

    norm_df = pd.read_csv(results_dir / "normalization_params.csv")
    normalization_params = {
        row["Parameter"]: {"mean": row["mean"], "std": row["std"]}
        for _, row in norm_df.iterrows()
    }

    log.info("Loaded normalization parameters:")
    for k, v in normalization_params.items():
        log.debug(f"{k}: mean={v['mean']}, std={v['std']}")

    poor_pts = []
    rmse = float("inf")

    df_old_path = results_dir / "avl_simulations_results.csv"
    df_old = pd.read_csv(df_old_path)
    df = pd.DataFrame(columns=df_old.columns)

    n_params = len(df_old.columns.drop(objective))

    x_array = level1_sets["x_train"]
    y_array = level1_sets["y_train"]
    nb_iters = len(x_array)

    log.info(f"Starting RBF adaptive refinement with maximum {nb_iters=}.")

    for it in range(nb_iters):

        log.info(f"=== Iteration {it} ===")

        # Generate new points
        new_point_df_norm = new_points_RBF(
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

        new_point_df_norm.to_csv(results_dir / f"new_points_norm_iter_{it}.csv", index=False)
        new_point_df.to_csv(results_dir / f"new_points_phys_iter_{it}.csv", index=False)

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

        # Update CPACS for each new point
        for i, geom_row in new_point_df.iterrows():

            cpacs_p = get_results_directory(SU2RUN_NAME) / f"CPACS_newpoint_{i+1:03d}_iter{it}.xml"
            copyfile(cpacs_file, cpacs_p)

            cpacs_out_obj = CPACS(cpacs_p)
            tixi = cpacs_out_obj.tixi

            params_to_update = {}

            for col in new_point_df.columns:
                col_parts = col.split("_of_")
                if len(col_parts) != 3:
                    log.warning(f"Skipping unexpected param name format: {col}")
                    continue
                name_parameter, uID_section, uID_wing = col_parts
                val = geom_row[col]

                xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)

                if name_parameter not in params_to_update:
                    params_to_update[name_parameter] = {"values": [], "xpath": []}

                params_to_update[name_parameter]["values"].append(val)
                params_to_update[name_parameter]["xpath"].append(xpath)

            cpacs_obj = update_geometry_cpacs(cpacs_file, cpacs_p, params_to_update)
            cpacs_list.append(cpacs_obj)

        # Run SU2 on new points
        new_df_list = []
        for idx, cpacs_ in enumerate(cpacs_list):
            dir_res = get_results_directory(SU2RUN_NAME) / f"SU2Run_{idx}_iter{it}"
            dir_res.mkdir(exist_ok=True)

            obj_value = launch_gmsh_su2_geom(
                cpacs=cpacs_,
                results_dir=dir_res,
                objective=objective,
                aeromap_uid=aeromap_uid,
            )

            new_row = new_point_df.iloc[idx].copy()
            new_row[objective] = obj_value
            new_df_list.append(new_row)

        new_df = pd.DataFrame(new_df_list)

        df_new = pd.concat([df, new_df], ignore_index=True, sort=False)

        df_new.to_csv(get_results_directory(SU2RUN_NAME) / f"SU2_dataframe_iter_{it}.csv", index=False)

        # Retrain surrogate

        model, rmse = train_surrogate_model_RBF(
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