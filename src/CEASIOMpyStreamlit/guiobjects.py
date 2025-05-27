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
)

from ceasiompy import log

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

    if key in st.session_state:
        st.success(f"Uploaded file: {st.session_state[key]}")


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


def list_vartype(tixi, xpath, default_value, name, key, description) -> None:
    if default_value is None:
        log.warning(f"Could not create GUI for {xpath} in list_vartype.")
    else:
        value = get_value_or_default(tixi, xpath, default_value[0])
        idx = default_value.index(value)
        st.radio(
            name,
            options=default_value,
            index=idx,
            key=key,
            help=description,
            on_change=save_cpacs_file,
        )


def bool_vartype(tixi, xpath, default_value, name, key, description) -> None:
    st.checkbox(
        name,
        value=get_value_or_default(tixi, xpath, default_value),
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
