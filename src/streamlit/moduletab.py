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

from src.streamlit.streamlitutils import section_edit_aeromap
from ceasiompy.utils.moduleinterfaces import get_specs_for_module

from src.streamlit.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    else_vartype,
    path_vartype,
    float_vartype,
    aeromap_checkbox,
    su2_data_settings,
    aeromap_selection,
    multiselect_vartype,
)

from typing import List
from collections import OrderedDict

from ceasiompy import log

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def order_by_gps(inputs: List) -> OrderedDict:
    groups = list(OrderedDict.fromkeys([v[6] for _, v in inputs.items()]))

    groups_container = OrderedDict()
    for group in groups:
        groups_container[group] = st.expander(f"**{group}**", expanded=True)

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


    # Iterate per group
    with groups_container[group]:

        # Check if the name or var_type is in the dictionary and call the corresponding function
        if name in aeromap_map:
            aeromap_map[name](session_state.cpacs, xpath, key, description)
        elif var_type == "path_type":
            path_vartype(default_value, key)
        elif var_type in vartype_map:
            vartype_map[var_type](
                session_state.cpacs.tixi,
                xpath,
                default_value,
                name,
                key,
                description
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
                description=description
            )

        session_state.xpath_to_update[xpath] = key


def add_module_tab() -> None:
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
        bool: bool_vartype
    }

    # Load each module iteratively
    for m, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):

        with tab:
            st.text("")
            specs = get_specs_for_module(module)
            # Check if specs.cpacs_inout is None
            if specs.cpacs_inout is None:
                log.error("specs.cpacs_inout is None. Ensure it is initialized before use.")
            else:
                inputs = specs.cpacs_inout.get_gui_dict()
            if not inputs:
                st.warning("No settings to modify this module.")
                continue

            groups_container = order_by_gps(inputs)

            for name, default_value, var_type, unit, xpath, description, group in inputs.values():
                
                key = f"{m}_{module}_{name.replace(' ', '')}_{group.replace(' ', '')}"
                process_unit(name, unit)
                
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

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
