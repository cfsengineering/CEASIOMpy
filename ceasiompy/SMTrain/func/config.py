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

import pandas as pd

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import (
    aircraft_name,
    get_aeromap_list_from_xpath,
)
from ceasiompy.SMTrain.func.utils import (
    level_to_str,
    filter_constant_columns,
)

from numpy import ndarray
from pandas import DataFrame
from ceasiompy.Database.func.storing import CeasiompyDb
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
    AEROMAP_FEATURES,
    SMTRAIN_OBJECTIVE_XPATH,
    # SMTRAIN_NEWDOE,
    SMTRAIN_MAX_ALT,
    SMTRAIN_MAX_MACH,
    SMTRAIN_MAX_AOA,
    SMTRAIN_MAX_AOS,
    SMTRAIN_NSAMPLES_XPATH,
    SMTRAIN_PLOT_XPATH,
    # SMTRAIN_NEW_DATASET,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_AVL_DATABASE_XPATH,
    # SMTRAIN_NEWDATASET_FRAC_XPATH,
    SMTRAIN_TRAINING_AEROMAP_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_settings(cpacs: CPACS) -> Tuple[str, float, str, bool, bool, int, bool, float]:
    """
    Reads the global and new suggested dataset settings.
    """
    tixi = cpacs.tixi
    fidelity_level = get_value(tixi, SMTRAIN_FIDELITY_LEVEL_XPATH)
    data_repartition = get_value(tixi, SMTRAIN_TRAIN_PERC_XPATH)
    objective = get_value(tixi, SMTRAIN_OBJECTIVE_XPATH)
    show_plot = get_value(tixi, SMTRAIN_PLOT_XPATH)
    # new_dataset = get_value(tixi, SMTRAIN_NEW_DATASET)
    # fraction_of_new_samples = int(get_value(tixi, SMTRAIN_NEWDATASET_FRAC_XPATH))
    # doe = get_value(tixi, SMTRAIN_NEWDOE)
    rmse_obj = get_value(tixi, SMTRAIN_THRESHOLD_XPATH)
    log.info(f"Surrogate's model {objective=} with {fidelity_level=}")

    return (
        fidelity_level,
        data_repartition,
        objective,
        show_plot,
        # new_dataset,
        # fraction_of_new_samples,
        # doe,
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
    tixi = cpacs.tixi
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

    # If retrieve data from database
    # Append the data here
    if get_value(tixi, SMTRAIN_AVL_DATABASE_XPATH):
        # _, ranges = design_of_experiment(cpacs)
        aircraft: str = aircraft_name(tixi)
        ceasiompy_db = CeasiompyDb()
        data = ceasiompy_db.get_data(
            table_name="avl_data",
            columns=["alt", "mach", "alpha", "beta", objective],
            db_close=True,
            filters=[
                # f"mach IN ({ranges['machNumber'][0]}, {ranges['machNumber'][1]})",
                f"aircraft = '{aircraft}'",
                # f"alt IN ({ranges['altitude'][0]}, {ranges['altitude'][1]})",
                # f"alpha IN ({ranges['angleOfAttack'][0]}, {ranges['angleOfAttack'][1]})",
                # f"beta IN ({ranges['angleOfSideslip'][0]}, {ranges['angleOfSideslip'][1]})",
                "pb_2V = 0.0",
                "qc_2V = 0.0",
                "rb_2V = 0.0",
            ]
        )
        log.info(f"Importing from ceasiompy.db {data=}")
        data_df = DataFrame(data, columns=df.columns)
        df = pd.concat([df, data_df], ignore_index=True)

        # Post processing
        df = df.drop_duplicates(ignore_index=True)

    # Skip filtering if there is only one row
    # (important for adaptive sampling)
    if len(df) == 1:
        df_filtered = df.iloc[:, :4].copy()
        removed_columns = {}
    else:
        df_filtered, removed_columns = filter_constant_columns(df, AEROMAP_FEATURES)

    output = df[objective].values.reshape(-1, 1)

    return df_filtered.values, output, df_filtered, removed_columns, df


def get_aeromap_for_training(cpacs: CPACS) -> List[str]:
    tixi = cpacs.tixi

    if tixi.checkElement(SMTRAIN_TRAINING_AEROMAP_XPATH):
        # Using Aeromap for training
        aeromap_text = tixi.getTextElement(SMTRAIN_TRAINING_AEROMAP_XPATH).strip()
        if aeromap_text:
            # If there is text use this as a uid
            aeromap_uid_list = get_aeromap_list_from_xpath(
                cpacs, SMTRAIN_TRAINING_AEROMAP_XPATH
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


def design_of_experiment(cpacs: CPACS) -> Tuple[int, Dict]:
    """
    Retrieves the aeromap data,
    extracts the range for each input variable,
    and returns the number of samples and the defined ranges.
    """
    tixi = cpacs.tixi
    n_samples = int(get_value(tixi, SMTRAIN_NSAMPLES_XPATH))
    if n_samples <= 0:
        raise ValueError("New samples must be greater than 0.")
    max_alt = int(get_value(tixi, SMTRAIN_MAX_ALT))
    max_mach = float(get_value(tixi, SMTRAIN_MAX_MACH))
    max_aoa = int(get_value(tixi, SMTRAIN_MAX_AOA))
    max_aos = int(get_value(tixi, SMTRAIN_MAX_AOS))

    ranges: Dict[str, List[float]] = {
        "altitude": [0, max_alt],
        "machNumber": [0.1, max_mach],
        "angleOfAttack": [0, max_aoa],
        "angleOfSideslip": [0, max_aos],
    }
    log.info(f"Design of Experiment Settings for {n_samples=}.")
    for key, value in ranges.items():
        log.info(f"{value[0]} <= {key} <= {value[1]}")

    return n_samples, ranges
