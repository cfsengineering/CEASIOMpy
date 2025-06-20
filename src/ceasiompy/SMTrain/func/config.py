"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get settings from GUI. Manage datasets and perform LHS when required.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from cpacspy.cpacsfunctions import get_value
from ceasiompy.SMTrain.func.utils import get_columns
from ceasiompy.utils.ceasiompyutils import aircraft_name

from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3
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
from ceasiompy.SMTrain import (
    SMTRAIN_MAX_ALT,
    SMTRAIN_MAX_AOA,
    SMTRAIN_MAX_AOS,
    SMTRAIN_MAX_MACH,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_NSAMPLES_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
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
    rmse_obj = get_value(tixi, SMTRAIN_THRESHOLD_XPATH)
    log.info(f"Surrogate's model {objective=} with {fidelity_level=}")

    return (
        fidelity_level,
        data_repartition,
        objective,
        show_plot,
        rmse_obj,
    )


def retrieve_aeromap_data(
    cpacs: CPACS,
    aeromap_uid: str,
    objective: str,
) -> DataFrame:
    """
    Retrieves the aerodynamic data from a CPACS aeromap
    and prepares input-output data for training.
    """
    activate_aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
    log.info(f"Aeromap {aeromap_uid} retrieved successfully.")

    # Extract data as lists
    altitude = activate_aeromap.get("altitude").tolist()
    mach = activate_aeromap.get("machNumber").tolist()
    aoa = activate_aeromap.get("angleOfAttack").tolist()
    aos = activate_aeromap.get("angleOfSideslip").tolist()
    obj = activate_aeromap.get(objective).tolist()

    # Only keep rows where objective is not nan
    filtered = [
        (alt, m, a, s, o)
        for alt, m, a, s, o in zip(altitude, mach, aoa, aos, obj)
        if not np.isnan(o)
    ]

    return DataFrame(
        filtered,
        columns=get_columns(objective),
    )


def retrieve_ceasiompy_db_data(
    tixi: Tixi3,
    objective: str,
) -> DataFrame:
    """
    Get data from ceasiompy.db used in previous AVL computations.
    """
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
        ],
    )
    log.info(f"Importing from ceasiompy.db {data=}")
    data_df = DataFrame(
        data,
        columns=get_columns(objective),
    ).drop_duplicates(ignore_index=True)

    return data_df


def design_of_experiment(cpacs: CPACS) -> Tuple[int, Dict[str, List[float]]]:
    """
    Retrieves the aeromap data,
    extracts the range for each input variable,
    and returns the number of samples and the defined ranges.
    """
    tixi = cpacs.tixi
    n_samples = int(get_value(tixi, SMTRAIN_NSAMPLES_XPATH))
    if n_samples < 0:
        raise ValueError(
            "New samples can not be negative."
            "If you solely intend to use the data from ceasiompy.db, "
            "leave n_samples to 0."
            "Otherwise, try choose a high-enough n_samples >=7."
        )

    # Get the max ranges values
    max_alt = int(get_value(tixi, SMTRAIN_MAX_ALT))
    max_mach = float(get_value(tixi, SMTRAIN_MAX_MACH))  # .X numbers
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
