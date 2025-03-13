# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import pandas as pd
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    SMTRAIN_XPATH,
    SMTRAIN_RS,
    SMTRAIN_DOE,
    SMTRAIN_SM_XPATH,
)
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.smTfunc import filter_constant_columns

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


# def response_surface_inputs(cpacs_path):

#     cpacs = CPACS(cpacs_path)

#     response_surface = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/Plot", False)
#     x_rSurf = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnX", "angleOfAttack")
#     x_rSurf_low_limit = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnX/LowLimit", 0.0)
#     x_rSurf_high_limit = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/VariableOnX/HighLimit", 0.0
#     )
#     y_rSurf = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnY", "machNumber")
#     y_rSurf_low_limit = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnY/LowLimit", 0.0)
#     y_rSurf_high_limit = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/VariableOnY/HighLimit", 0.0
#     )
#     first_constant_variable = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/FirstConstantVariable", "altitude"
#     )
#     val_of_first_constant_variable = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/FirstConstantVariable/value", 1000
#     )
#     second_constant_variable = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/SecondConstantVariable", "angleOfSideslip"
#     )
#     val_of_second_constant_variable = get_value_or_default(
#         cpacs.tixi, SMTRAIN_RS + "/SecondConstantVariable/value", 0
#     )

#     const_var = {
#         first_constant_variable: val_of_first_constant_variable,
#         second_constant_variable: val_of_second_constant_variable,
#     }

#     return (
#         response_surface,
#         x_rSurf,
#         x_rSurf_low_limit,
#         x_rSurf_high_limit,
#         y_rSurf,
#         y_rSurf_low_limit,
#         y_rSurf_high_limit,
#         const_var,
#     )


def get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective):
    cpacs = CPACS(cpacs_path)
    aeromap_list = cpacs.get_aeromap_uid_list()

    if not aeromap_list:
        log.error("No aeromaps found in the CPACS file.")
        raise ValueError("No aeromaps available.")

    datasets = {}
    aeromap_default = aeromap_list[0]  # Usa il primo aeromap come default

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}

    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Choose from {list(objective_map.keys())}."
        )

    def retrieve_aeromap_data(aeromap_uid):
        activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        print(activate_aeromap)

        if not activate_aeromap:
            log.error(f"Aeromap {aeromap_uid} not found.")
            raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

        df = pd.DataFrame(
            {
                "altitude": activate_aeromap.get("altitude").tolist(),
                "machNumber": activate_aeromap.get("machNumber").tolist(),
                "angleOfAttack": activate_aeromap.get("angleOfAttack").tolist(),
                "angleOfSideslip": activate_aeromap.get("angleOfSideslip").tolist(),
                objective_map[objective]: activate_aeromap.get(objective_map[objective]).tolist(),
            }
        )

        df_filtered, removed_columns = filter_constant_columns(
            df, input_columns
        )  # Rimuove colonne costanti

        inputs = df_filtered.values
        output = df[objective_map[objective]].values.reshape(-1, 1)

        return inputs, output, df_filtered, removed_columns, df

    for level in range(1, min(fidelity_level, 3) + 1):  # cosi al massimo 3 liveeli di fedelta'
        aeromap_uid = get_value_or_default(
            cpacs.tixi, f"{SMTRAIN_XPATH}/trainingDataset{level}", aeromap_default
        )

        log.info(f"Training dataset {level}: {aeromap_uid}")

        try:
            datasets[f"level_{level}"] = retrieve_aeromap_data(aeromap_uid)
        except ValueError as e:
            log.warning(f"Skipping level {level} due to error: {e}")

    cpacs.save_cpacs(cpacs_path, overwrite=True)

    return datasets


# def get_datasets_from_aeromaps(cpacs_path, fidelity_level, objective):
#     cpacs = CPACS(cpacs_path)
#     aeromap_list = cpacs.get_aeromap_uid_list()

#     if not aeromap_list:
#         log.error("No aeromaps found in the CPACS file.")
#         raise ValueError("No aeromaps available.")

#     aeromap_default = aeromap_list[0]  # Usa il primo aeromap come default
#     datasets = {}
#     objective_map = {
#         "Total CL": "cl",
#         "Total CD": "cd",
#         "Total CM": "cmd",
#     }

#     if objective not in objective_map:
#         raise ValueError(
#             f"Invalid objective '{objective}'. Choose from {list(objective_map.keys())}."
#         )

#     # Funzione per recuperare i dati dall'aeromap
#     def retrieve_aeromap_data(aeromap_uid):
#         activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
#         if not activate_aeromap:
#             log.error(f"Aeromap {aeromap_uid} not found.")
#             raise ValueError(f"Aeromap {aeromap_uid} does not exist.")

#         alt_list = activate_aeromap.get("altitude").tolist()
#         mach_list = activate_aeromap.get("machNumber").tolist()
#         aoa_list = activate_aeromap.get("angleOfAttack").tolist()
#         aos_list = activate_aeromap.get("angleOfSideslip").tolist()
#         objective_list = activate_aeromap.get(objective_map[objective]).tolist()

#         inputs = np.column_stack((alt_list, mach_list, aoa_list, aos_list))
#         output = np.column_stack((objective_list))  # Mantiene la forma (N, 1)

#         return inputs, output

#     # Recupera il dataset per il primo livello di fedeltà
#     if fidelity_level >= 1:
#         aeromap_uid = get_value_or_default(
#             cpacs.tixi, SMTRAIN_XPATH + "/trainingDataset1", aeromap_default
#         )
#         log.info(f"The first training dataset is {aeromap_uid}")
#         inputs1, output1 = retrieve_aeromap_data(aeromap_uid)
#         datasets["level_1"] = (inputs1, output1)

#     # Recupera il dataset per il secondo livello di fedeltà
#     if fidelity_level >= 2:
#         aeromap_uid = get_value_or_default(
#             cpacs.tixi, SMTRAIN_XPATH + "/trainingDataset2", aeromap_default
#         )
#         log.info(f"The second training dataset is {aeromap_uid}")
#         inputs2, output2 = retrieve_aeromap_data(aeromap_uid)
#         datasets["level_2"] = (inputs2, output2)

#     # Recupera il dataset per il terzo livello di fedeltà
#     if fidelity_level >= 3:
#         aeromap_uid = get_value_or_default(
#             cpacs.tixi, SMTRAIN_XPATH + "/trainingDataset3", aeromap_default
#         )
#         log.info(f"The third training dataset is {aeromap_uid}")
#         inputs3, output3 = retrieve_aeromap_data(aeromap_uid)
#         datasets["level_3"] = (inputs3, output3)

#     # Salva i cambiamenti nel file CPACS
#     cpacs.save_cpacs(cpacs_path, overwrite=True)

#     return datasets


def DoE(cpacs_path):
    cpacs = CPACS(cpacs_path)

    n_samples = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/nSamples", 100)
    ranges = {
        "altitude": [
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/altitudeMin", 0),
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/altitudeMax", 1000),
        ],
        "machNumber": [
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/machNumberMin", 0),
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/machNumberMax", 0.3),
        ],
        "angleOfAttack": [
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/angleOfAttackMin", 0),
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/angleOfAttackMax", 10),
        ],
        "angleOfSideslip": [
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/angleOfSideslip", 0),
            get_value_or_default(cpacs.tixi, SMTRAIN_DOE + "/angleOfSideslip", 0),
        ],
    }

    return n_samples, ranges


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
