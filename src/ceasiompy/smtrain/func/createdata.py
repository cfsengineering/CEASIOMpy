"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import streamlit as st

from pandas import concat
from cpacspy.cpacsfunctions import get_value
from ceasiompy.pyavl.pyavl import main as run_avl
from ceasiompy.su2run.su2run import main as run_su2
from ceasiompy.cpacs2gmsh.cpacs2gmsh import main as run_cpacs2gmsh
from ceasiompy.smtrain.func.utils import (
    create_aeromap_from_varpts,
)
from ceasiompy.smtrain.func.config import (
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
from ceasiompy.su2run import SU2_MAX_ITER_XPATH
from ceasiompy.smtrain.func import AEROMAP_SELECTED
from ceasiompy.smtrain import (
    SMTRAIN_AVL_DATABASE_XPATH,
)
from ceasiompy.pyavl import (
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.su2run import (
    MODULE_NAME as SU2RUN_NAME,
)
from ceasiompy.utils.commonxpaths import (
    SU2MESH_XPATH,
    USED_SU2_MESH_XPATH,
    SELECTED_AEROMAP_XPATH,
)


# Functions

def launch_avl(
    cpacs: CPACS,
    lh_sampling_path: Union[Path, None],
    objective: str,
    result_dir: Path,
) -> DataFrame:

    """
    Executes AVL aerodynamic analysis running PyAVL Module

    This function processes a CPACS file, integrates a new aeromap from a previously
    generated dataset, and runs PyAVL module to compute aerodynamic coefficients.

    Returns:
        DataFrame: Contains AVL results for the requested objective.
    """
    tixi = cpacs.tixi
    avl_results_dir = Path(result_dir,"PyAVL")
    avl_results_dir.mkdir(exist_ok=True)

    # Remove existing aeromap if present
    if tixi.uIDCheckExists(AEROMAP_SELECTED):
        cpacs.delete_aeromap(AEROMAP_SELECTED)

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
        tixi.updateTextElement(SELECTED_AEROMAP_XPATH, aeromap.uid)
        run_avl(cpacs, results_dir=get_results_directory(PYAVL_NAME))
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

    update_cpacs_from_specs(cpacs, SU2RUN_NAME, test=True)
    max_iters = str(get_value(tixi, SU2_MAX_ITER_XPATH))

    # Update CPACS with the new aeromap and su2 mesh paths
    tixi.updateTextElement(USED_SU2_MESH_XPATH + "type", su2_mesh_path_type)
    tixi.updateTextElement(SELECTED_AEROMAP_XPATH, aeromap.uid)
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


def launch_gmsh_su2_geom(
    cpacs: CPACS,
    results_dir: Path,
    objective: str,
    aeromap_uid: str,
    idx: int,
    it: int,
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """
    gmsh_dir = results_dir / "CPACS2GMSH"
    gmsh_dir.mkdir(exist_ok=True)
    su2_dir = results_dir / "SU2Run" / f"SU2Run_{idx}_iter{it}"
    su2_dir.mkdir(exist_ok=True)

    run_cpacs2gmsh(cpacs, wkdir=gmsh_dir)
    run_su2(cpacs, results_dir=su2_dir)

    df_su2 = retrieve_aeromap_data(cpacs, aeromap_uid, objective)
    obj_value = df_su2[objective].iloc[0]

    return obj_value
