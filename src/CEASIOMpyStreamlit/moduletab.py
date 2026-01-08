"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit Tabs per module function.
| Author : Leon Deligny
| Creation: 21 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st
from cpacspy.cpacsfunctions import (
    get_value_or_default,
    get_value,
)
from ceasiompy.utils.geometryfunctions import get_aircrafts_list
from CEASIOMpyStreamlit.streamlitutils import section_edit_aeromap
from ceasiompy.utils.moduleinterfaces import get_specs_for_module
from CEASIOMpyStreamlit.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    else_vartype,
    path_vartype,
    float_vartype,
    aeromap_checkbox,
    aeromap_selection,
    # simulation_settings,
    multiselect_vartype,
    # SectionsOptimise,
    # range_aeromap,
)
from tixi3.tixi3wrapper import Tixi3
import tempfile
import os
from pathlib import Path
import pandas as pd
from typing import (
    List,
    Dict,
)
from collections import OrderedDict

from ceasiompy import log
from ceasiompy.utils.ceasiompyutils import (
    update_cpacs_from_specs,
)

from ceasiompy.utils.geometryfunctions import (
    return_uid_wings_sections,
)
from ceasiompy.SMTrain.func.config import (
    get_xpath_for_param,
)
from cpacspy.cpacsfunctions import create_branch
from CEASIOMpyStreamlit.streamlitutils import save_cpacs_file
from ceasiompy.SU2Run import (
    SU2_MAX_ITER_XPATH,)
from ceasiompy.SMTrain import (
    INCLUDE_GUI,
    LEVEL_ONE,
    LEVEL_TWO,
    OBJECTIVES_LIST,
    AEROMAP_FEATURES,
    SMTRAIN_XPATH_PARAMS_AEROMAP,
    SMTRAIN_XPATH_AEROMAP_UID,
    SMTRAIN_MAX_ALT,
    SMTRAIN_MAX_MACH,
    SMTRAIN_MAX_AOA,
    SMTRAIN_MAX_AOS,
    WING_PARAMETERS,
    SMTRAIN_XPATH_WINGS,
    SMTRAIN_GEOM_WING_OPTIMISE,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_NSAMPLES_AEROMAP_XPATH,
    SMTRAIN_NSAMPLES_GEOMETRY_XPATH,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_SIMULATION_PURPOSE_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_AVL_DATABASE_XPATH,
    SMTRAIN_KRG_MODEL,
    SMTRAIN_RBF_MODEL,
)

from ceasiompy.CPACS2GMSH import (
    INCLUDE_GUI,
    GMSH_OPEN_GUI_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_CTRLSURF_ANGLE_XPATH,
    GMSH_SYMMETRY_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
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
    GMSH_EXPORT_PROP_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_SAVE_CGNS_XPATH,
)

from ceasiompy.CPACS2GMSH import (
    MODULE_NAME as CPACS2GMSH_NAME,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def if_choice_vartype(
    vartype_map,
    session_state,
    xpath,
    default_value,
    name,
    key,
    description,
) -> None:

    default_index = int(
        default_value.index(
            get_value_or_default(session_state.cpacs.tixi, xpath + "type", "CPACS2GMSH mesh")
        )
    )

    selected_type = st.radio(
        "Select variable type:",
        options=default_value,
        index=default_index,
        key=f"{key}_type",
        help="Choose the input type",
    )
    session_state[f"{key}_types"] = selected_type
    selected_func = vartype_map[selected_type]

    if selected_type == "Path":
        selected_func(
            key=key,
        )
        session_state.xpath_to_update[xpath] = key
    elif selected_type == "CPACS2GMSH mesh":
        selected_func(
            tixi=session_state.cpacs.tixi,
            xpath=xpath,
            default_value="",
            name=name,
            key=key,
            description=description,
        )
        session_state.xpath_to_update[xpath] = key
    elif selected_type == "db":
        selected_func(
            tixi=session_state.cpacs.tixi,
            xpath=xpath + "list",
            default_value=get_aircrafts_list(),
            name=name,
            key=key + "list",
            description=description,
        )
        session_state.xpath_to_update[xpath + "list"] = key + "list"

    session_state.xpath_to_update[xpath + "type"] = f"{key}_types"


def order_by_gps(inputs: List) -> OrderedDict:
    groups = list(OrderedDict.fromkeys([v[6] for v in inputs.values()]))

    expanded_list: Dict[str, List[bool]] = {}
    for v in inputs.values():
        group = f"{v[6]}"
        if group not in expanded_list:
            expanded_list[group] = []
        expanded_list[group].append(v[8])

    groups_container = OrderedDict()
    for group in groups:
        groups_container[group] = st.expander(
            f"**{group}**",
            expanded=all(expanded_list[group]),
        )

    return groups_container


def checks(session_state, tabs) -> None:
    if "tabs" not in session_state:
        session_state["tabs"] = []

    if "workflow_modules" in session_state and session_state.workflow_modules:
        session_state.tabs = tabs(session_state.workflow_modules)

    if "xpath_to_update" not in session_state:
        session_state.xpath_to_update = {}


def add_gui_object(
    session_state,
    name,
    group,
    groups_container,
    key,
    aeromap_map,
    xpath,
    description,
    var_type,
    vartype_map,
    default_value,
) -> None:

    selected_value = None
    # Iterate per group
    with groups_container[group]:

        # Check if the name or var_type is in the dictionary and call the corresponding function
        if name in aeromap_map:
            aeromap_map[name](session_state.cpacs, xpath, key, description)
        elif var_type == "path_type":
            path_vartype(key)
        elif var_type in vartype_map:
            selected_value = vartype_map[var_type](
                session_state.cpacs.tixi, xpath, default_value, name, key, description
            )
        elif var_type == "multiselect":
            multiselect_vartype(default_value, name, key)
        else:
            else_vartype(
                tixi=session_state.cpacs.tixi,
                xpath=xpath,
                default_value=default_value,
                name=name,
                key=key,
                description=description,
            )

        session_state.xpath_to_update[xpath] = key

        tixi: Tixi3
        tixi = st.session_state.cpacs.tixi

        
        if selected_value == "Run New Simulations":
            default_value = OBJECTIVES_LIST
            value = get_value_or_default(tixi, SMTRAIN_OBJECTIVE_XPATH, default_value[0])
            idx = default_value.index(value)
            session_state.xpath_to_update[SMTRAIN_OBJECTIVE_XPATH] = f'{key}_objective'
            selected_value = st.radio(
                f"Objective",
                options=default_value,
                index=idx,
                key=f'{key}_objective',
                help="Objective function list for the surrogate model to predict",
                on_change=save_cpacs_file,
            )

            default_value = ["Flight Condition Exploration", "Geometry Exploration"]
            value = get_value_or_default(tixi, SMTRAIN_SIMULATION_PURPOSE_XPATH, default_value[0])
            idx = default_value.index(value)
            session_state.xpath_to_update[SMTRAIN_SIMULATION_PURPOSE_XPATH] = f'{key}_simulation_purpose'
            selected_value = st.radio(
                f"Choice of simulation Purpose",
                options=default_value,
                index=idx,
                key=f'{key}_simulation_purpose',
                help="choose to train the model for optimal flight conditions given a fixed geometry or for optimal geometry given a fixed flight conditions.",
                on_change=save_cpacs_file,
            )
            
            # tixi: Tixi3
            # tixi = st.session_state.cpacs.tixi

            if selected_value == 'Flight Condition Exploration':
                with st.columns([1, 2])[0]:
                    session_state.xpath_to_update[SMTRAIN_NSAMPLES_AEROMAP_XPATH] = f'{key}_sample_aeromap'
                    st.number_input("Number of samples", value=int(get_value_or_default(tixi, SMTRAIN_NSAMPLES_AEROMAP_XPATH, 10)), key= f'{key}_sample_aeromap', help='Choose the number of samples', on_change=save_cpacs_file)

                xpath = SMTRAIN_XPATH_PARAMS_AEROMAP
                for par in AEROMAP_FEATURES:
                    session_state.xpath_to_update[xpath + f"/parameter/{par}/status"] = f"param_{par}"
                    session_state.xpath_to_update[xpath + f"/parameter/{par}/min_value/value"] = f"param_{par}_min"
                    session_state.xpath_to_update[xpath + f"/parameter/{par}/max_value/value"] = f"param_{par}_max"

                        
                # aeromap_selected=get_value(tixi, SMTRAIN_XPATH_AEROMAP_UID)

                st.markdown('##### Select the parameters to consider')
                for par in AEROMAP_FEATURES:
                    param_local_xpath = xpath + f"/parameter/{par}/status"
                    min_value_path = xpath + f"/parameter/{par}/min_value/value"
                    max_value_path = xpath + f"/parameter/{par}/max_value/value"

                    default_min_value = 0.0
                    default_max_value = 0.0

                    par_key = f"param_{par}"
                    min_key = f"param_{par}_min"
                    max_key = f"param_{par}_max"

                    col_1, col_2, col_3 = st.columns([0.5, 0.4, 0.4])

                    with col_1:
                        par_selected = st.checkbox(
                            f"{par}",
                            value=get_value_or_default(tixi, param_local_xpath, 0),
                            key=par_key,
                            help=f"Enable DoE for {par}",
                            on_change=save_cpacs_file,
                        )
                        if par_selected:
                            with col_2:
                                st.number_input(
                                    f"Min",
                                    value=get_value_or_default(tixi, min_value_path, default_min_value),
                                    format="%0.1f",
                                    key=min_key,
                                    help="Default set to 20% less than the current value. Adjustable as needed.",
                                    on_change=save_cpacs_file,
                                )
                            with col_3:
                                st.number_input(
                                    f"Max",
                                    value=get_value_or_default(tixi, max_value_path, default_max_value),
                                    format="%0.1f",
                                    key=max_key,
                                    help="Default set to 20% more than the current value. Adjustable as needed.",
                                    on_change=save_cpacs_file,
                                )
                

            if selected_value == 'Geometry Exploration':
                # Add the settings
                # tixi = st.session_state.cpacs.tixi
                with st.columns([1, 2])[0]:
                    session_state.xpath_to_update[SMTRAIN_NSAMPLES_GEOMETRY_XPATH] = f'{key}_sample_geom'
                    st.number_input("Number of samples", value=int(get_value_or_default(tixi, SMTRAIN_NSAMPLES_GEOMETRY_XPATH, 10)), key= f'{key}_sample_geom', help='Choose the number of samples', on_change=save_cpacs_file)
                xpath = SMTRAIN_GEOM_WING_OPTIMISE
                uid_list = return_uid_wings_sections(tixi)
                wings = sorted(set(wing_uid for (wing_uid, _) in uid_list))
                for wing_uid in wings:
                    session_state.xpath_to_update[xpath + f"/{wing_uid}/selected"] = f"{key}_wing_{wing_uid}"
                    sections = [sec_uid for (wng, sec_uid) in uid_list if wng == wing_uid]
                    for section_uid in sections:
                        session_state.xpath_to_update[
                            xpath + f"/{wing_uid}/sections/{section_uid}/selected"
                        ] = f"section_{section_uid}"
                        
                        for param in WING_PARAMETERS:
                            sections_key = f"section_{section_uid}"
                            session_state.xpath_to_update[xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/status"] = f"{sections_key}_{param}"
                            session_state.xpath_to_update[xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/min_value/value"] = f"{sections_key}_{param}_min"
                            session_state.xpath_to_update[xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/max_value/value"] = f"{sections_key}_{param}_max"      
                
                st.markdown('###### Select the wings to optimise')
                for wing_uid in wings:
                    wing_key = f"{key}_wing_{wing_uid}"
                    wing_selected_xpath = xpath + f"/{wing_uid}/selected"
                    wing_selected = st.checkbox(
                        f"{wing_uid}",
                        value=get_value_or_default(tixi, wing_selected_xpath, 0),
                        key=wing_key,
                        help=f"Enable optimization for {wing_uid}",
                        on_change=save_cpacs_file,
                    )

                    sections = [sec_uid for (wng, sec_uid) in uid_list if wng == wing_uid]
                    # show the section if the wing was selected
                    if wing_selected:
                        st.markdown(f"##### ↪️ Sections of {wing_uid}")
                        # sections = [sec_uid for (wng, sec_uid) in uid_list if wng == wing_uid]
                        for section_uid in sections:
                            sections_key = f"section_{section_uid}"
                            sections_selected_xpath = xpath + f"/{wing_uid}/sections/{section_uid}/selected"
                            col1,col2,col3 = st.columns([0.05,0.3,0.7])
                            with col2:
                                st.markdown("""--""")
                                # section_numerate = section_uid.split("_")[1]
                                section_selected = st.checkbox(
                                    f"{section_uid}",
                                    value=get_value_or_default(tixi, sections_selected_xpath, 0),
                                    key=sections_key,
                                    help=f"Select if you want to optimise this section",
                                    on_change=save_cpacs_file,
                                )
                            
                            with col3:
                                if section_selected:
                                    st.markdown(f"##### Parameters")
                                    for param in WING_PARAMETERS:
                                        param_local_xpath = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/status"
                                        min_value_path = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/min_value/value"
                                        max_value_path = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/max_value/value"
                                        params_current_value_xpath = get_xpath_for_param(tixi, param, wing_uid, section_uid)

                                        # print(f'XPATH for parameters: {param_xpath}')

                                        current_value = get_value_or_default(tixi, params_current_value_xpath, 0)

                                        default_min_value = 0.8 * current_value
                                        default_max_value = 1.2 * current_value

                                        param_key = f'{sections_key}_{param}'
                                        min_key = f'{sections_key}_{param}_min'
                                        max_key = f'{sections_key}_{param}_max'

                                        param_box = st.checkbox(
                                            f"{param}",
                                            value=get_value_or_default(tixi, param_local_xpath, 0),
                                            key=param_key,
                                            help=f"Select if you want to optimise this parameter",
                                            on_change=save_cpacs_file,
                                        )

                                        if param_box:
                                                                                
                                            col_min, col_val, col_max = st.columns([0.5, 0.5, 0.5])
                                            
                                            with col_min:
                                                st.number_input(
                                                    f"Min",
                                                    value=get_value_or_default(tixi, min_value_path, default_min_value),
                                                    format="%0.3f",
                                                    key=min_key,
                                                    help="Default set to 20% less than the current value. Adjustable as needed.",
                                                    on_change=save_cpacs_file,
                                                )

                                            with col_val:
                                                st.markdown("Current value:")
                                                st.markdown(f"<= {current_value:.3f} <=")
                                            
                                            with col_max:
                                                st.number_input(
                                                    f"Max",
                                                    value=get_value_or_default(tixi, max_value_path, default_max_value),
                                                    format="%0.3f",
                                                    key=max_key,
                                                    help="Default set to 20% more than the current value. Adjustable as needed.",
                                                    on_change=save_cpacs_file,
                                                )

        if 'simulations_file_path' not in st.session_state:
            st.session_state['simulations_file_path'] = ''

        if 'simulations_df' not in st.session_state:
            st.session_state['simulations_df'] = None

        elif selected_value == "Load Geometry Exploration Simulations":
            # session_state.xpath_to_update[xpath + "/csvpath"] = 'existing_avl_results'
            coll,collr = st.columns(2)
            with coll:
                uploaded_existing_simulations = st.file_uploader(
                    "Upload simulations file", 
                    type=["csv"], 
                    key='existing_avl_results'
                )
                if uploaded_existing_simulations:
                    # Ensure working directory exists
                    working_dir = Path(st.session_state.workflow.working_dir)
                    working_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save the uploaded CSV to the working directory
                    csv_filename = 'avl_simulations_results.csv'
                    csv_path = working_dir / csv_filename
                    with open(csv_path, "wb") as f:
                        f.write(uploaded_existing_simulations.getbuffer())
                    
                    # Load the CSV into a DataFrame and store both DataFrame and path in session_state
                    simulations_df = pd.read_csv(csv_path)
                    st.session_state.simulations_df = simulations_df
                    st.session_state.simulations_file_path = str(csv_path)
                    
                    st.success("CSV copied to working directory!")
                    st.write(f"DataFrame shape: {simulations_df.shape}")
                    st.dataframe(simulations_df.head())
                    st.write(f"Persistent path: {csv_path}")
            with collr:
                uploaded_ranges_file = st.file_uploader(
                    "Upload parameter ranges file", 
                    type=["csv"], 
                    key='existing_range_file'
                )
                    
                if uploaded_ranges_file:
                    # Ensure working directory exists
                    working_dir = Path(st.session_state.workflow.working_dir)
                    working_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save the uploaded CSV to the working directory
                    csv_range_filename = 'ranges_for_gui.csv'
                    csv_range_path = working_dir / csv_range_filename
                    with open(csv_range_path, "wb") as f:
                        f.write(uploaded_ranges_file.getbuffer())
                    
                    # Load the CSV into a DataFrame and store both DataFrame and path in session_state
                    range_df = pd.read_csv(csv_range_path)
                    st.session_state.range_df = range_df
                    st.session_state.range_file_path = str(range_df)
                    
                    st.success("CSV copied to working directory!")
                    st.write(f"DataFrame shape: {range_df.shape}")
                    st.dataframe(range_df.head())
                    st.write(f"Persistent path: {csv_range_path}")
            

        if selected_value == 'Two levels':
            # st.write('Select at least one model.')
            # value = get_value_or_default(tixi, SMTRAIN_KRG_MODEL, False)
            # session_state.xpath_to_update[SMTRAIN_KRG_MODEL] = f'{key}_krg_model'
            # krg_model_bool = st.checkbox(
            #     f'KRG',
            #     value=get_value_or_default(tixi, SMTRAIN_KRG_MODEL, False),
            #     key=f'{key}_krg_model',
            #     help="Select this model for the simulation (choose more than one for comparison).",
            #     on_change=save_cpacs_file,
            # )

            value = get_value_or_default(tixi, SMTRAIN_THRESHOLD_XPATH, 0.05)
            session_state.xpath_to_update[SMTRAIN_THRESHOLD_XPATH] = f'{key}_th_rmse'
            with st.columns([1, 2])[0]:
                st.number_input(
                    f"RMSE objective",
                    value=value,
                    format="%0.3f",
                    key=f"{key}_th_rmse",
                    help="Selects the model's RMSE threshold value for Bayesian optimisation",
                    on_change=save_cpacs_file,
                )

            value = int(get_value_or_default(tixi, SU2_MAX_ITER_XPATH, 10))
            session_state.xpath_to_update[SU2_MAX_ITER_XPATH] = f'{key}_max_iter'
            with st.columns([1, 2])[0]:
                st.number_input(
                    f"Max iterations",
                    value=value,
                    key=f"{key}_max_iter",
                    help="Maximum number of iterations performed by SU2",
                    on_change=save_cpacs_file,
                )

            # Load default cpacs2gmsh settings that are not in smtrain gui
            if tixi.checkElement(GMSH_CTRLSURF_ANGLE_XPATH):
                tixi.updateTextElement(GMSH_CTRLSURF_ANGLE_XPATH, '0.0')
            else:
                create_branch(tixi, GMSH_CTRLSURF_ANGLE_XPATH)
                tixi.updateDoubleElement(GMSH_CTRLSURF_ANGLE_XPATH, 0, "%g")

            if tixi.checkElement(GMSH_SYMMETRY_XPATH):
                tixi.updateBooleanElement(GMSH_SYMMETRY_XPATH, False)
            else:
                create_branch(tixi, GMSH_SYMMETRY_XPATH)
                tixi.updateBooleanElement(GMSH_SYMMETRY_XPATH, False)

            if tixi.checkElement(GMSH_FARFIELD_FACTOR_XPATH):
                tixi.updateDoubleElement(GMSH_FARFIELD_FACTOR_XPATH, 10, "%g")
            else:
                create_branch(tixi, GMSH_FARFIELD_FACTOR_XPATH)
                tixi.updateDoubleElement(GMSH_FARFIELD_FACTOR_XPATH, 10, "%g")

            if tixi.checkElement(GMSH_EXPORT_PROP_XPATH):
                tixi.updateBooleanElement(GMSH_EXPORT_PROP_XPATH, False)
            else:
                create_branch(tixi, GMSH_EXPORT_PROP_XPATH)
                tixi.updateBooleanElement(GMSH_EXPORT_PROP_XPATH, False)

            if tixi.checkElement(GMSH_SAVE_CGNS_XPATH):
                tixi.updateBooleanElement(GMSH_SAVE_CGNS_XPATH, False)
            else:
                create_branch(tixi, GMSH_SAVE_CGNS_XPATH)
                tixi.updateBooleanElement(GMSH_SAVE_CGNS_XPATH, False)
            
            if tixi.checkElement(GMSH_OPEN_GUI_XPATH):
                tixi.updateBooleanElement(GMSH_OPEN_GUI_XPATH, False)
            else:
                create_branch(tixi, GMSH_OPEN_GUI_XPATH)
                tixi.updateBooleanElement(GMSH_OPEN_GUI_XPATH, False)

            
            default_value = ["Euler", "RANS"]
            value1 = get_value_or_default(tixi, GMSH_MESH_TYPE_XPATH, default_value[0])
            idx = default_value.index(value1)
            session_state.xpath_to_update[GMSH_MESH_TYPE_XPATH] = f'{key}_mesh_type'
            selected_mesh_type = st.radio(
                f"type_mesh",
                options=default_value,
                index=idx,
                key=f'{key}_mesh_type',
                help='Choose between Euler and RANS mesh',
                on_change=save_cpacs_file,
            )
            
            if selected_mesh_type:
                st.markdown("##### Mesh settings")
                col_size, col_gen1, col_gen2 = st.columns([3.5,3.8,3.5])
                
                with col_size:
                    st.markdown("###### Mesh size")

                    value = get_value_or_default(tixi, GMSH_MESH_SIZE_FARFIELD_XPATH, 10)
                    session_state.xpath_to_update[GMSH_MESH_SIZE_FARFIELD_XPATH] = f'{key}_ff_msf'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Farfield mesh size factor",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_ff_msf',
                            help="""Factor proportional to the biggest cell on the plane
                                    to obtain cell size on the farfield(just for Euler)""",
                            on_change=save_cpacs_file,
                        )
                    
                    value = get_value_or_default(tixi, GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH, 1)
                    session_state.xpath_to_update[GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH] = f'{key}_fus_msf'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Fuselage mesh size factor",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_fus_msf',
                            help="Factor proportional to fuselage radius of curvature to obtain cell size on it",
                            on_change=save_cpacs_file,
                        )

                    value = get_value_or_default(tixi, GMSH_MESH_SIZE_FACTOR_WINGS_XPATH, 1)
                    session_state.xpath_to_update[GMSH_MESH_SIZE_FACTOR_WINGS_XPATH] = f'{key}_wing_msf'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Wings mesh size factor",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_wing_msf',
                            help="Factor proportional to wing radius of curvature to obtain cell size on it",
                            on_change=save_cpacs_file,
                        )

                    value = get_value_or_default(tixi, GMSH_MESH_SIZE_ENGINES_XPATH, 0.23)
                    session_state.xpath_to_update[GMSH_MESH_SIZE_ENGINES_XPATH] = f'{key}_engine_msf'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Engines",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_engine_msf',
                            help="Value assigned for the engine surfaces mesh size, unit: [m]",
                            on_change=save_cpacs_file,
                        )

                    value = get_value_or_default(tixi, GMSH_MESH_SIZE_PROPELLERS_XPATH, 0.23)
                    session_state.xpath_to_update[GMSH_MESH_SIZE_PROPELLERS_XPATH] = f'{key}_propeller_msf'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Propellers",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_propeller_msf',
                            help="Value assigned for the propeller surfaces mesh size, unit: [m]",
                            on_change=save_cpacs_file,
                        )
                    
                    with col_gen1:
                        st.markdown("###### Advanced mesh parameters")
                        value = get_value_or_default(tixi, GMSH_N_POWER_FACTOR_XPATH, 2)
                        session_state.xpath_to_update[GMSH_N_POWER_FACTOR_XPATH] = f'{key}_Npower_factor'
                        with st.columns([5, 1])[0]:
                            st.number_input(
                                f"n power factor",
                                value=value,
                                format="%0.3f",
                                key=f'{key}_Npower_factor',
                                help="Power of the power law of the refinement on LE and TE.",
                                on_change=save_cpacs_file,
                            )

                        value = get_value_or_default(tixi, GMSH_N_POWER_FIELD_XPATH, 0.9)
                        session_state.xpath_to_update[GMSH_N_POWER_FIELD_XPATH] = f'{key}_Npower_field'
                        with st.columns([5, 1])[0]:
                            st.number_input(
                                f"n power field",
                                value=value,
                                format="%0.3f",
                                key=f'{key}_Npower_field',
                                help="Value that changes the measure of fist cells near aircraft parts",
                                on_change=save_cpacs_file,
                            )

                        value = get_value_or_default(tixi, GMSH_REFINE_FACTOR_XPATH, 2)
                        session_state.xpath_to_update[GMSH_REFINE_FACTOR_XPATH] = f'{key}_refine_factor'
                        with st.columns([5, 1])[0]:
                            st.number_input(
                                f"LE/TE refinement factor",
                                value=value,
                                format="%0.3f",
                                key=f'{key}_refine_factor',
                                help="Refinement factor of wing leading/trailing edge mesh",
                                on_change=save_cpacs_file,
                            )

                        session_state.xpath_to_update[GMSH_REFINE_TRUNCATED_XPATH] = f'{key}_refine_trunated_TE'
                        refine_truncated = st.checkbox(
                            f'Refine truncated TE',
                            value=get_value_or_default(tixi, GMSH_REFINE_TRUNCATED_XPATH, False),
                            key=f'{key}_refine_trunated_TE',
                            help='Enable the refinement of truncated trailing edge',
                            on_change=save_cpacs_file,
                        )

                        session_state.xpath_to_update[GMSH_AUTO_REFINE_XPATH] = f'{key}_auto_refine'
                        auto_refine = st.checkbox(
                            f'Auto refine',
                            value=get_value_or_default(tixi, GMSH_AUTO_REFINE_XPATH, False),
                            key=f'{key}_auto_refine',
                            help="Automatically refine the mesh on surfaces that are small compare to the chosen mesh"
                                    "size, this option increase the mesh generation time",
                            on_change=save_cpacs_file,
                        )

                    if selected_mesh_type == 'RANS':
                        with col_gen2:
                            st.markdown("###### RANS options")

                            value = get_value_or_default(tixi, GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH, 1.5)
                            session_state.xpath_to_update[GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH] = f'{key}_refine_angled_factor'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Refinement factor of lines in between angled surfaces (only in RANS)",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_refine_angled_factor',
                                    help="Refinement factor of edges at intersections that are not flat enough",
                                    on_change=save_cpacs_file,
                                )

                            value = get_value_or_default(tixi, GMSH_NUMBER_LAYER_XPATH, 20)
                            session_state.xpath_to_update[GMSH_NUMBER_LAYER_XPATH] = f'{key}_n_layer'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Number of layer",
                                    value=value,
                                    key=f'{key}_n_layer',
                                    help="Number of prismatic element layers.",
                                    on_change=save_cpacs_file,
                                )

                            value = get_value_or_default(tixi, GMSH_H_FIRST_LAYER_XPATH, 3)
                            session_state.xpath_to_update[GMSH_H_FIRST_LAYER_XPATH] = f'{key}_h_first_layer'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Height of first layer [µm]",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_h_first_layer',
                                    help="Is the height of the first prismatic cell, touching the wall, in mesh length units.",
                                    on_change=save_cpacs_file,
                                )

                            value = get_value_or_default(tixi, GMSH_MAX_THICKNESS_LAYER_XPATH, 100)
                            session_state.xpath_to_update[GMSH_MAX_THICKNESS_LAYER_XPATH] = f'{key}_max_layer_thickness'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Max layer thickness [mm] ",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_max_layer_thickness',
                                    help="The maximum allowed absolute thickness of the prismatic layer.",
                                    on_change=save_cpacs_file,
                                )
                            
                            value = get_value_or_default(tixi, GMSH_GROWTH_RATIO_XPATH, 1.2)
                            session_state.xpath_to_update[GMSH_GROWTH_RATIO_XPATH] = f'{key}_growth_ratio'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Growth ratio",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_growth_ratio',
                                    help="The largest allowed ratio between the wall-normal edge lengths of consecutive cells",
                                    on_change=save_cpacs_file,
                                )
                            
                            value = get_value_or_default(tixi, GMSH_GROWTH_FACTOR_XPATH, 1.4)
                            session_state.xpath_to_update[GMSH_GROWTH_FACTOR_XPATH] = f'{key}_growth_factor'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Growth factor",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_growth_factor',
                                    help="Desired growth factor between edge lengths of coincident tetrahedra",
                                    on_change=save_cpacs_file,
                                )

                            value = get_value_or_default(tixi, GMSH_FEATURE_ANGLE_XPATH, 40)
                            session_state.xpath_to_update[GMSH_FEATURE_ANGLE_XPATH] = f'{key}_feature_angle'
                            with st.columns([5, 1])[0]:
                                st.number_input(
                                    f"Feature Angle [grad]",
                                    value=value,
                                    format="%0.3f",
                                    key=f'{key}_feature_angle',
                                    help="Larger angles are treated as resulting from approximation of curved surfaces",
                                    on_change=save_cpacs_file,
                                )

                    st.markdown('###### Engines')
                    value = get_value_or_default(tixi, GMSH_INTAKE_PERCENT_XPATH, 20)
                    session_state.xpath_to_update[GMSH_INTAKE_PERCENT_XPATH] = f'{key}_intake_percent'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Engine intake position [%]",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_intake_percent',
                            help="Position of the intake surface boundary condition in percentage of"
                                    "the engine length from the beginning of the engine",
                            on_change=save_cpacs_file,
                        )

                    value = get_value_or_default(tixi, GMSH_EXHAUST_PERCENT_XPATH, 20)
                    session_state.xpath_to_update[GMSH_EXHAUST_PERCENT_XPATH] = f'{key}_exhaust_percent'
                    with st.columns([5, 1])[0]:
                        st.number_input(
                            f"Engine exhaust position [%]",
                            value=value,
                            format="%0.3f",
                            key=f'{key}_exhaust_percent',
                            help="Position of the exhaust surface boundary condition in percentage of"
                                    "the engine length from the beginning of the engine",
                            on_change=save_cpacs_file,
                        )
        if selected_value == 'One levels':
            st.write('Select at least one model.')
            value = get_value_or_default(tixi, SMTRAIN_KRG_MODEL, False)
            session_state.xpath_to_update[SMTRAIN_KRG_MODEL] = f'{key}_krg_model_lf'
            krg_model_bool = st.checkbox(
                f'KRG',
                value=get_value_or_default(tixi, SMTRAIN_KRG_MODEL, False),
                key=f'{key}_krg_model_lf',
                help="Select this model for the simulation (choose more than one for comparison).",
                on_change=save_cpacs_file,
            )

            value = get_value_or_default(tixi, SMTRAIN_RBF_MODEL, False)
            session_state.xpath_to_update[SMTRAIN_RBF_MODEL] = f'{key}_rbf_model_lf'
            rbf_model_bool = st.checkbox(
                f'RBF',
                value=get_value_or_default(tixi, SMTRAIN_RBF_MODEL, False),
                key=f'{key}_rbf_model_lf',
                help="Select this model for the simulation (choose more than one for comparison).",
                on_change=save_cpacs_file,
            )
                        


def add_module_tab(new_file: bool) -> None:
    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    with st.expander("**Edit Aeromaps**", expanded=False):
        section_edit_aeromap()

    checks(st.session_state, st.tabs)

    aeromap_map = {
        "__AEROMAP_SELECTION": aeromap_selection,
        "__AEROMAP_CHECKBOX": aeromap_checkbox,
    }

    vartype_map = {
        int: int_vartype,
        float: float_vartype,
        list: list_vartype,
        bool: bool_vartype,
        # "Simulation Settings": simulation_settings,
        # "SectionsOptimise" : SectionsOptimise,
        # "RangeAeromap" : range_aeromap,
    }

    dynamic_vartype_map = {
        "Path": path_vartype,
        "db": list_vartype,
        "CPACS2GMSH mesh": else_vartype,
    }
    # Load each module iteratively
    for m, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):
        with tab :
            st.text("")
            specs = get_specs_for_module(module, reloading=new_file)
            # Check if specs.cpacs_inout is None
            if specs.cpacs_inout is None:
                log.error("specs.cpacs_inout is None. Ensure it is initialized before use.")
            else:
                inputs = specs.cpacs_inout.get_gui_dict()
            if not inputs:
                st.warning("No settings to modify this module.")
                continue

            groups_container = order_by_gps(inputs)

            for (
                name,
                default_value,
                var_type,
                unit,
                xpath,
                description,
                group,
                _,
                _,
            ) in inputs.values():
                key = f"{m}_{module}_{name.replace(' ', '')}_{group.replace(' ', '')}"
                process_unit(name, unit)

                if var_type == "DynamicChoice":
                    with groups_container[group]:
                        if_choice_vartype(
                            dynamic_vartype_map,
                            session_state=st.session_state,
                            xpath=xpath,
                            default_value=default_value,
                            name=name,
                            key=key,
                            description=description,
                        )

                else:
                    add_gui_object(
                        st.session_state,
                        name,
                        group,
                        groups_container,
                        key,
                        aeromap_map,
                        xpath,
                        description,
                        var_type,
                        vartype_map,
                        default_value,
                    )


def process_unit(name: str, unit: str) -> None:
    # TODO: Add constants in __init__ ?
    if unit not in ["[]", "[1]", None]:
        name = f"{name} {unit}"
