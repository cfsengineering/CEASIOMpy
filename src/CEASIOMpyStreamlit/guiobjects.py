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

from tixi3.tixi3wrapper import (
    Tixi3,
    Tixi3Exception,
)

from ceasiompy import log

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def safe_get_value(tixi: Tixi3, xpath, default_value):
    """Read a value without creating missing CPACS branches."""

    if tixi is None:
        return default_value

    try:
        if tixi.checkElement(xpath):
            return tixi.getTextElement(xpath)
    except Tixi3Exception:
        return default_value

    return default_value


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


def multiselect_vartype(default_value, name, key) -> list[float]:
    # Initialize the list in session state if it doesn't exist
    if key not in st.session_state:
        st.session_state[key] = []
        st.session_state[key].extend(default_value)

    gen_left_col, gen_right_col = st.columns(
        spec=[2, 3],
        vertical_alignment="center",
    )

    with gen_left_col:
        # Input for new float value
        # Display the current list of floats in a table
        if st.session_state[key]:
            st.table(pd.DataFrame(st.session_state[key], columns=[name]))

    with gen_right_col:
        # Add button to append the new value to the list
        left_col, mid_col, right_col = st.columns(
            spec=[1, 1, 1],
            vertical_alignment="bottom",
        )

        with left_col:
            # Input for new float value
            new_value = st.number_input(
                label=name,
                value=0.0,
                key=f"new_{key}",
            )

        with mid_col:
            # Add button to append the new value to the list
            if st.button(
                label="➕ Add",
                key=f"add_{key}",
            ):
                if new_value not in st.session_state[key]:
                    st.session_state[key].append(new_value)
                    save_cpacs_file()
                    st.rerun()

        with right_col:
            # Remove button to remove the last value from the list
            if st.button(
                label="❌ Remove",
                key=f"remove_last_{key}",
            ):
                if st.session_state[key]:
                    st.session_state[key].pop()
                    save_cpacs_file()
                    st.rerun()

    return st.session_state[key]


def int_vartype(tixi, xpath, default_value, name, key, description) -> int:
    with st.columns([1, 2])[0]:
        raw_value = safe_get_value(tixi, xpath, default_value)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = int(default_value)
        return st.number_input(
            name,
            value=value,
            key=key,
            help=description,
            on_change=save_cpacs_file,
        )


def float_vartype(tixi, xpath, default_value, name, key, description) -> float:
    raw_value = safe_get_value(tixi, xpath, default_value)
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = float(default_value)
    with st.columns([1, 2])[0]:
        return st.number_input(
            name,
            value=value,
            format="%g",
            key=key,
            help=description,
            on_change=save_cpacs_file,
        )
    return value


def list_vartype(tixi, xpath, default_value, name, key, description) -> str:
    # Special handling for aeromap selection when default_value is None
    if default_value is None:
        from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH

        if xpath == SELECTED_AEROMAP_XPATH:
            # Get available aeromaps from CPACS
            aeromap_list = st.session_state.cpacs.get_aeromap_uid_list()
            if not aeromap_list:
                st.warning("No aeromaps available. Please create an aeromap first.")
                return None
            default_value = aeromap_list
        else:
            raise ValueError(f"Could not create GUI for {xpath} in list_vartype.")

    value = safe_get_value(tixi, xpath, default_value[0])

    # Check if value is in the list, otherwise use first option
    if value not in default_value:
        value = default_value[0]

    idx = default_value.index(value)
    return st.radio(
        name,
        options=default_value,
        index=idx,
        key=key,
        help=description,
        horizontal=True,
        on_change=save_cpacs_file,
    )


def add_ctrl_surf_vartype(tixi, xpath, default_value, name, key, description) -> None:
    '''
    Specific function for selecting a deformation angle in the CPACSUpdater module.
    Special request of Giacomo Benedetti.
    '''
    if default_value is None:
        log.warning(f"Could not create GUI for {xpath} in add_ctrl_surf_vartype.")
        return None

    ctrl_xpath = xpath + "/ctrlsurf"
    angle_xpath = xpath + "/deformation_angle"

    value = safe_get_value(tixi, ctrl_xpath, default_value[0])
    idx = default_value.index(value)
    selected = st.radio(
        name,
        options=default_value,
        index=idx,
        key=key,
        help=description,
        on_change=save_cpacs_file,
    )

    # if value of st.radio is npot 'none' then add float_vartype entry
    if selected is not None and str(selected).lower() != "none":
        deformation_angle = safe_get_value(tixi, angle_xpath, default_value=0.0)
        float_vartype(
            tixi,
            angle_xpath,
            deformation_angle,  # Default value for deformation angle
            "Deformation angle [deg]",
            f"{key}_deformation_angle",
            "Set the deformation angle for the selected control surface.",
        )


def bool_vartype(tixi, xpath, default_value, name, key, description) -> bool:
    raw_value = safe_get_value(tixi, xpath, default_value)
    if isinstance(raw_value, str):
        value = raw_value.strip().lower() in {"1", "true", "yes", "y"}
    else:
        value = bool(raw_value)

    return st.checkbox(
        name,
        value=value,
        key=key,
        help=description,
        on_change=save_cpacs_file,
    )


def else_vartype(tixi, xpath, default_value, name, key, description) -> None:
    if name != "Choose mesh":
        value = str(safe_get_value(tixi, xpath, default_value))
        with st.columns([1, 2])[0]:
            st.text_input(
                name,
                value=value,
                key=key,
                help=description,
                on_change=save_cpacs_file,
            )
