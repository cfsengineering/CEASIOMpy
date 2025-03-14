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
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


import pandas as pd


def get_predictions_dataset(cpacs_path, removed_columns):
    cpacs = CPACS(cpacs_path)

    # Define the XPath to retrieve aeromap UIDs for predictions
    aeromap_for_predictions_xpath = SMUSE_XPATH + "/predictionDataset"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_for_predictions_xpath)

    # Check if there are any aeromaps available
    if not aeromap_uid_list:
        log.error("No aeromaps found in the CPACS file.")
        raise ValueError("No aeromaps available.")

    # Dictionary to store all datasets
    dataset_dict = {}

    # Loop through each aeromap and process the data
    for idx, aeromap_uid in enumerate(aeromap_uid_list, start=1):  # Start numbering from 1
        activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        log.info(f"Prediction dataset: {aeromap_uid}")

        # Define input feature names
        input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

        # Ensure that the aeromap exists before processing
        if activate_aeromap is None:
            log.error(f"Aeromap {aeromap_uid} not found.")
            raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

        # Create the original DataFrame from the aeromap data
        df = pd.DataFrame(
            {
                "altitude": activate_aeromap.get("altitude").tolist(),
                "machNumber": activate_aeromap.get("machNumber").tolist(),
                "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
                "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
            }
        )

        # Rimuove le colonne specificate nei metadati del modello, se presenti
        df_filtered = df.drop(
            columns=[col for col in removed_columns if col in df.columns],
            errors="ignore",
        )

        # Store results in the dictionary
        dataset_dict[f"prediction_dataset_{idx}"] = {
            "df_filtered": df_filtered,  # Filtered DataFrame (without constant columns)
            "removed_columns": removed_columns,  # List of removed constant columns
            "df_original": df,  # Original unfiltered DataFrame
        }

        log.info(df_filtered)
        log.info(removed_columns)

    # Return the dictionary containing all processed datasets

    log.info(dataset_dict)

    return dataset_dict


def load_surrogate(cpacs_path):

    cpacs = CPACS(cpacs_path)

    model_path = Path(get_value(cpacs.tixi, SM_XPATH))
    if not model_path or not model_path.exists():
        raise FileNotFoundError(f"Surrogate model file not found: {model_path}")

    with open(model_path, "rb") as file:
        model_metadata = pickle.load(file)

    model = model_metadata["model"]
    coefficient_name = model_metadata["coefficient"]
    removed_columns = model_metadata["removed_columns"]

    log.info(f"model:{model}")
    log.info(f"coefficient_name:{coefficient_name}")
    log.info(f"removed_columns:{removed_columns}")

    return model, coefficient_name, removed_columns


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
