"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI objects in CEASIOMpy.
| Author : Leon Deligny
| Creation: 21 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import pandas as pd
import streamlit as st

from CEASIOMpyStreamlit.streamlitutils import save_cpacs_file
from cpacspy.cpacsfunctions import (
    get_string_vector,
    get_value_or_default,
    get_value,
)

from tixi3.tixi3wrapper import Tixi3
from ceasiompy import log

from ceasiompy.utils.geometryfunctions import (
    return_uid_wings_sections,
)

from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    AEROPERFORMANCE_XPATH,
)

from ceasiompy.SMTrain import (
    SMTRAIN_XPATH_AEROMAP_UID
)

from ceasiompy.SMTrain import (
    WING_PARAMETERS,
    AEROMAP_FEATURES,
)

from ceasiompy.SMTrain.func.config import (
    get_xpath_for_param,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def aeromap_selection(cpacs, xpath, key, description):
    aeromap_uid_list = cpacs.get_aeromap_uid_list()

    if not len(aeromap_uid_list):
        st.error("You must create an aeromap in order to use this module!")
    else:
        value = get_value_or_default(cpacs.tixi, xpath, aeromap_uid_list[0])
        if value in aeromap_uid_list:
            idx = aeromap_uid_list.index(value)
        else:
            idx = 0
        st.radio(
            "Select an aeromap",
            key=key,
            options=aeromap_uid_list,
            index=idx,
            help=description,
            on_change=save_cpacs_file,
        )


def aeromap_checkbox(cpacs, xpath, key, description) -> None:
    aeromap_uid_list = cpacs.get_aeromap_uid_list()

    if not len(aeromap_uid_list):
        st.error("You must create an aeromap in order to use this module!")

    else:
        with st.columns([1, 2])[0]:
            try:
                default_otp = get_string_vector(cpacs.tixi, xpath)
            except ValueError:
                default_otp = None

            st.multiselect(
                "Select one or several aeromaps",
                key=key,
                options=aeromap_uid_list,
                default=default_otp,
                help=description,
                on_change=save_cpacs_file,
            )


def path_vartype(key) -> None:
    uploaded_file = st.file_uploader(
        "Select a SU2 file",
        type=["su2"],
    )
    if uploaded_file:
        su2_file_path = st.session_state.workflow.working_dir / uploaded_file.name

        # Save the uploaded file to the specified path
        with open(su2_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state[key] = str(su2_file_path)
        save_cpacs_file()


def multiselect_vartype(default_value, name, key) -> None:
    # Initialize the list in session state if it doesn't exist
    if key not in st.session_state:
        st.session_state[key] = []
        st.session_state[key].extend(default_value)

    # Display the current list of floats in a table
    if st.session_state[key]:
        st.table(pd.DataFrame(st.session_state[key], columns=[name]))

    # Input for new float value
    new_value = st.number_input(name, value=0.0, step=0.1, key=f"new_{key}")

    # Add button to append the new value to the list
    if st.button("➕ Add", key=f"add_{key}"):
        st.session_state[key].append(new_value)
        save_cpacs_file()
        st.rerun()

    # Remove button to remove the last value from the list
    if st.button("❌ Remove", key=f"remove_last_{key}"):
        if st.session_state[key]:
            st.session_state[key].pop()
            save_cpacs_file()
            st.rerun()


def int_vartype(tixi, xpath, default_value, name, key, description) -> None:
    with st.columns([1, 2])[0]:
        value = int(get_value_or_default(tixi, xpath, default_value))
        st.number_input(name, value=value, key=key, help=description, on_change=save_cpacs_file)


def float_vartype(tixi, xpath, default_value, name, key, description) -> None:
    value = get_value_or_default(tixi, xpath, default_value)
    with st.columns([1, 2])[0]:
        st.number_input(
            name,
            value=value,
            format="%0.3f",
            key=key,
            help=description,
            on_change=save_cpacs_file,
        )


def list_vartype(tixi, xpath, default_value, name, key, description):
    if default_value is None:
        log.warning(f"Could not create GUI for {xpath} in list_vartype.")
        return None

    value = get_value_or_default(tixi, xpath, default_value[0])
    idx = default_value.index(value)
    selected_value = st.radio(
        name,
        options=default_value,
        index=idx,
        key=key,
        help=description,
        on_change=save_cpacs_file,
    )
    return selected_value


def bool_vartype(tixi, xpath, default_value, name, key, description) -> None:
    st.checkbox(
        name,
        value=bool(get_value_or_default(tixi, xpath, default_value)),
        key=key,
        help=description,
        on_change=save_cpacs_file,
    )

def else_vartype(tixi, xpath, default_value, name, key, description) -> None:
    if name != "Choose mesh":
        value = str(get_value_or_default(tixi, xpath, default_value))
        with st.columns([1, 2])[0]:
            st.text_input(
                name,
                value=value,
                key=key,
                help=description,
                on_change=save_cpacs_file,
            )


# def simulation_settings(tixi, xpath, default_value, name, key, description) -> None:

#     if default_value is None:
#         log.warning(f"Could not create GUI for {xpath} in list_vartype.")
#         return None

#     value = get_value_or_default(tixi, xpath, default_value[0])
#     idx = default_value.index(value)
#     selected_value = st.radio(
#         name,
#         options=default_value,
#         index=idx,
#         key=key,
#         help=description,
#         on_change=save_cpacs_file,
#     )
#     if selected_value == 'Load Existing Simulations':
#         uploaded_file = st.file_uploader(
#             "Upload avl_simulations_results.csv file",
#             type=["csv"],
#             key='existing_avl_results',
#             on_change=save_cpacs_file,
#             help='load csv',
#         )

#         # Store at 
#         # Path(temp_dir, uploaded_file.name)




# def range_aeromap(tixi: Tixi3, xpath, default_value, name, key, description) -> None:
    
#     aeromap_selected=get_value(tixi, SMTRAIN_XPATH_AEROMAP_UID)

#     st.markdown('##### Select the parameters to consider')
#     for par in AEROMAP_FEATURES:
#         param_local_xpath = xpath + f"/parameter/{par}/status"
#         min_value_path = xpath + f"/parameter/{par}/min_value/value"
#         max_value_path = xpath + f"/parameter/{par}/max_value/value"

#         default_min_value = 0.0
#         default_max_value = 0.0

#         par_key = f"param_{par}"
#         min_key = f"param_{par}_min"
#         max_key = f"param_{par}_max"

#         col_1, col_2, col_3 = st.columns([0.5, 0.4, 0.4])

#         with col_1:
#             par_selected = st.checkbox(
#                 f"{par}",
#                 value=get_value_or_default(tixi, param_local_xpath, default_value),
#                 key=par_key,
#                 help=f"Enable DoE for {par}",
#                 on_change=save_cpacs_file,
#             )
#             if par_selected:
#                 with col_2:
#                     st.number_input(
#                         f"Min",
#                         value=get_value_or_default(tixi, min_value_path, default_min_value),
#                         format="%0.1f",
#                         key=min_key,
#                         help="Default set to 20% less than the current value. Adjustable as needed.",
#                         on_change=save_cpacs_file,
#                     )
#                 with col_3:
#                     st.number_input(
#                         f"Max",
#                         value=get_value_or_default(tixi, max_value_path, default_max_value),
#                         format="%0.1f",
#                         key=max_key,
#                         help="Default set to 20% more than the current value. Adjustable as needed.",
#                         on_change=save_cpacs_file,
#                     )
            

# def SectionsOptimise(tixi: Tixi3, xpath, default_value, name, key_wing, description) -> None:

#     uid_list = return_uid_wings_sections(tixi)

#     wings = sorted(set(wing_uid for (wing_uid, _) in uid_list))
        
#     st.markdown('##### Select the wings to optimise')
#     for wing_uid in wings:
#         wing_key = f"{key_wing}_wing_{wing_uid}"
#         wing_selected_xpath = xpath + f"/{wing_uid}/selected"
#         wing_selected = st.checkbox(
#             f"{wing_uid}",
#             value=get_value_or_default(tixi, wing_selected_xpath, default_value),
#             key=wing_key,
#             help=f"Enable optimization for {wing_uid}",
#             on_change=save_cpacs_file,
#         )

#         sections = [sec_uid for (wng, sec_uid) in uid_list if wng == wing_uid]
#         # show the section if the wing was selected
#         if wing_selected:
#                 st.markdown(f"##### ↪️ Sections of {wing_uid}")
#                 # sections = [sec_uid for (wng, sec_uid) in uid_list if wng == wing_uid]
#                 for section_uid in sections:
#                     sections_key = f"section_{section_uid}"
#                     sections_selected_xpath = xpath + f"/{wing_uid}/sections/{section_uid}/selected"
#                     col1,col2,col3 = st.columns([0.05,0.3,0.7])
#                     with col2:
#                         st.markdown("""--""")
#                         # section_numerate = section_uid.split("_")[1]
#                         section_selected = st.checkbox(
#                             f"{section_uid}",
#                             value=get_value_or_default(tixi, sections_selected_xpath, default_value),
#                             key=sections_key,
#                             help=f"Select if you want to optimise this section",
#                             on_change=save_cpacs_file,
#                         )
                    
#                     with col3:
#                         if section_selected:
#                                 st.markdown(f"##### Parameters")
#                                 for param in WING_PARAMETERS:
#                                     param_local_xpath = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/status"
#                                     min_value_path = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/min_value/value"
#                                     max_value_path = xpath + f"/{wing_uid}/sections/{section_uid}/parameters/{param}/max_value/value"
#                                     params_current_value_xpath = get_xpath_for_param(tixi, param, wing_uid, section_uid)

#                                     # print(f'XPATH for parameters: {param_xpath}')

#                                     current_value = get_value_or_default(tixi, params_current_value_xpath, default_value)

#                                     default_min_value = 0.8 * current_value
#                                     default_max_value = 1.2 * current_value

#                                     param_key = f'{sections_key}_{param}'
#                                     min_key = f'{sections_key}_{param}_min'
#                                     max_key = f'{sections_key}_{param}_max'

#                                     param_box = st.checkbox(
#                                         f"{param}",
#                                         value=get_value_or_default(tixi, param_local_xpath, default_value),
#                                         key=param_key,
#                                         help=f"Select if you want to optimise this parameter",
#                                         on_change=save_cpacs_file,
#                                     )

#                                     if param_box:
                                                                            
#                                         col_min, col_val, col_max = st.columns([0.5, 0.5, 0.5])
                                        
#                                         with col_min:
#                                             st.number_input(
#                                                 f"Min",
#                                                 value=get_value_or_default(tixi, min_value_path, default_min_value),
#                                                 format="%0.3f",
#                                                 key=min_key,
#                                                 help="Default set to 20% less than the current value. Adjustable as needed.",
#                                                 on_change=save_cpacs_file,
#                                             )

#                                         with col_val:
#                                             st.markdown("Current value:")
#                                             st.markdown(f"<= {current_value:.3f} <=")
                                        
#                                         with col_max:
#                                             st.number_input(
#                                                 f"Max",
#                                                 value=get_value_or_default(tixi, max_value_path, default_max_value),
#                                                 format="%0.3f",
#                                                 key=max_key,
#                                                 help="Default set to 20% more than the current value. Adjustable as needed.",
#                                                 on_change=save_cpacs_file,
#                                             )
                        #             else:
                        #                 tixi.updateBooleanElement(params_xpath, False)
                        # else: #section_selected:
                        #     tixi.updateBooleanElement(sections_selected_xpath, False)
                            
                        

        # # # print(f'storing at key: {key_wing}')
