# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
import pickle
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import MFSMTRAIN_XPATH
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_paths(cpacs_path):

    cpacs = CPACS(cpacs_path)

    prediction_dataset = get_value_or_default(
        cpacs.tixi, MFSMUSE_XPATH + "/predictionDataset", None
    )

    return prediction_dataset


def load_surrogate(cpacs_path):

    cpacs = CPACS(cpacs_path)

    model_path = get_value_or_default(cpacs.tixi, MFSMUSE_XPATH + "/modelFile", None)

    log.info("Trying to open surrogate model" + model_path)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    return model


def get_response_surface_values(cpacs_path):

    cpacs = CPACS(cpacs_path)

    x_rs = get_value_or_default(cpacs.tixi, MFSMUSE_RS + "/VariableOnX", "angleOfAttack")
    y_rs = get_value_or_default(cpacs.tixi, MFSMUSE_RS + "/VariableOnY", "machNumber")

    return x_rs, y_rs


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
