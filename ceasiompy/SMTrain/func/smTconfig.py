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
)
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.smTfunc import filter_constant_columns
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_setting(cpacs_path):

    cpacs = CPACS(cpacs_path)

    fidelity_level = int(get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/fidelityLevel", 1))
    data_repartition = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/trainingPercentage", 0.7)
    objective = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/objective", "cl")

    log.info(f"fid_lev: {fidelity_level}")
    log.info(f"d_rep: {data_repartition}")
    log.info(f"obj: {objective}")

    return fidelity_level, data_repartition, objective


def plots_and_new_dataset(cpacs_path):

    cpacs = CPACS(cpacs_path)

    show_plot = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/ValidationPlot", True)
    new_dataset = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/newDataset", True)
    fraction_of_new_samples = int(
        get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/newDatasetFraction", 2)
    )

    log.info(f"show_plot: {show_plot}")
    log.info(f"new_dataset: {new_dataset}")
    log.info(f"fraction_of_new_samples: {fraction_of_new_samples}")

    return show_plot, new_dataset, fraction_of_new_samples


def retrieve_aeromap_data(cpacs, aeromap_uid, objective, objective_map):

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    if activate_aeromap is None:
        log.error(f"Aeromap {aeromap_uid} not found.")
        raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

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

    # Filtra le colonne costanti
    df_filtered, removed_columns = filter_constant_columns(df, input_columns)

    # Estrai gli input e l'output
    inputs = df_filtered.values
    output = df[objective_map[objective]].values.reshape(-1, 1)

    return inputs, output, df_filtered, removed_columns, df


def get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective):
    cpacs = CPACS(cpacs_path)

    aeromap_for_training_xpath = SMTRAIN_XPATH + "/aeromapForTraining"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_for_training_xpath)

    if not aeromap_uid_list:
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

    log.info(f"datasets: {datasets}")
    return datasets


def get_doe_settings(cpacs_path):
    cpacs = CPACS(cpacs_path)

    doe = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/newDoe", False)
    fidelity_level_doe = get_value_or_default(
        cpacs.tixi, SMTRAIN_DOE + "/fidelityLevel", "One Level"
    )
    avl = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/AVL", True)
    su2 = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/SU2", False)
    rmse_obj = get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/rmseThreshold", 0.05)

    return doe, fidelity_level_doe, avl, su2, rmse_obj


def DoE(cpacs_path):
    cpacs = CPACS(cpacs_path)

    n_samples = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/nSamples", 100)

    aeromap_for_doe_xpath = SMTRAIN_XPATH + "/aeromapForDoe"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_for_doe_xpath)
    aeromap_df = cpacs.get_aeromap_by_uid(aeromap_uid_list).df

    ranges = {
        "altitude": [
            aeromap_df["altitude"].iloc[0],
            aeromap_df["altitude"].iloc[1],
        ],
        "Mach": [
            aeromap_df["Mach"].iloc[0],
            aeromap_df["Mach"].iloc[1],
        ],
        "AoA": [
            aeromap_df["AoA"].iloc[0],
            aeromap_df["AoA"].iloc[1],
        ],
        "AoS": [
            aeromap_df["AoS"].iloc[0],
            aeromap_df["AoS"].iloc[1],
        ],
    }

    return n_samples, ranges


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
