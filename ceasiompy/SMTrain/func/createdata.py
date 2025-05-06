"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from pandas import concat
from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.SU2Run.su2run import main as run_su2
from ceasiompy.SMTrain.func.utils import create_aeromap_from_varpts
from ceasiompy.SMTrain.func.config import (
    retrieve_aeromap_data,
    retrieve_ceasiompy_db_data,
)
from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
    update_cpacs_from_specs,
)

from typing import Union
from pathlib import Path
from pandas import DataFrame
from unittest.mock import MagicMock
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.SMTrain.func import LH_SAMPLING_DATA
from ceasiompy.SMTrain import (
    SMTRAIN_AVL_DATABASE_XPATH,
    SMTRAIN_USED_SU2_MESH_XPATH,
)
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.SU2Run import (
    USED_SU2_MESH_XPATH,
    SU2_AEROMAP_UID_XPATH,
    MODULE_NAME as SU2RUN_NAME,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def launch_avl(
    cpacs: CPACS,
    lh_sampling_path: Union[Path, None],
    objective: str,
) -> DataFrame:
    """
    Executes AVL aerodynamic analysis running PyAVL Module

    This function processes a CPACS file, integrates a new aeromap from a previously
    generated dataset, and runs PyAVL module to compute aerodynamic coefficients.

    Returns:
        DataFrame: Contains AVL results for the requested objective.
    """
    tixi = cpacs.tixi

    # Remove existing aeromap if present
    if tixi.uIDCheckExists(LH_SAMPLING_DATA):
        cpacs.delete_aeromap(LH_SAMPLING_DATA)

    aeromap = AeroMap(tixi, uid="ceasiompy_db", create_new=True)
    df_aeromap = None
    if lh_sampling_path is not None:
        # Overwrite aeromap from LHS dataset
        aeromap = cpacs.create_aeromap_from_csv(lh_sampling_path)
        aeromap.save()

        # Run AVL analysis
        st.session_state = MagicMock()
        update_cpacs_from_specs(cpacs, PYAVL_NAME, test=True)

        # Update CPACS with the new aeromap
        tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap.uid)
        cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
        cpacs = CPACS(cpacs.cpacs_file)
        run_avl(cpacs, results_dir=get_results_directory(PYAVL_NAME))
        df_aeromap = retrieve_aeromap_data(cpacs, aeromap.uid, objective)

    if get_value(tixi, SMTRAIN_AVL_DATABASE_XPATH):
        df_db = retrieve_ceasiompy_db_data(tixi, objective)
        if df_aeromap is not None:
            df_aeromap = concat([df_aeromap, df_db], ignore_index=True)

    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
    cpacs = CPACS(cpacs.cpacs_file)

    # Log the generated dataset, with objective values
    log.info(f"Level one results extracted for {objective}:")
    log.info(df_aeromap)

    return df_aeromap


def launch_su2(
    cpacs: CPACS,
    results_dir: Path,
    objective: str,
    high_variance_points=None,  # TODO: For sure there is an issue with this argument
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """
    tixi = cpacs.tixi
    aeromap = create_aeromap_from_varpts(cpacs, results_dir, high_variance_points)

    # Load default parameters
    st.session_state = MagicMock()
    update_cpacs_from_specs(cpacs, SU2RUN_NAME, test=True)

    # Update CPACS with the new aeromap
    tixi.updateTextElement(SU2_AEROMAP_UID_XPATH, aeromap.uid)

    # Update CPACS with dynamic mesh path and settings
    su2_mesh_path = get_value(tixi, SMTRAIN_USED_SU2_MESH_XPATH)
    tixi.updateTextElement(USED_SU2_MESH_XPATH, su2_mesh_path)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
    cpacs = CPACS(cpacs.cpacs_file)
    run_su2(cpacs, results_dir=get_results_directory(SU2RUN_NAME))

    # Retrieve aerodynamic data, save then overwrite cpacs file
    cpacs = CPACS(cpacs.cpacs_file)
    df = retrieve_aeromap_data(cpacs, aeromap.uid, objective)
    cpacs.save_cpacs(cpacs, overwrite=True)

    log.info(f"Level two results extracted for {objective}:")
    log.info(df)

    return df
