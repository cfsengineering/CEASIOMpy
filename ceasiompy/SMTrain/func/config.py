"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get settings from GUI. Manage datasets and perform LHS when required.

| Author: Giacomo Gronda
| Creation: 2025-03-20

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath
from ceasiompy.SMTrain.func.utils import (
    level_to_str,
    filter_constant_columns,
)

from numpy import ndarray
from pandas import DataFrame
from typing import (
    List,
    Dict,
    Tuple,
)
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.PyAVL import AVL_AEROMAP_UID_XPATH
from ceasiompy.SU2Run import SU2_AEROMAP_UID_XPATH
from ceasiompy.SMTrain import (
    OBJECTIVES_LIST,
    SMTRAIN_XPATH,
    SMTRAIN_NEWDOE,
    SMTRAIN_NSAMPLES_XPATH,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_NEW_DATASET,
    SMTRAIN_AEROMAP_DOE_XPATH,
    SMTRAIN_AVL_OR_SU2_XPATH,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_NEWDATASET_FRAC_XPATH,
    SMTRAIN_AEROMAP_FOR_TRAINING_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_settings(cpacs: CPACS) -> Tuple[str, float, str, bool, bool, int, bool, bool, float]:
    """
    Reads the global and new suggested dataset settings.
    """

    # TODO: Add long paths (remove SMTRAIN_XPATH + ...)
    tixi = cpacs.tixi
    fidelity_level = get_value(tixi, SMTRAIN_FIDELITY_LEVEL_XPATH)
    data_repartition = get_value(tixi, SMTRAIN_TRAIN_PERC_XPATH)
    objective = get_value(tixi, SMTRAIN_XPATH + "/objective")
    show_plot = get_value(tixi, SMTRAIN_PLOT_XPATH)
    new_dataset = get_value(tixi, SMTRAIN_NEW_DATASET)
    fraction_of_new_samples = int(get_value(tixi, SMTRAIN_NEWDATASET_FRAC_XPATH))
    doe = get_value(tixi, SMTRAIN_NEWDOE)
    avl_or_su2 = get_value(tixi, SMTRAIN_AVL_OR_SU2_XPATH)
    rmse_obj = get_value(tixi, SMTRAIN_THRESHOLD_XPATH)
    avl = (avl_or_su2 == "AVL")

    if objective not in OBJECTIVES_LIST:
        raise ValueError(f"Invalid {objective=}. Choose from {list(OBJECTIVES_LIST.keys())}.")

    log.info("SMTrain Settings:")
    log.info(f"Fidelity Level: {fidelity_level}")
    log.info(f"Data Repartition: {data_repartition}")
    log.info(f"Objective: {objective}")
    log.info(f"Show Plot: {show_plot}")
    log.info(f"New Dataset: {new_dataset}")
    log.info(f"Fraction of New Samples: {fraction_of_new_samples}")
    log.info(f"DoE Enabled: {doe}")
    log.info(f"Aerodynamic Solver: {avl_or_su2}")
    log.info(f"RMSE Threshold: {rmse_obj}")

    return (
        fidelity_level,
        data_repartition,
        objective,
        show_plot,
        new_dataset,
        fraction_of_new_samples,
        doe,
        avl,
        rmse_obj,
    )


def retrieve_aeromap_data(
    cpacs: CPACS,
    aeromap_uid: str,
    objective: str,
) -> Tuple[ndarray, ndarray, DataFrame, Dict, DataFrame]:
    """
    Retrieves the aerodynamic data from a CPACS aeromap
    and prepares input-output data for training.
    """

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]
    activate_aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

    if activate_aeromap is None:
        raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

    log.info(f"Aeromap {aeromap_uid} retrieved successfully.")

    df = DataFrame({
        "altitude": activate_aeromap.get("altitude").tolist(),
        "machNumber": activate_aeromap.get("machNumber").tolist(),
        "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
        "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
        objective: activate_aeromap.get(objective).tolist(),
    })

    # Skip filtering if there is only one row
    # (important for adaptive sampling)
    if len(df) == 1:
        df_filtered = df.iloc[:, :4].copy()
        removed_columns = {}
    else:
        df_filtered, removed_columns = filter_constant_columns(df, input_columns)

    output = df[objective].values.reshape(-1, 1)

    return df_filtered.values, output, df_filtered, removed_columns, df


def get_aeromap_for_training(cpacs: CPACS) -> List[str]:
    tixi = cpacs.tixi

    if tixi.checkElement(SMTRAIN_AEROMAP_FOR_TRAINING_XPATH):
        # Using Aeromap for training
        aeromap_text = tixi.getTextElement(SMTRAIN_AEROMAP_FOR_TRAINING_XPATH).strip()
        if aeromap_text:
            # If there is text use this as a uid
            aeromap_uid_list = get_aeromap_list_from_xpath(
                cpacs, SMTRAIN_AEROMAP_FOR_TRAINING_XPATH
            )
            return aeromap_uid_list

    # Otherwise check 'AVL_AEROMAP_UID_XPATH'
    if tixi.checkElement(AVL_AEROMAP_UID_XPATH):
        avl_text = tixi.getTextElement(AVL_AEROMAP_UID_XPATH).strip()
        if avl_text:
            aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, AVL_AEROMAP_UID_XPATH)
            return aeromap_uid_list

    # Otherwise check 'SU2_AEROMAP_UID_XPATH'
    if tixi.checkElement(SU2_AEROMAP_UID_XPATH):
        su2_text = tixi.getTextElement(SU2_AEROMAP_UID_XPATH).strip()
        if su2_text:
            aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, SU2_AEROMAP_UID_XPATH)
            return aeromap_uid_list

    # If no valid aeromap is found
    # use the default aeromap
    if aeromap_uid_list is None:
        aeromap_uid_list = cpacs.get_aeromap_uid_list()

    if not aeromap_uid_list:
        # If the list is empty then no aeromaps were found
        raise ValueError("No aeromaps available.")

    return aeromap_uid_list


def get_datasets_from_aeromaps(
    cpacs: CPACS,
    objective: str,
) -> Dict:
    """
    Extracts datasets from multiple aeromaps
    based on the selected fidelity level and objective.

    Note:
        If SMTrain is used after PyAVL or SU2Run in the Workflow,
        it will retrieve their updated aeromaps.

    Returns:
        Dictionary containing datasets for each aeromap level, structured as:
            {
                LEVEL_ONE : (inputs, output, df_filtered, removed_columns, df),
                LEVEL_TWO : (inputs, output, df_filtered, removed_columns, df),
                ...
            }
    """
    # Initialize variables
    datasets = {}

    #
    aeromap_uid_list = get_aeromap_for_training(cpacs)

    for level, aeromap_uid in enumerate(aeromap_uid_list, start=1):
        log.info(f"Training dataset {level}: {aeromap_uid}")
        datasets[level_to_str(level)] = retrieve_aeromap_data(
            cpacs, aeromap_uid, objective
        )

    log.info(f"Datasets retrieved successfully for levels: {list(datasets.keys())}")
    return datasets


def get_aeromap(cpacs: CPACS) -> Tuple[DataFrame, int]:
    tixi = cpacs.tixi
    n_samples = int(get_value(tixi, SMTRAIN_NSAMPLES_XPATH))
    aeromap_uid = get_value(tixi, SMTRAIN_AEROMAP_DOE_XPATH)

    if not aeromap_uid:
        log.error("No aeromap found for DoE in the CPACS file.")
        raise ValueError("No aeromap available for DoE.")

    log.info(f"Aeromap for DoE: {aeromap_uid}")
    aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

    return aeromap.df, n_samples


def design_of_experiment(cpacs: CPACS) -> Tuple[int, Dict]:
    """
    Retrieves the aeromap data,
    extracts the range for each input variable,
    and returns the number of samples and the defined ranges.
    """

    aeromap_df, n_samples = get_aeromap(cpacs)

    try:
        ranges = {
            "altitude": [
                aeromap_df["altitude"].iloc[0],
                aeromap_df["altitude"].iloc[1],
            ],
            "machNumber": [
                aeromap_df["machNumber"].iloc[0],
                aeromap_df["machNumber"].iloc[1],
            ],
            "angleOfAttack": [
                aeromap_df["angleOfAttack"].iloc[0],
                aeromap_df["angleOfAttack"].iloc[1],
            ],
            "angleOfSideslip": [
                aeromap_df["angleOfSideslip"].iloc[0],
                aeromap_df["angleOfSideslip"].iloc[1],
            ],
        }

    except IndexError as e:
        log.error(f"Error accessing aeromap data: {e}")
        raise ValueError("Some issues with ranges provided")

    log.info(f"DoE settings - n_samples: {n_samples}, ranges: {ranges}")

    return n_samples, ranges


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
