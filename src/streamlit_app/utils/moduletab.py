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

from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.geometryfunctions import get_aircrafts_list
from ceasiompy.utils.moduleinterfaces import get_specs_for_module
from streamlit_app.utils.streamlitutils import (
    section_edit_stp_aeromap,
    section_edit_cpacs_aeromap,
)
from streamlit_app.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    else_vartype,
    path_vartype,
    float_vartype,
    aeromap_checkbox,
    aeromap_selection,
    multiselect_vartype,
    add_ctrl_surf_vartype,
)

from collections import OrderedDict
from tixi3.tixi3wrapper import Tixi3
from typing import (
    List,
    Dict,
)

from ceasiompy import log

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

    #
    tixi: Tixi3 = st.session_state.gui_settings.tixi

    default_index = int(
        default_value.index(
            get_value_or_default(tixi, xpath + "type", "CPACS2GMSH mesh")
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
            tixi=tixi,
            xpath=xpath,
            default_value="",
            name=name,
            key=key,
            description=description,
        )
        session_state.xpath_to_update[xpath] = key
    elif selected_type == "db":
        selected_func(
            tixi=tixi,
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

    if "modules_list" in session_state and session_state.modules_list:
        session_state.tabs = tabs(session_state.modules_list)

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

        tixi: Tixi3 = session_state.gui_settings.tixi

        # Check if the name or var_type is in the dictionary and call the corresponding function
        if name in aeromap_map:
            if "cpacs" in session_state:
                aeromap_map[name](
                    session_state.cpacs,
                    session_state.gui_settings,
                    xpath,
                    key,
                    description,
                )
            elif "stp" in session_state:
                aeromap_map[name](
                    session_state.stp,
                    session_state.gui_settings,
                    xpath,
                    key,
                    description,
                )
        elif var_type == "path_type":
            path_vartype(key)
        elif var_type in vartype_map:
            vartype_map[var_type](
                tixi, xpath, default_value, name, key, description
            )
        elif var_type == "multiselect":
            multiselect_vartype(default_value, name, key)
        else:
            else_vartype(
                tixi=tixi,
                xpath=xpath,
                default_value=default_value,
                name=name,
                key=key,
                description=description,
            )

        session_state.xpath_to_update[xpath] = key

        if var_type == "AddControlSurfaces":
            session_state.xpath_to_update[xpath + "/ctrlsurf"] = key
            session_state.xpath_to_update[
                xpath + "/deformation_angle"
            ] = f"{key}_deformation_angle"


def add_module_tab(new_file: bool) -> None:
    if "cpacs" not in st.session_state and "stp" not in st.session_state:
        st.warning("No Geometry files have been selected!")
        return

    with st.expander("**Edit Aeromaps**", expanded=False):
        if "cpacs" in st.session_state:
            section_edit_cpacs_aeromap()
        if "stp" in st.session_state:
            section_edit_stp_aeromap()

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
        "AddControlSurfaces": add_ctrl_surf_vartype,
    }

    dynamic_vartype_map = {
        "Path": path_vartype,
        "db": list_vartype,
        "CPACS2GMSH mesh": else_vartype,
    }
    # Load each module iteratively
    for m, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.modules_list)
    ):
        with tab :
            st.text("")
            specs = get_specs_for_module(
                module,
                reloading=new_file,
            )
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
