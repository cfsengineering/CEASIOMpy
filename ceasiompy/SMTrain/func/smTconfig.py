# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import pandas as pd
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    SMTRAIN_XPATH,
    SMTRAIN_DOE,
    SMTRAIN_SM_XPATH,
    AVL_AEROMAP_UID_XPATH,
    SU2_AEROMAP_UID_XPATH,
)
from cpacspy.cpacsfunctions import get_value_or_default, get_value, open_tixi
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_settings(cpacs_path):
    """Function to read the global and new suggested dataset settings from the aeromap

    Function 'get_settings' reads the global and new suggested dataset settings
    from the graphical user interface
    of CEASIOMPY.

    Args:
        cpacs_path (Path): Path to the CPACS input file.

    Returns:
        tuple: A tuple containing the following settings:
            - fidelity_level (str): Selected fidelity level (default: "One level").
            - data_repartition (float): Training data percentage (default: 0.7).
            - objective (str): Optimization objective, e.g., "cl" for lift coefficient (default: "cl").
            - show_plot (bool): Whether to display validation plots (default: False).
            - new_dataset (bool): Whether to generate a new dataset (default: False).
            - fraction_of_new_samples (int): Factor for new dataset sample increase (default: 2).
    """

    cpacs = CPACS(cpacs_path)

    fidelity_level = get_value_or_default(
        cpacs.tixi, SMTRAIN_XPATH + "/fidelityLevel", "One level"
    )
    data_repartition = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/trainingPercentage", 0.7)
    objective = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/objective", "cl")
    show_plot = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/ValidationPlot", False)
    new_dataset = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/newDataset", False)
    fraction_of_new_samples = int(
        get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/newDatasetFraction", 2)
    )

    log.info("SMTrain Setting:")
    log.info(f"Fidelity Level: {fidelity_level}")
    log.info(f"Data Repartition: {data_repartition}")
    log.info(f"Objective: {objective}")
    log.info(f"Show Plot: {show_plot}")
    log.info(f"New Dataset: {new_dataset}")
    log.info(f"Fraction of New Samples: {fraction_of_new_samples}")

    return (
        fidelity_level,
        data_repartition,
        objective,
        show_plot,
        new_dataset,
        fraction_of_new_samples,
    )


def get_doe_settings(cpacs_path):
    """Function to read the DoE settings from the aeromap.

    Function 'get_doe_settings' reads DoE settings
    from the graphical user interface of CEASIOMpy.

    Args:
        cpacs_path (Path): Path to the CPACS input file.

    Returns:
        tuple: A tuple containing the following settings:
            - doe (bool): Whether to use a new Design of Experiments (DoE) (default: False).
            - avl_or_su2 (str): Selected aerodynamic solver, either "AVL" or "SU2" (default: "AVL").
            - rmse_obj (float): Root Mean Square Error (RMSE) threshold for stopping criteria (default: 0.05).
    """

    cpacs = CPACS(cpacs_path)

    doe = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/newDoe", False)
    avl_or_su2 = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "useAVLorSU2", "AVL")
    rmse_obj = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/rmseThreshold", 0.05)

    log.info(f"DoE Enabled: {doe}")
    log.info(f"Aerodynamic Solver: {avl_or_su2}")
    log.info(f"RMSE Threshold: {rmse_obj}")

    return doe, avl_or_su2, rmse_obj


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

    # Skip filtering if there is only one row
    if len(df) == 1:
        df_filtered = df.copy()
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

    # If a csv file is provided is taken as aeromap, otherwise if SMTrain is in a Workflow with other
    # modules, their results are taken as aeromap

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


def DoE(cpacs_path):
    """Function to generate a Design of Experiments (DoE) from aeromap data.

    Function 'DoE' retrieves the aeromap data, extracts the range for each input variable,
    and returns the number of samples and the defined ranges.

    Args:
        cpacs_path (Path): Path to the CPACS input file.

    Returns:
        n_samples (int): Number of samples for the DoE.
        ranges (dict): Dictionary with input variables as keys and their min/max range as values.
    """

    cpacs = CPACS(cpacs_path)

    n_samples = int(get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/nSamples", 100))

    aeromap_uid = get_value(cpacs.tixi, SMTRAIN_XPATH + "/aeromapForDoe")

    if not aeromap_uid:
        log.error("No aeromap found for DoE in the CPACS file.")
        raise ValueError("No aeromap available for DoE.")

    log.info(f"Aeromap for DoE: {aeromap_uid}")

    aeromap_df = cpacs.get_aeromap_by_uid(aeromap_uid).df

    if aeromap_df is None or aeromap_df.empty:
        log.error("No valid aeromap data available for DoE.")
        raise ValueError("Aeromap data is empty or invalid.")

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
