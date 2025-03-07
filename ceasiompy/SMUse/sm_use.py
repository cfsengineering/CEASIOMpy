"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author: Name
| Creation: YEAR-MONTH-DAY

TODO:

    * Things to improve ...
    * Things to add ...

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.SMUse.func.smUconfig import (
    get_paths,
    load_surrogate,
)
from ceasiompy.SMUse.func.smU_func import make_predictions, save_new_dataset

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_smUse(cpacs_path):
    model = load_surrogate(cpacs_path)
    # aggiungere funzione per recuperare il path del dataset SMTrain
    prediction_dataset = get_paths(cpacs_path)
    predictions = make_predictions(prediction_dataset, model)

    return prediction_dataset, predictions


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    result_dir = get_results_directory("SMUse")
    pred_dataset, preds = run_smUse(cpacs_path)
    save_new_dataset(pred_dataset, preds, result_dir, cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
