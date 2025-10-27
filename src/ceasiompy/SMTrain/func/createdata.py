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
from ceasiompy.utils.guisettings import update_gui_settings_from_specs
from ceasiompy.SMTrain.func.config import (
    retrieve_aeromap_data,
    retrieve_ceasiompy_db_data,
)
from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
)

from typing import Union
from pathlib import Path
from pandas import DataFrame
from unittest.mock import MagicMock
from ceasiompy.utils.guisettings import GUISettings
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.SU2Run import SU2_MAX_ITER_XPATH
from ceasiompy.SMTrain.func import LH_SAMPLING_DATA
from ceasiompy.SMTrain import SMTRAIN_AVL_DATABASE_XPATH
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.SU2Run import (
    SU2_AEROMAP_UID_XPATH,
    MODULE_NAME as SU2RUN_NAME,
)
from ceasiompy.utils.guixpaths import (
    SU2MESH_XPATH,
    USED_SU2_MESH_XPATH,
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
        gui_settings: GUISettings = update_gui_settings_from_specs(
            cpacs=cpacs,
            gui_settings=None,
            module_name=PYAVL_NAME,
            test=True,
        )

        # Update CPACS with the new aeromap
        gui_settings.tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap.uid)
        gui_settings.save()

        run_avl(
            cpacs=cpacs,
            gui_settings=gui_settings,
            results_dir=get_results_directory(PYAVL_NAME),
        )
        df_aeromap = retrieve_aeromap_data(cpacs, aeromap.uid, objective)

    if get_value(tixi, SMTRAIN_AVL_DATABASE_XPATH):
        df_db = retrieve_ceasiompy_db_data(tixi, objective)
        if df_aeromap is not None:
            df_aeromap = concat([df_aeromap, df_db], ignore_index=True)
        else:
            df_aeromap = df_db

    # Log the generated dataset, with objective values
    log.info(f"Level one results extracted for {objective}:")
    log.info(df_aeromap)

    return df_aeromap


def launch_su2(
    cpacs: CPACS,
    results_dir: Path,
    objective: str,
    high_variance_points: Union[str, None] = None,
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """
    tixi = cpacs.tixi
    su2mesh, su2_mesh_path = None, None
    aeromap = create_aeromap_from_varpts(cpacs, results_dir, high_variance_points)

    # Load default parameters
    st.session_state = MagicMock()

    if tixi.checkElement(SU2MESH_XPATH):
        su2mesh = get_value(tixi, SU2MESH_XPATH)
    if tixi.checkElement(USED_SU2_MESH_XPATH):
        su2_mesh_path = tixi.getTextElement(USED_SU2_MESH_XPATH)
        if not su2_mesh_path:
            su2_mesh_path = None

    su2_mesh_path_type = get_value(tixi, USED_SU2_MESH_XPATH + "type")
    max_iters = str(get_value(tixi, SU2_MAX_ITER_XPATH))
    update_gui_settings_from_specs(cpacs, SU2RUN_NAME, test=True)

    # Update CPACS with the new aeromap and su2 mesh paths
    tixi.updateTextElement(USED_SU2_MESH_XPATH + "type", su2_mesh_path_type)
    tixi.updateTextElement(SU2_AEROMAP_UID_XPATH, aeromap.uid)
    tixi.updateTextElement(SU2_MAX_ITER_XPATH, max_iters)

    if su2mesh is not None:
        tixi.updateTextElement(SU2MESH_XPATH, su2mesh)
    if su2_mesh_path is not None:
        tixi.updateTextElement(USED_SU2_MESH_XPATH, su2_mesh_path)

    # Run SU2 calculations
    run_su2(cpacs, results_dir=get_results_directory(SU2RUN_NAME))

    # Retrieve aerodynamic data, save then overwrite cpacs file
    df = retrieve_aeromap_data(cpacs, aeromap.uid, objective)
    log.info(f"Level two results extracted for {objective}:")
    log.info(df)

    return df
