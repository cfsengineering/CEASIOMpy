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
from ceasiompy.utils.guisettings import GUISettings
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from typing import (
    Dict,
    Tuple,
    Union,
)

from ceasiompy.SMTrain.func.utils import level_to_str
from cpacspy.cpacsfunctions import (
    get_value,
    get_string_vector,
)

from ceasiompy import log
from ceasiompy.SMUse import SMUSE_DATASET_XPATH
from ceasiompy.utils.guixpaths import SM_XPATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_predictions_dataset(
    cpacs: CPACS,
    gui_settings: GUISettings,
) -> Dict[str, DataFrame]:
    """
    Extracts the dataset for predictions from the CPACS file
    by reading the specified aeromaps.
    """

    aeromap_uid_list = get_string_vector(gui_settings, SMUSE_DATASET_XPATH)

    dataset_dict: Dict[str, DataFrame] = {}
    for idx, aeromap_uid in enumerate(aeromap_uid_list, start=1):
        activate_aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
        log.info(f"Prediction dataset: {aeromap_uid}")
        dataset_dict[level_to_str(idx)] = DataFrame(
            {
                "altitude": activate_aeromap.get("altitude").tolist(),
                "machNumber": activate_aeromap.get("machNumber").tolist(),
                "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
                "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
            }
        )

    log.info("Completed dataset extraction.")
    return dataset_dict


def load_surrogate(
    cpacs: CPACS,
    gui_settings: GUISettings,
) -> Tuple[Union[MFK, KRG], str, Dict[str, DataFrame]]:
    """
    Loads the surrogate model and metadata from the CPACS file.
    """

    # Retrieve the model path from CPACS
    model_path = Path(get_value(gui_settings.tixi, SM_XPATH))
    if not model_path or not model_path.exists():
        raise FileNotFoundError(f"Surrogate model file not found: {model_path}")

    # Load the model and its metadata
    with open(model_path, "rb") as file:
        model_metadata = joblib.load(file)

    model = model_metadata["model"]
    coefficient = model_metadata["coefficient"]

    log.info("Surrogate model loaded.")
    log.debug(f"{model=}, {coefficient=}")

    dataset_dict = get_predictions_dataset(
        cpacs=cpacs,
        gui_settings=gui_settings,
    )

    return model, coefficient, dataset_dict
