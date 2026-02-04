"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI objects in CEASIOMpy.
"""

# Imports

import pandas as pd
import streamlit as st

from cpacspy.cpacsfunctions import (
    create_branch,
    add_string_vector,
)

from tixi3.tixi3wrapper import (
    Tixi3,
    Tixi3Exception,
)

from ceasiompy import log


# Functions
def add_value(tixi: Tixi3, xpath, value) -> None:
    """
    Add a value (string, integer, float, list) at the given XPath,
    if the node does not exist, it will be created.
    Values will be overwritten if paths exists.
    """

    # Lists are different
    if isinstance(value, list):
        # Check if list is empty
        if not value:
            add_string_vector(st.session_state.cpacs.tixi, xpath, [""])
            return None
        add_string_vector(st.session_state.cpacs.tixi, xpath, value)
        return None

    # Strip trailing '/' (has no meaning here)
    xpath = xpath.rstrip("/")

    # Get the field name and the parent CPACS path
    xpath_child_name = xpath.split("/")[-1]
    xpath_parent = xpath[: -(len(xpath_child_name) + 1)]

    if not tixi.checkElement(xpath_parent):
        create_branch(tixi, xpath_parent)

    if not tixi.checkElement(xpath):
        tixi.createElement(xpath_parent, xpath_child_name)

    tixi.updateTextElement(xpath, str(value))


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
        # save_cpacs_file()


def _sync_multiselect_to_cpacs(tixi: Tixi3, xpath: str, values: list[float]) -> None:
    if tixi is None or xpath is None:
        raise TypeError(f"{tixi=} or {xpath=} is None.")
    create_branch(tixi, xpath)
    tixi.updateTextElement(xpath, ";".join(str(val) for val in values))


def multiselect_vartype(
    tixi: Tixi3,
    xpath: str,
    default_value,
    name,
    key,
    description,
) -> list[str]:
    if not default_value:
        raise 

    output = st.multiselect(
        label=name,
        options=default_value,
        key=key,
        help=description,
        default=default_value[0],
    )
    add_value(tixi, xpath, output)
    return output


def dataframe_vartype(
    tixi: Tixi3,
    xpath: str,
    default_value,
    name,
    key,
    description,
) -> list[float]:
    # Initialize the list in session state if it doesn't exist
    if key not in st.session_state:
        st.session_state[key] = []
        st.session_state[key].extend(default_value)
        _sync_multiselect_to_cpacs(tixi, xpath, st.session_state[key])

    gen_left_col, gen_right_col = st.columns(
        spec=[1, 2],
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
            spec=[3, 2, 2],
            vertical_alignment="bottom",
        )

        with left_col:
            # Input for new float value
            new_value = st.number_input(
                label=name,
                value=0.0,
                key=f"new_{key}",
                help=description,
            )

        with mid_col:
            # Add button to append the new value to the list
            if st.button(
                label="➕ Add",
                key=f"add_{key}",
                width="stretch",
                help="Add a new value to the list.",
            ):
                if new_value not in st.session_state[key]:
                    st.session_state[key].append(new_value)
                    _sync_multiselect_to_cpacs(tixi, xpath, st.session_state[key])
                    st.rerun()

        with right_col:
            # Remove button to remove the last value from the list
            if st.button(
                label="❌ Remove",
                key=f"remove_last_{key}",
                width="stretch",
                help="Remove the last value from the list.",
            ):
                if st.session_state[key]:
                    st.session_state[key].pop()
                    _sync_multiselect_to_cpacs(tixi, xpath, st.session_state[key])
                    st.rerun()

    _sync_multiselect_to_cpacs(tixi, xpath, st.session_state[key])
    return st.session_state[key]


def int_vartype(tixi, xpath, default_value, name, key, description) -> int:
    with st.columns([1, 2])[0]:
        raw_value = safe_get_value(tixi, xpath, default_value)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = int(default_value)
        output = st.number_input(
            name,
            value=value,
            key=key,
            help=description,
        )
        add_value(tixi, xpath, output)
        return output


def float_vartype(
    tixi: Tixi3,
    xpath,
    default_value,
    name,
    key,
    description,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    raw_value = safe_get_value(tixi, xpath, default_value)
    try:
        default_value = float(raw_value)
    except (TypeError, ValueError):
        default_value = float(default_value)

    with st.columns([1, 2])[0]:
        output = st.number_input(
            name,
            value=default_value,
            format="%g",
            key=key,
            help=description,
            min_value=min_value,
            max_value=max_value,
        )
        add_value(tixi, xpath, output)
        return output
    return default_value


def list_vartype(tixi: Tixi3, xpath, default_value, name, key, description) -> str:
    value = safe_get_value(tixi, xpath, default_value[0])

    # Check if value is in the list, otherwise use first option
    if value not in default_value:
        value = default_value[0]

    idx = default_value.index(value)
    output = st.radio(
        name,
        options=default_value,
        index=idx,
        key=key,
        help=description,
        horizontal=True,
    )
    add_value(tixi, xpath, output)
    return output


def add_ctrl_surf_vartype(
    tixi: Tixi3,
    xpath, default_value, name, key, description,
) -> float | None:
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
    )
    add_value(tixi, ctrl_xpath, selected)

    # if value of st.radio is npot 'none' then add float_vartype entry
    if selected is not None and str(selected).lower() != "none":
        deformation_angle = safe_get_value(tixi, angle_xpath, default_value=0.0)
        output = float_vartype(
            tixi,
            angle_xpath,
            deformation_angle,  # Default value for deformation angle
            "Deformation angle [deg]",
            f"{key}_deformation_angle",
            "Set the deformation angle for the selected control surface.",
        )
        return output
    return None


def bool_vartype(tixi, xpath, default_value, name, key, description) -> bool:
    raw_value = safe_get_value(tixi, xpath, default_value)
    if isinstance(raw_value, str):
        value = raw_value.strip().lower() in {"1", "true", "yes", "y"}
    else:
        value = bool(raw_value)

    output = st.checkbox(
        name,
        value=value,
        key=key,
        help=description,
    )
    add_value(tixi, xpath, output)
    return output
