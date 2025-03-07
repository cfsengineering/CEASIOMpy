# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
import pickle
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SMUSE_XPATH
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_paths(cpacs_path):

    cpacs = CPACS(cpacs_path)

    prediction_dataset = get_value_or_default(cpacs.tixi, SMUSE_XPATH + "/predictionDataset", None)

    return prediction_dataset


def load_surrogate(cpacs_path):

    cpacs = CPACS(cpacs_path)

    model_path = get_value_or_default(cpacs.tixi, SMUSE_XPATH + "/modelFile", None)

    log.info("Trying to open surrogate model" + model_path)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    return model


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
