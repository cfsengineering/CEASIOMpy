"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

''''Script to run .....

Python version: >=3.8

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:

    * Things to improve ...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.SMTrain.func.smTconfig import (
    get_setting,
    # get_paths,
    DoE,
    plots_and_new_dataset,
    # response_surface_inputs,
    get_datasets_from_aeromaps,
)
from ceasiompy.SMTrain.func.smTfunc import (
    # extract_data_set,
    split_data,
    train_surrogate_model,
    save_model,
    plot_validation,
    # response_surface,
    new_doe,
)
from ceasiompy.SMTrain.func.smTresults import get_smt_results
from pathlib import Path

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_smTrain(cpacs_path, wkdir):
    fidelity_level, data_repartition, objective_coefficent = get_setting(cpacs_path)
    # dataset_paths = get_paths(cpacs_path, fidelity_level)
    datasets = get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective_coefficent)
    show_plot, new_dataset, fraction_of_new_samples = plots_and_new_dataset(cpacs_path)
    # (
    #     response_surface_plot,
    #     x_rSurf,
    #     x_rSurf_low_limit,
    #     x_rSurf_high_limit,
    #     y_rSurf,
    #     y_rSurf_low_limit,
    #     y_rSurf_high_limit,
    #     const_var,
    # ) = response_surface_inputs(cpacs_path)
    # datasets = extract_data_set(dataset_paths, objective_coefficent, wkdir)

    sets = split_data(datasets, data_repartition)
    model = train_surrogate_model(fidelity_level, datasets, sets)
    if show_plot is True:
        log.info("Validation plots")
        plot_validation(model, sets, objective_coefficent)
    if new_dataset is True:
        new_doe(datasets, model, fraction_of_new_samples, wkdir)
    save_model(model, objective_coefficent, wkdir)

    # if response_surface_plot is True:


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    result_dir = get_results_directory("SMTrain")
    run_smTrain(cpacs_path, result_dir)
    get_smt_results(cpacs_path, cpacs_out_path, result_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
