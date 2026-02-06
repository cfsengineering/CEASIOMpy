"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
Either (1) Kriging or (2-3) Multi-Fidelity Kriging model can be used,
depending on the level of fidelity chosen.

TODO:
    * More tests on adaptive sampling
    * Never tested with 3 levels of fidelity
"""


# Imports
import numpy as np

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.smtrain.func.plot import plot_validation
from ceasiompy.smtrain.func.utils import (
    save_model,
    store_best_geom_from_training,
)
from ceasiompy.smtrain.func.sampling import (
    split_data,
    lh_sampling_geom,
    get_high_variance_points,
)
from ceasiompy.smtrain.func.config import (
    get_settings,
    normalize_dataset,
    get_params_to_optimise,
    create_list_cpacs_geometry,
    save_best_surrogate_geometry,
)
from ceasiompy.smtrain.func.trainsurrogatemodel import (
    rbf_training,
    krg_training,
    run_adapt_refinement_geom,
    run_first_level_simulations,
)

from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from ceasiompy.smtrain.func.utils import DataSplit
from ceasiompy.smtrain.func.config import TrainingSettings

from ceasiompy import log
from ceasiompy.smtrain import (
    LEVEL_TWO,
    MODULE_NAME as SMTRAIN,
)


# Methods

# def _load_smtrain_model(cpacs: CPACS) -> None:
#     ranges_gui = get_params_to_optimise(cpacs)

#     krg_model, rbf_model, sets, param_order = training_existing_db(
#         results_dir,
#         split_ratio,
#         selected_krg_model,
#         selected_rbf_model
#     )

#     if fidelity_level == LEVEL_TWO:
#         run_adapt_refinement_geom_krg_existing_db(
#             cpacs=cpacs,
#             results_dir=results_dir,
#             model=krg_model,
#             level1_sets=sets,
#             rmse_obj=rmse_obj,
#             objective=objective,
#             aeromap_uid=aeromap_selected,
#             ranges_gui=ranges_gui,
#         )

#     if selected_krg_model:
#         log.info("Validation plots.")
#         plot_dir = results_dir / "Validation_plot_KRG"
#         plot_dir.mkdir(parents=True, exist_ok=True)
#         plot_validation(krg_model, sets, objective, plot_dir)

#         save_model(cpacs, krg_model, objective, results_dir, param_order)

#     if selected_rbf_model:
#         log.info("Validation plots.")
#         plot_dir = results_dir / "Validation_plot_RBF"
#         plot_dir.mkdir(parents=True, exist_ok=True)
#         plot_validation(rbf_model, sets, objective, plot_dir)

#         save_model(cpacs, rbf_model, objective, results_dir, param_order)


# def _flight_condition_exploration(
#     cpacs: CPACS,
#     results_dir: Path,
#     objective,
#     split_ratio,
#     fidelity_level,
#     rmse_obj,
# ):
#     n_samples, ranges = design_of_experiment(cpacs)
#     lh_sampling_path = lh_sampling(n_samples, ranges, results_dir)

#     # First level fidelity training
#     model, sets, param_order = run_first_level_training(
#         cpacs=cpacs,
#         lh_sampling_path=lh_sampling_path,
#         objective=objective,
#         split_ratio=split_ratio,
#         result_dir=results_dir,
#     )

#     # Second level fidelity training
#     if fidelity_level == LEVEL_TWO:
#         run_adaptative_refinement(
#             cpacs=cpacs,
#             results_dir=results_dir,
#             model=model,
#             level1_sets=sets,
#             rmse_obj=rmse_obj,
#             objective=objective,
#         )

#     # 3. Plot, save and get results
#     log.info("Validation plots.")
#     plot_dir = results_dir / "Validation_plot"
#     plot_dir.mkdir(parents=True, exist_ok=True)
#     plot_validation(model, sets, objective, plot_dir)

#     save_model(cpacs, model, objective, results_dir,param_order)


def _geometry_exploration(
    cpacs: CPACS,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    # Get Parameters Ranges
    params_ranges = get_params_to_optimise(cpacs)

    # LHS sampling from the Parameter Ranges
    lh_sampling = lh_sampling_geom(
        n_samples=training_settings.n_samples,
        params_ranges=params_ranges,
    )

    # Create the list of CPACS files (in function of geometry values of lh_smapling)
    cpacs_list = create_list_cpacs_geometry(
        cpacs=cpacs,
        lh_sampling=lh_sampling,
        results_dir=results_dir,
    )

    # Generate directory where to store Low Fidelity runs
    low_fidelity_dir = results_dir / "low_fidelity"
    low_fidelity_dir.mkdir(parents=True, exist_ok=True)

    # Low Fidelity First (+ Always available by default)
    level1_df: DataFrame = run_first_level_simulations(
        cpacs_list=cpacs_list,
        lh_sampling=lh_sampling,
        results_dir=results_dir,
        params_ranges=params_ranges,
        training_settings=training_settings,
    )

    # Save Best Geometry from training in adequate Results Directory
    store_best_geom_from_training(
        dataframe=level1_df,
        cpacs_list=cpacs_list,
        lh_sampling=lh_sampling,
        results_dir=low_fidelity_dir,
        params_ranges=params_ranges,
        training_settings=training_settings,
    )

    if "KRG" in training_settings.sm_models:
        krg_results_dir = results_dir / "krg_surrogate_model"
        krg_results_dir.mkdir(parents=True, exist_ok=True)

    if "RBF" in training_settings.sm_models:
        rbf_results_dir = results_dir / "rbf_surrogate_model"
        rbf_results_dir.mkdir(parents=True, exist_ok=True)

    # Train Selected Surrogate Models
    # Normalize

    # Split
    level1_split: DataSplit = split_data(
        df=level1_df,
        training_settings=training_settings,
    )

    if "KRG" in training_settings.sm_models:
        best_krg_model, best_krg_rmse = krg_training(level1_split)
        save_best_surrogate_geometry(
            df_norm=level1_split,
            best_rmse=best_krg_rmse,
            best_model=best_krg_model,
            results_dir=low_fidelity_dir,
            level1_split=level1_split,
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

    # Adaptative Refinement
    if training_settings.fidelity_level == LEVEL_TWO:
        if (
            ("KRG" in training_settings.sm_models)
            or ("RBF" in training_settings.sm_models)
        ):
            log.info("Starting Adaptative Refinement of the Design Space.")

            # Generate directory where to store Low Fidelity runs
            high_fidelity_dir = results_dir / "high_fidelity"
            high_fidelity_dir.mkdir(exist_ok=True)

        if "KRG" in training_settings.sm_models:
            high_var_pts: DataFrame = get_high_variance_points(
                model=best_krg_model,
                level1_df_norm=level1_df_norm,
                training_settings=training_settings,
            )

        if "RBF" in training_settings.sm_models:
            loo_pts = get_loo_points(
                x_array=x_array,
                y_array=y_array,
                model=model,
                ranges_gui=ranges_gui,
                n_local=1,
                perturb_scale=1,
            )

        unvalid_pts = np.concatenate(
            arrays=[high_var_pts, loo_pts]
        )

        # On High-Variance Points
        level2_df = run_adapt_refinement_geom(
            cpacs=cpacs,
            unvalid_pts=unvalid_pts,
            level1_df=level1_df,
            results_dir=high_fidelity_dir,
            training_settings=training_settings,
        )
        level2_split: DataSplit = split_data(
            df=level2_df_norm,
            training_settings=training_settings,
        )

    columns: list[str] = [c for c in level1_df.columns if c != training_settings.objective]

    # 3. Plot, save and get results
    if "KRG" in training_settings.sm_models:
        plot_validation(
            model=best_krg_model,
            results_dir=krg_results_dir,
            level1_split=level1_split,
            training_settings=training_settings,
        )
        save_model(
            model=best_krg_model,
            columns=columns,
            results_dir=krg_results_dir,
            training_settings=training_settings,
        )

    if "RBF" in training_settings.sm_models:
        plot_validation(
            model=best_rbf_model,
            results_dir=rbf_results_dir,
            level1_split=level1_split,
            training_settings=training_settings,
        )
        save_model(
            model=best_rbf_model,
            columns=columns,
            results_dir=rbf_results_dir,
            training_settings=training_settings,
        )


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Train a surrogate model (single-level or multi-fidelity) using aerodynamic data.

    1. Retrieve settings from the CPACS file
    2. Train surrogate model
    3. Plot and save model
    """
    tixi = cpacs.tixi

    # 1. Retrieve settings from the CPACS file
    training_settings = get_settings(tixi)

    old_new_sim = "Run New Simulations"

    if old_new_sim == "Run New Simulations":
        simulation_purpose = "Geometry Exploration"
        if simulation_purpose == "Flight Condition Exploration":
            # _flight_condition_exploration(
            #     cpacs=cpacs,
            #     results_dir=results_dir,
            #     training_settings=training_settings,
            # )
            raise NotImplementedError

        if simulation_purpose == "Geometry Exploration":
            _geometry_exploration(
                cpacs=cpacs,
                results_dir=results_dir,
                training_settings=training_settings,
            )

    if old_new_sim == "Load Geometry Exploration Simulations":
        # _load_smtrain_model(
        #     cpacs=cpacs,
        # )
        raise NotImplementedError


if __name__ == "__main__":
    call_main(main, SMTRAIN)
