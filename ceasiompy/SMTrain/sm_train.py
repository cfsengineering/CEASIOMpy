"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
The surrogate model can be trained either through a csv file containing the inputs and outputs,
or by carrying out a Design of Experiments after providing the domain extremes.
Either Kriging or Multi-Fidelity Kriging algorithm can be used,
depending on the level of fidelity chosen.

Python version: >= 3.8

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:

    * Create test function
    * Adapt SaveAeroCoefficient for the adaptive sampling
    * More test on adaptive sampling
    * Never tested with 3 levels of fidelity
    * Define how to change AVL and SU2 settings


"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.SMTrain.func.smtconfig import (
    get_settings,
    get_doe_settings,
    DoE,
    get_datasets_from_aeromaps,
)
from ceasiompy.SMTrain.func.smtfunc import (
    split_data,
    train_surrogate_model,
    save_model,
    plot_validation,
    new_doe,
    lh_sampling,
    launch_avl,
    launch_su2,
    new_points,
)
from ceasiompy.SMTrain.func.smtresults import get_smt_results
from pathlib import Path
import pandas as pd
import numpy as np

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_smTrain(cpacs_path, cpacs_tmp_cfg, wkdir):
    """
    Train a surrogate model using aerodynamic data.
    Depending on the fidelity level, the function trains a single-level or multi-fidelity model.

    Args:
        cpacs_path (str): Path to the CPACS input file.
        cpacs_tmp_cfg (str): Path to the temporary CPACS configuration file.
        wkdir (str): Working directory where results are stored.
    """

    # Retrieve settings from the CPACS file
    (
        fidelity_level,
        data_repartition,
        objective_coefficient,
        show_plot,
        new_dataset,
        fraction_of_new_samples,
    ) = get_settings(cpacs_path)

    # Get DoE settings
    doe, avl_or_su2, rmse_obj = get_doe_settings(cpacs_path)

    # If DoE is enabled, generate new samples
    if doe is True:
        n_samples, ranges = DoE(cpacs_path)
        lh_sampling(n_samples, ranges, wkdir)

        # One level fidelity model training
        if fidelity_level == "One level":
            if avl_or_su2 == "AVL":
                # Generate dataset using AVL
                avl_dataset = launch_avl(wkdir, cpacs_path, cpacs_tmp_cfg, objective_coefficient)
                datasets = {"level_1": avl_dataset}
                sets = split_data(datasets, data_repartition)

                # Train Kriging model
                model, _ = train_surrogate_model(fidelity_level, datasets, sets)
            elif avl_or_su2 == "SU2":
                # Generate dataset using SU2
                wkdir_su2 = get_results_directory("SU2Run")
                su2_dataset = launch_su2(
                    wkdir, wkdir_su2, cpacs_path, cpacs_tmp_cfg, objective_coefficient
                )
                datasets = {"level_1": su2_dataset}
                sets = split_data(datasets, data_repartition)

                # Train Kriging model
                model, _ = train_surrogate_model(fidelity_level, datasets, sets)
            else:
                raise ValueError("You must select 'Use AVL' or 'Use SU2' option")

        # Two-level fidelity model training
        elif fidelity_level == "Two levels":
            # Train the first-level (low-fidelity) model using AVL
            avl_dataset = launch_avl(wkdir, cpacs_path, cpacs_tmp_cfg, objective_coefficient)
            datasets = {"level_1": avl_dataset}
            avl_sets = split_data(datasets, data_repartition)
            model, _ = train_surrogate_model("One level", datasets, avl_sets)

            # Adaptive refinement: iterative improvement using SU2 high-fidelity data
            high_variance_points = []
            max_iterations = len(avl_dataset[0])  # Ensure the iteration limit is not exceeded X)
            iteration = 0

            rmse = float("inf")

            while rmse > rmse_obj and iteration < max_iterations:
                # Select new high-variance points for refinement
                new_point_df = new_points(datasets, model, wkdir, high_variance_points)

                # Check if new_point_df is empty (no new high-variance points available)
                if new_point_df.empty:
                    log.warning(
                        "No new high-variance points found. Ending refinement process and "
                        "returning the current surrogate model."
                    )
                    break  # Exit loop and return the current model

                new_point = new_point_df.values[0]
                high_variance_points.append(new_point)

                # Generate unique SU2 working directory using iteration
                wkdir_su2 = Path(get_results_directory("SU2Run")) / f"SU2_{iteration}"
                wkdir_su2.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

                su2_dataset = launch_su2(
                    wkdir,
                    wkdir_su2,
                    cpacs_path,
                    cpacs_tmp_cfg,
                    objective_coefficient,
                    high_variance_points,
                )

                if "level_2" in datasets:
                    # Estrai i dati dalla tupla salvata
                    X_old, y_old, df_old, removed_old, df_cl_old = datasets["level_2"]
                    X_new, y_new, df_new, removed_new, df_cl_new = su2_dataset

                    # Concatenazione degli array NumPy
                    X_combined = np.vstack([X_old, X_new])  # Input
                    y_combined = np.vstack([y_old, y_new])  # Output

                    # Concatenazione dei DataFrame
                    df_combined = pd.concat([df_old, df_new], ignore_index=True)
                    df_cl_combined = pd.concat([df_cl_old, df_cl_new], ignore_index=True)

                    # Il dizionario non cambia (assumendo che sia vuoto)
                    removed_combined = (
                        removed_old  # Se servisse modificarlo, dipende dal contenuto
                    )

                    # Ricostruzione della tupla aggiornata
                    datasets["level_2"] = (
                        X_combined,
                        y_combined,
                        df_combined,
                        removed_combined,
                        df_cl_combined,
                    )

                else:
                    datasets["level_2"] = su2_dataset  # Primo inserimento

                # Train multi-fidelity Kriging model
                sets = split_data(datasets, 0.7, 0.5)
                model, rmse = train_surrogate_model(fidelity_level, datasets, sets)
                iteration += 1

            # Warn if max iterations reached without meeting RMSE threshold
            if iteration == max_iterations:
                log.warning("Maximum number of iterations reached. RMSE value > Threshold")

        else:
            raise ValueError("You must select 'One' or 'Two' as fidelity level")

    # If DoE is not used, load existing datasets from CSV
    else:
        datasets = get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective_coefficient)
        sets = split_data(datasets, data_repartition)

        # Train the surrogate model
        model, _ = train_surrogate_model(fidelity_level, datasets, sets)

        # Generate new dataset if required
        if new_dataset is True:
            new_doe(datasets, model, fraction_of_new_samples, wkdir)

    # Generate validation plots if required
    if show_plot is True:
        log.info("Validation plots")
        plot_validation(model, sets, objective_coefficient, wkdir)

    # Save the trained surrogate model
    save_model(model, objective_coefficient, datasets, wkdir)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    result_dir = get_results_directory("SMTrain")
    cpacs_tmp_cfg = Path(cpacs_out_path.parent, "ConfigTMP.xml")
    run_smTrain(cpacs_path, cpacs_tmp_cfg, result_dir)

    get_smt_results(cpacs_path, cpacs_out_path, result_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
