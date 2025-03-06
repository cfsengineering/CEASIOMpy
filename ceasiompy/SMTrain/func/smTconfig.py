# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

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

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_setting(cpacs_path):

    cpacs = CPACS(cpacs_path)

    fidelity_level = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/fidelityLevel", 3)
    data_repartition = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/trainingPercentage", 0.7)
    objective = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/objective", "Total CL")

    print(f"fid_lev: {fidelity_level}")
    print(f"d_rep: {data_repartition}")
    print(f"obj: {objective}")

    return fidelity_level, data_repartition, objective


def plots_and_new_dataset(cpacs_path):

    cpacs = CPACS(cpacs_path)

    show_plot = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/ValidationPlot", False)
    new_dataset = get_value_or_default(cpacs.tixi, SMTRAIN_XPATH + "/newDataset", False)
    fraction_of_new_samples = get_value_or_default(
        cpacs.tixi, SMTRAIN_XPATH + "/newDatasetFraction", 2
    )

    return show_plot, new_dataset, fraction_of_new_samples


def response_surface_inputs(cpacs_path):

    cpacs = CPACS(cpacs_path)

    response_surface = get_value_or_default(cpacs.tixi, SMTRAIN_RS, False)
    x_rSurf = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnX", "angleOfAttack")
    x_rSurf_low_limit = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnX/LowLimit", 0.0)
    x_rSurf_high_limit = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/VariableOnX/HighLimit", 0.0
    )
    y_rSurf = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnY", "machNumber")
    y_rSurf_low_limit = get_value_or_default(cpacs.tixi, SMTRAIN_RS + "/VariableOnY/LowLimit", 0.0)
    y_rSurf_high_limit = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/VariableOnY/HighLimit", 0.0
    )
    first_constant_variable = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/FirstConstantVariable", "altitude"
    )
    val_of_first_constant_variable = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/FirstConstantVariable/value", 1000
    )
    second_constant_variable = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/SecondConstantVariable", "angleOfSideslip"
    )
    val_of_second_constant_variable = get_value_or_default(
        cpacs.tixi, SMTRAIN_RS + "/SecondConstantVariable/value", 0
    )

    const_var = {
        first_constant_variable: val_of_first_constant_variable,
        second_constant_variable: val_of_second_constant_variable,
    }

    return (
        response_surface,
        x_rSurf,
        x_rSurf_low_limit,
        x_rSurf_high_limit,
        y_rSurf,
        y_rSurf_low_limit,
        y_rSurf_high_limit,
        const_var,
    )


def get_paths(cpacs_path, fidelity_level):

    # da capire se lasciare il valore di default (quindi "-") oppure fare in modo che il dict abbia solo i path
    # in caso aggiornare anche il ciclo for in "extract_data_set"

    cpacs = CPACS(cpacs_path)

    dataset_paths = {}

    if fidelity_level >= 1:
        dataset_paths["first_dataset_path"] = get_value_or_default(
            cpacs.tixi, SMTRAIN_XPATH + "/csvPath1", None
        )
        log.info(f"First dataset path: {dataset_paths['first_dataset_path']}")

    if fidelity_level >= 2:
        dataset_paths["second_dataset_path"] = get_value_or_default(
            cpacs.tixi, SMTRAIN_XPATH + "/csvPath2", None
        )
        log.info(f"Second dataset path: {dataset_paths['second_dataset_path']}")

    if fidelity_level == 3:
        dataset_paths["third_dataset_path"] = get_value_or_default(
            cpacs.tixi, SMTRAIN_XPATH + "/csvPath3", None
        )
        log.info(f"Third dataset path: {dataset_paths['third_dataset_path']}")

    return dataset_paths


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
