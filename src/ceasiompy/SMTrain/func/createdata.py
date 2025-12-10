"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st
import pandas as pd
from pandas import concat
from shutil import copyfile
import shutil
import gmsh
from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.SU2Run.su2run import main as run_su2
from ceasiompy.CPACS2GMSH.cpacs2gmsh import main as run_cpacs2gmsh
from ceasiompy.SMTrain.func.utils import (
    create_aeromap_from_varpts,
    generate_su2_wkdir,
)
from ceasiompy.SMTrain.func.config import (
    retrieve_aeromap_data,
    retrieve_ceasiompy_db_data,
    get_xpath_for_param,
    update_geometry_cpacs,
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
from ceasiompy.SU2Run import SU2_MAX_ITER_XPATH
from ceasiompy.SMTrain.func import AEROMAP_SELECTED
from ceasiompy.SMTrain import (
    SMTRAIN_AVL_DATABASE_XPATH,
    MODULE_NAME as SMTrain
)
from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)
from ceasiompy.SU2Run import (
    SU2_AEROMAP_UID_XPATH,
    MODULE_NAME as SU2RUN_NAME,
)
from ceasiompy.CPACS2GMSH import (
    MODULE_NAME as CPACS2GMSH_NAME,
)
from ceasiompy.utils.commonxpaths import (
    SU2MESH_XPATH,
    USED_SU2_MESH_XPATH,
)

from ceasiompy.CPACS2GMSH import (
    MODULE_NAME as CPACS2GMSH_NAME,
    GMSH_MESH_TYPE_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
    GMSH_AUTO_REFINE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
)


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


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
        tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap.uid)

        run_avl(cpacs, avl_results_dir)

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


def launch_gmsh_su2_geom(
    cpacs: CPACS,
    results_dir: Path,
    objective: str,
    aeromap_csv_path,
    new_point_df,
    aeromap_uid,
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """
    gmsh.clear()
    tixi = cpacs.tixi
    # Load default parameters
    st.session_state = MagicMock()
    type_mesh = str(get_value(tixi, GMSH_MESH_TYPE_XPATH))
    farfield_ms = str(get_value(tixi, GMSH_MESH_SIZE_FARFIELD_XPATH))
    fuselage_ms = str(get_value(tixi, GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH))
    wings_ms = str(get_value(tixi, GMSH_MESH_SIZE_FACTOR_WINGS_XPATH))
    engines_ms = str(get_value(tixi, GMSH_MESH_SIZE_ENGINES_XPATH))
    propellers_ms = str(get_value(tixi, GMSH_MESH_SIZE_PROPELLERS_XPATH))
    Npower_fac = str(get_value(tixi, GMSH_N_POWER_FACTOR_XPATH))
    Npower_field = str(get_value(tixi, GMSH_N_POWER_FIELD_XPATH))
    refine_fac = str(get_value(tixi, GMSH_REFINE_FACTOR_XPATH))
    refine_trunc = str(get_value(tixi, GMSH_REFINE_TRUNCATED_XPATH))
    auto_ref = str(get_value(tixi, GMSH_AUTO_REFINE_XPATH))
    angled_ar = str(get_value(tixi, GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH))
    n_layer = str(get_value(tixi, GMSH_NUMBER_LAYER_XPATH))
    h_first = str(get_value(tixi, GMSH_H_FIRST_LAYER_XPATH))
    max_thick = str(get_value(tixi, GMSH_MAX_THICKNESS_LAYER_XPATH))
    growth_ratio = str(get_value(tixi, GMSH_GROWTH_RATIO_XPATH))
    growth_fac = str(get_value(tixi, GMSH_GROWTH_FACTOR_XPATH))
    feature_angle = str(get_value(tixi, GMSH_FEATURE_ANGLE_XPATH))
    intake_per = str(get_value(tixi, GMSH_INTAKE_PERCENT_XPATH))
    exhaust_per = str(get_value(tixi, GMSH_EXHAUST_PERCENT_XPATH))
    
    # Retrieve the CpACS2gmsh gui values of smtrain
    update_cpacs_from_specs(cpacs, CPACS2GMSH_NAME, test=False)

    # Load back the smtrain cpacs2gmsh gui values into the cpacs.tixi 

    local_mesh_dir = get_results_directory(CPACS2GMSH_NAME)
    # local_mesh_dir.mkdir(exist_ok=True)

    tixi.updateTextElement(GMSH_MESH_TYPE_XPATH, type_mesh)
    tixi.updateTextElement(GMSH_MESH_SIZE_FARFIELD_XPATH, farfield_ms)
    tixi.updateTextElement(GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH, fuselage_ms)
    tixi.updateTextElement(GMSH_MESH_SIZE_FACTOR_WINGS_XPATH, wings_ms)
    tixi.updateTextElement(GMSH_MESH_SIZE_ENGINES_XPATH, engines_ms)
    tixi.updateTextElement(GMSH_MESH_SIZE_PROPELLERS_XPATH, propellers_ms)
    tixi.updateTextElement(GMSH_N_POWER_FACTOR_XPATH, Npower_fac)
    tixi.updateTextElement(GMSH_N_POWER_FIELD_XPATH, Npower_field)
    tixi.updateTextElement(GMSH_REFINE_FACTOR_XPATH, refine_fac)
    tixi.updateTextElement(GMSH_REFINE_TRUNCATED_XPATH, refine_trunc)
    tixi.updateTextElement(GMSH_AUTO_REFINE_XPATH, auto_ref)
    tixi.updateTextElement(GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH, angled_ar)
    tixi.updateTextElement(GMSH_NUMBER_LAYER_XPATH, n_layer)
    tixi.updateTextElement(GMSH_H_FIRST_LAYER_XPATH, h_first)
    tixi.updateTextElement(GMSH_MAX_THICKNESS_LAYER_XPATH, max_thick)
    tixi.updateTextElement(GMSH_GROWTH_RATIO_XPATH, growth_ratio)
    tixi.updateTextElement(GMSH_GROWTH_FACTOR_XPATH, growth_fac)
    tixi.updateTextElement(GMSH_FEATURE_ANGLE_XPATH, feature_angle)
    tixi.updateTextElement(GMSH_INTAKE_PERCENT_XPATH, intake_per)
    tixi.updateTextElement(GMSH_EXHAUST_PERCENT_XPATH, exhaust_per)

    run_cpacs2gmsh(cpacs, wkdir=local_mesh_dir)

    # tixi = cpacs.tixi
    su2mesh, su2_mesh_path = None, None
    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    # dest_path = Path(results_dir) / "currently_cpacs_to_run.xml"
    # shutil.copy2(get_results_directory(SMTrain), dest_path)

    if tixi.checkElement(SU2MESH_XPATH):
        su2mesh = get_value(tixi, SU2MESH_XPATH)

    if tixi.checkElement(USED_SU2_MESH_XPATH):
        su2_mesh_path = tixi.getTextElement(USED_SU2_MESH_XPATH)
        if not su2_mesh_path:
            su2_mesh_path = None

    
    # su2_mesh_path_type = str(get_value(tixi, USED_SU2_MESH_XPATH + "type"))
    max_iters = str(get_value(tixi, SU2_MAX_ITER_XPATH))

    update_cpacs_from_specs(cpacs, SU2RUN_NAME, test=False)

    tixi.updateTextElement(SU2_AEROMAP_UID_XPATH, aeromap_uid)
    # tixi.updateTextElement(USED_SU2_MESH_XPATH + "type", su2_mesh_path_type)
    tixi.updateTextElement(SU2_MAX_ITER_XPATH, max_iters)

    if su2mesh is not None:
        log.info(f'{su2mesh=}')
        tixi.updateTextElement(SU2MESH_XPATH, su2mesh)

    if su2_mesh_path is not None:
        tixi.updateTextElement(USED_SU2_MESH_XPATH, str(su2_mesh_path))
    
    # results = []
    run_su2(cpacs, results_dir=results_dir)

    df_su2 = retrieve_aeromap_data(cpacs, aeromap_uid, objective)
    print("DATAFRAME FROM SU2:")
    print(f"{df_su2}")
    obj_value = df_su2[objective].iloc[0]
    print(f"SU2 objective value: {obj_value}")
    return obj_value 