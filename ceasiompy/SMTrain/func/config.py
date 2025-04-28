"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get settings from GUI. Manage datasets and perform LHS when required

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Move some functions to smTfunc

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pandas as pd

from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath
from cpacspy.cpacsfunctions import (
    open_tixi,
    get_value,
)

from pandas import DataFrame
from typing import (
    Dict,
    Tuple,
)
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.PyAVL import AVL_AEROMAP_UID_XPATH
from ceasiompy.utils.commonxpath import (
    SMTRAIN_XPATH,
    SMTRAIN_DOE,
    SU2_AEROMAP_UID_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_settings(cpacs: CPACS) -> Tuple[str, float, str, bool, bool, int, bool, str, float]:
    """
    Reads the global and new suggested dataset settings.

    Returns:
        fidelity_level (str)
        data_repartition (float): Training data percentage
        objective (str): model objective
        show_plot (bool)
        new_dataset (bool)
        fraction_of_new_samples (int): Factor for new dataset sample (fraction respect old)
    """
    # TODO: Add long paths (remove SMTRAIN_XPATH + ...)
    tixi = cpacs.tixi
    fidelity_level = get_value(tixi, SMTRAIN_XPATH + "/fidelityLevel")
    data_repartition = get_value(tixi, SMTRAIN_XPATH + "/trainingPercentage")
    objective = get_value(tixi, SMTRAIN_XPATH + "/objective")
    show_plot = get_value(tixi, SMTRAIN_XPATH + "/ValidationPlot")
    new_dataset = get_value(tixi, SMTRAIN_XPATH + "/newDataset")
    fraction_of_new_samples = int(get_value(tixi, SMTRAIN_XPATH + "/newDatasetFraction"))
    doe = get_value(tixi, SMTRAIN_DOE + "/newDoe")
    avl_or_su2 = get_value(tixi, SMTRAIN_DOE + "useAVLorSU2")
    rmse_obj = get_value(tixi, SMTRAIN_DOE + "/rmseThreshold")

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
        avl_or_su2,
        rmse_obj,
    )


def filter_constant_columns(df, input_columns):
    """Function to remove constant input columns from the dataset.

    Function 'filter_constant_columns' removes input columns that have a single unique value
    and stores their values separately.

    Args:
        df (pd.DataFrame): DataFrame containing the dataset.
        input_columns (list): List of input column names to check.

    Returns:
        tuple:
            - df_filtered (pd.DataFrame): DataFrame without constant columns.
            - removed_columns (dict): Dictionary of removed columns with their constant values.
    """

    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = {col: df[col].iloc[0] for col in input_columns if col not in columns_to_keep}

    if removed_columns:
        print(f"Removing constant columns: {list(removed_columns.keys())}")

    return df[columns_to_keep], removed_columns


def retrieve_aeromap_data(cpacs, aeromap_uid, objective, objective_map):
    """Function to extract aeromap data and prepare input-output datasets.

    Function 'retrieve_aeromap_data' retrieves the aerodynamic dataset from the CPACS aeromap
    and prepares input-output data for training.

    Args:
        cpacs (CPACS): CPACS object containing the aeromap data.
        aeromap_uid (str): Unique identifier of the aeromap.
        objective (str): Target aerodynamic coefficient (e.g., "cl", "cd").
        objective_map (dict): Mapping of objective names to their corresponding aeromap keys.

    Returns:
        tuple:
            - inputs (np.ndarray): Numpy array of input features (altitude, Mach, AoA, AoS).
            - output (np.ndarray): Numpy array of output values (target aerodynamic coefficient).
            - df_filtered (pd.DataFrame): Filtered DataFrame without constant input columns.
            - removed_columns (dict): Dictionary of removed columns and their values.
            - df (pd.DataFrame): Original unfiltered DataFrame.
    """

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    if activate_aeromap is None:
        log.error(f"Aeromap {aeromap_uid} not found.")
        raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

    log.info(f"Aeromap {aeromap_uid} retrieved successfully.")

    # Crea il DataFrame per l'aeromap con le colonne richieste
    df = pd.DataFrame(
        {
            "altitude": activate_aeromap.get("altitude").tolist(),
            "machNumber": activate_aeromap.get("machNumber").tolist(),
            "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
            "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
            objective_map[objective]: activate_aeromap.get(objective_map[objective]).tolist(),
        }
    )

    # Skip filtering if there is only one row (important for adaptive sampling)
    if len(df) == 1:
        df_filtered = df.iloc[:, :4].copy()
        removed_columns = {}
    else:
        df_filtered, removed_columns = filter_constant_columns(df, input_columns)

    # Estrai gli input e l'output
    inputs = df_filtered.values
    output = df[objective_map[objective]].values.reshape(-1, 1)

    return inputs, output, df_filtered, removed_columns, df


def get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective):
    """Function to retrieve datasets from multiple aeromaps.

    Function 'get_datasets_from_aeromaps' extracts datasets from multiple aeromaps
    based on the selected fidelity level and objective.
    If SMTrain is used after PyAVL or SU2 in the Workflow, it will retrieve their updated aeromaps.

    Args:
        cpacs_path (Path): Path to the CPACS input file.
        fidelity_level (str): Fidelity level of the dataset (e.g., "One level", "Multi-level").
        objective (str): Target aerodynamic coefficient (e.g., "cl", "cd").

    Returns:
        dict: Dictionary containing datasets for each aeromap level, structured as:
            {
                "level_1": (inputs, output, df_filtered, removed_columns, df),
                "level_2": (inputs, output, df_filtered, removed_columns, df),
                ...
            }
    """

    cpacs = CPACS(cpacs_path)
    tixi = open_tixi(cpacs_path)

    # If a csv file is provided is taken as aeromap, otherwise if SMTrain is in a Workflow
    # with other modules, their results are taken as aeromap

    # Check if 'aeromapForTraining' exists and is not empty
    if tixi.checkElement(SMTRAIN_XPATH + "/aeromapForTraining"):
        aeromap_text = tixi.getTextElement(SMTRAIN_XPATH + "/aeromapForTraining").strip()
        if aeromap_text:  # If it contains a valid value, use it
            aeromap_uid_list = get_aeromap_list_from_xpath(
                cpacs, SMTRAIN_XPATH + "/aeromapForTraining"
            )
        else:  # If empty, move to the next option
            aeromap_uid_list = None
    else:  # If the element does not exist, move to the next option
        aeromap_uid_list = None

    # If 'aeromapForTraining' is not valid, check 'AVL_AEROMAP_UID_XPATH'
    if aeromap_uid_list is None and tixi.checkElement(AVL_AEROMAP_UID_XPATH):
        avl_text = tixi.getTextElement(AVL_AEROMAP_UID_XPATH).strip()
        if avl_text:  # If it contains a valid value, use it
            aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, AVL_AEROMAP_UID_XPATH)

    # If AVL is not valid, check 'SU2_AEROMAP_UID_XPATH'
    if aeromap_uid_list is None and tixi.checkElement(SU2_AEROMAP_UID_XPATH):
        su2_text = tixi.getTextElement(SU2_AEROMAP_UID_XPATH).strip()
        if su2_text:  # If it contains a valid value, use it
            aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, SU2_AEROMAP_UID_XPATH)

    # If no valid aeromap is found, use the default method
    if aeromap_uid_list is None:
        aeromap_uid_list = cpacs.get_aeromap_uid_list()

    log.info(f"Aeromap list retrieved: {aeromap_uid_list}")
    # input()

    if not aeromap_uid_list:
        cpacs.get_aeromap_uid_list()

        log.error("No aeromaps found in the CPACS file.")
        raise ValueError("No aeromaps available.")

    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}

    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Choose from {list(objective_map.keys())}."
        )

    datasets = {}

    # Ciclo su ciascun aeromap_uid e assegnazione del livello
    for level, aeromap_uid in enumerate(aeromap_uid_list, start=1):
        log.info(f"Training dataset {level}: {aeromap_uid}")

        try:
            # Recupera i dati dell'aeromap per ogni livello e aggiungi al dizionario
            datasets[f"level_{level}"] = retrieve_aeromap_data(
                cpacs, aeromap_uid, objective, objective_map
            )
        except ValueError as e:
            log.warning(f"Skipping aeromap {aeromap_uid} due to error: {e}")

    log.info(f"Datasets retrieved successfully: {list(datasets.keys())}")
    return datasets


def get_aeromap(cpacs: CPACS) -> Tuple[DataFrame, int]:
    tixi = cpacs.tixi
    n_samples = int(get_value(tixi, SMTRAIN_DOE + "/nSamples"))
    aeromap_uid = get_value(tixi, SMTRAIN_XPATH + "/aeromapForDoe")

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
