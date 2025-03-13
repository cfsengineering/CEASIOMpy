# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
import pandas as pd
import pickle
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SMUSE_XPATH, SMTRAIN_SM_XPATH, SM_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, get_value
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.smTfunc import filter_constant_columns

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_predictions_dataset(cpacs_path):

    cpacs = CPACS(cpacs_path)
    aeromap_list = cpacs.get_aeromap_uid_list()

    if not aeromap_list:
        log.error("No aeromaps found in the CPACS file.")
        raise ValueError("No aeromaps available.")

    dataset = {}
    aeromap_default = aeromap_list[0]  # Usa il primo aeromap come default
    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    aeromap_uid = get_value_or_default(
        cpacs.tixi, SMUSE_XPATH + "/predictionDataset", aeromap_default
    )
    log.info(f"Prediction dataset: {aeromap_uid}")

    activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    if activate_aeromap is None:
        log.error(f"Aeromap {aeromap_uid} not found.")
        raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

    df = pd.DataFrame(
        {
            "altitude": activate_aeromap.get("altitude").tolist(),
            "machNumber": activate_aeromap.get("machNumber").tolist(),
            "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
            "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
        }
    )

    df_filtered, removed_columns = filter_constant_columns(
        df, input_columns
    )  # Rimuove colonne costanti

    return df_filtered, removed_columns, df


def load_surrogate(cpacs_path):

    cpacs = CPACS(cpacs_path)

    model_path = Path(get_value(cpacs.tixi, SM_XPATH))
    if not model_path or not model_path.exists():
        raise FileNotFoundError(f"Surrogate model file not found: {model_path}")

    with open(model_path, "rb") as file:
        model_metadata = pickle.load(file)

    model = model_metadata["model"]
    coefficient_name = model_metadata["coefficient"]

    return model, coefficient_name


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
