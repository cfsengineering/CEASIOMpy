"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
The surrogate model can be trained either through a csv file containing the inputs and outputs,
or by carrying out a Design of Experiments after providing the domain extremes.
Either kriging or Multi-Fidelity kriging algorithm can be used,
depending on the level of fidelity chosen.

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    * Create test functions
    * Adapt SaveAeroCoefficient for the adaptive sampling
    * More test on adaptive sampling
    * Never tested with 3 levels of fidelity
    * Define how to change AVL and SU2 settings

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np
import pandas as pd

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.SMTrain.func.plot import plot_validation
from ceasiompy.SMTrain.func.results import get_smt_results
from ceasiompy.SMTrain.func.train_surrogate import (
    save_model,
    train_surrogate_model,
)
from ceasiompy.SMTrain.func.config import (
    get_settings,
    design_of_experiment,
    get_datasets_from_aeromaps,
)
from ceasiompy.SMTrain.func.sampling import (
    new_doe,
    new_points,
    split_data,
    lh_sampling,
)
from ceasiompy.SMTrain.func.create_data import (
    launch_avl,
    launch_su2,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.SMTrain import MODULE_NAME
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Train a surrogate model (single-level or multi-fidelity) using aerodynamic data.
    """

    # Retrieve settings from the CPACS file
    (
        fidelity_level,
        data_repartition,
        objective_coefficient,
        show_plot,
        new_dataset,
        fraction_of_new_samples,
        doe, avl_or_su2, rmse_obj,
    ) = get_settings(cpacs)

    avl = (avl_or_su2 == "AVL")

    if doe:
        # Generate new samples
        n_samples, ranges = design_of_experiment(cpacs)
        lh_sampling_path = lh_sampling(n_samples, ranges, results_dir)

        # One level fidelity model training
        if fidelity_level == "One level":
            if avl:
                level1_dataset = launch_avl(cpacs, lh_sampling_path, objective_coefficient)
            else:
                level1_dataset = launch_su2(cpacs, results_dir, SU2RUN_NAME, objective_coefficient)
            datasets = {"level_1": level1_dataset}
            sets = split_data(datasets, data_repartition)
            model, _ = train_surrogate_model(fidelity_level, datasets, sets)

        # Two-level fidelity model training
        elif fidelity_level == "Two levels":
            # Train the first-level (low-fidelity) model using AVL
            avl_dataset = launch_avl(cpacs, lh_sampling_path, objective_coefficient)
            datasets = {"level_1": avl_dataset}
            avl_sets = split_data(datasets, data_repartition)
            model, _ = train_surrogate_model("One level", datasets, avl_sets)

            # Adaptive refinement: iterative improvement using SU2 high-fidelity data
            high_variance_points = []
            max_iterations = len(avl_dataset[0])
            iteration = 0
            rmse = float("inf")

            while (
                iteration < max_iterations
                and
                rmse > rmse_obj
            ):
                # Select new high-variance points for refinement
                new_point_df = new_points(datasets, model, results_dir, high_variance_points)

                # Check if new_point_df is empty (no new high-variance points available)
                if new_point_df.empty:
                    log.warning(
                        "No new high-variance points found. Ending refinement process and "
                        "returning the current surrogate model."
                    )
                    break

                new_point = new_point_df.values[0]
                high_variance_points.append(new_point)

                # Generate unique SU2 working directory using iteration
                wkdir_su2 = Path(SU2RUN_NAME) / f"SU2_{iteration}"
                wkdir_su2.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

                su2_dataset = launch_su2(
                    cpacs,
                    results_dir,
                    wkdir_su2,
                    objective_coefficient,
                    high_variance_points,
                )

                if "level_2" in datasets:
                    X_old, y_old, df_old, removed_old, df_cl_old = datasets["level_2"]
                    X_new, y_new, df_new, _ , df_cl_new = su2_dataset

                    X_combined = np.vstack([X_old, X_new])  # Input
                    y_combined = np.vstack([y_old, y_new])  # Output

                    df_combined = pd.concat([df_old, df_new], ignore_index=True)
                    df_cl_combined = pd.concat([df_cl_old, df_cl_new], ignore_index=True)

                    removed_combined = removed_old

                    datasets["level_2"] = (
                        X_combined,
                        y_combined,
                        df_combined,
                        removed_combined,
                        df_cl_combined,
                    )

                else:
                    datasets["level_2"] = su2_dataset

                sets = split_data(datasets, 0.7, 0.5)
                model, rmse = train_surrogate_model(fidelity_level, datasets, sets)
                iteration += 1

        else:
            raise ValueError("Fidelity level must be either 'One' or 'Two'")

    # If DoE is not used, load existing datasets from CSV
    else:
        datasets = get_datasets_from_aeromaps(cpacs, fidelity_level, objective_coefficient)
        sets = split_data(datasets, data_repartition)

        # Train the surrogate model
        model, _ = train_surrogate_model(fidelity_level, datasets, sets)

        # Generate new dataset if required
        if new_dataset is True:
            new_doe(datasets, model, fraction_of_new_samples, results_dir)

    # Plot, save and get results
    if show_plot is True:
        log.info("Validation plots.")
        plot_validation(model, sets, objective_coefficient, results_dir)

    save_model(model, objective_coefficient, datasets, results_dir)
    get_smt_results(cpacs, results_dir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
