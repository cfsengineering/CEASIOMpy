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
    get_doe_settings,
    DoE,
    plots_and_new_dataset,
    get_datasets_from_aeromaps,
)
from ceasiompy.SMTrain.func.smTfunc import (
    split_data,
    train_surrogate_model,
    save_model,
    plot_validation,
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
    datasets = get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective_coefficent)
    show_plot, new_dataset, fraction_of_new_samples = plots_and_new_dataset(cpacs_path)
    doe, fidelity_level_doe, avl, su2, rmse_obj = get_doe_settings(cpacs_path)
    sets = split_data(datasets, data_repartition)
    model = train_surrogate_model(fidelity_level, datasets, sets)

    if show_plot is True:
        log.info("Validation plots")
        plot_validation(model, sets, objective_coefficent)
    if new_dataset is True:
        new_doe(datasets, model, fraction_of_new_samples, wkdir)
    if doe is True:
        n_samples, ranges = DoE(cpacs_path)

    save_model(model, objective_coefficent, datasets, wkdir)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    result_dir = get_results_directory("SMTrain")
    model = run_smTrain(cpacs_path, result_dir)
    get_smt_results(cpacs_path, cpacs_out_path, result_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
