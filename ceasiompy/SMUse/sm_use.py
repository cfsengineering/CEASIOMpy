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
from ceasiompy.SMUse.func.smUconfig import (
    get_paths,
    load_surrogate,
    get_response_surface_values,
)
from ceasiompy.SMUse.func.smU_func import make_predictions, save_new_dataset, response_surface

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_smUse(cpacs_path, wkdir):
    model = load_surrogate(cpacs_path)
    # aeromap?
    prediction_dataset = load_surrogate(cpacs_path)
    # response surface
    predictions = make_predictions(cpacs_path, prediction_dataset, model)
    output_path = save_new_dataset(prediction_dataset, predictions, cpacs_path, wkdir)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    result_dir = get_results_directory("SMUse")
    run_smUse(cpacs_path, results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
