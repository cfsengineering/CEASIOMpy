"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import joblib

from pathlib import Path
from pandas import DataFrame
from smt.applications import MFK
from smt.surrogate_models import KRG
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from typing import (
    List,
    Dict,
    Tuple,
    Union,
)

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

from ceasiompy import log
from ceasiompy.SMUse import SMUSE_DATASET
from ceasiompy.utils.commonxpaths import SM_XPATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_predictions_dataset(
    cpacs: CPACS
    #, removed_columns: List
) -> Dict:
    """
    Extracts the dataset for predictions from the CPACS file
    by reading the specified aeromaps.
    """

    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, SMUSE_DATASET)

    # Check if there are any aeromaps available
    if not aeromap_uid_list:
        log.error("No aeromaps found in the CPACS file.")
        raise ValueError("No aeromaps available.")

    dataset_dict = {}
    for idx, aeromap_uid in enumerate(aeromap_uid_list, start=1):
        activate_aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

        log.info(f"Prediction dataset: {aeromap_uid}")

        # Ensure that the aeromap exists before processing
        if activate_aeromap is None:
            log.error(f"Aeromap {aeromap_uid} not found.")
            raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

        df = DataFrame({
            "altitude": activate_aeromap.get("altitude").tolist(),
            "machNumber": activate_aeromap.get("machNumber").tolist(),
            "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
            "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
        })

        # df_filtered = df.drop(
        #     columns=[col for col in removed_columns if col in df.columns],
        #     errors="ignore",
        # )

        df_filtered = df

        # Store results in the dictionary
        dataset_dict[f"prediction_dataset_{idx}"] = {
            "df_filtered": df_filtered,  # Filtered DataFrame (without constant columns)
            # "removed_columns": removed_columns,  # List of removed constant columns
            "df_original": df,  # Original unfiltered DataFrame
        }

        log.debug(f"Filtered dataset:\n{df_filtered}")
        # log.debug(f"Removed columns: {removed_columns}")

    log.info("Completed dataset extraction.")
    return dataset_dict


def load_surrogate(cpacs: CPACS) -> Tuple[Union[MFK, KRG], str, Dict]:
    """
    Loads the surrogate model and metadata from the CPACS file.
    """

    # Retrieve the model path from CPACS
    model_path = Path(get_value(cpacs.tixi, SM_XPATH))
    if not model_path or not model_path.exists():
        raise FileNotFoundError(f"Surrogate model file not found: {model_path}")

    # Load the model and its metadata
    with open(model_path, "rb") as file:
        model_metadata = joblib.load(file)

    model = model_metadata["model"]
    coefficient_name = model_metadata["coefficient"]
    # removed_columns = model_metadata["removed_columns"]

    log.info("Surrogate model successfully loaded.")
    log.debug(f"Model: {model}")
    log.debug(f"Coefficient name: {coefficient_name}")
    # log.debug(f"Removed columns: {removed_columns}")

    dataset_dict = get_predictions_dataset(cpacs)  # , removed_columns

    return model, coefficient_name, dataset_dict
