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
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils import get_wkdir
from ceasiompy.utils.cpacs_utils import SimpleCPACS

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
    multiselect_vartype,
    add_ctrl_surf_vartype,
    safe_get_value,
)

from collections import OrderedDict

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

    default_index = int(
        default_value.index(
            safe_get_value(session_state.cpacs.tixi, xpath + "type", "CPACS2GMSH mesh")
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


def order_by_gps(inputs: list) -> OrderedDict:
    groups = list(OrderedDict.fromkeys([v[6] for v in inputs.values()]))

    expanded_list: dict[str, list[bool]] = {}
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
    xpath,
    description,
    var_type,
    vartype_map,
    default_value,
) -> None:

    # Iterate per group
    with groups_container[group]:
        if var_type == "path_type":
            path_vartype(key)
        elif var_type in vartype_map:
            vartype_map[var_type](
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

        if var_type == "AddControlSurfaces":
            session_state.xpath_to_update[xpath + "/ctrlsurf"] = key
            session_state.xpath_to_update[
                xpath + "/deformation_angle"
            ] = f"{key}_deformation_angle"


def add_module_tab(new_file: bool) -> None:
    # Check if CPACS file exists (either in session state or on disk)
    if "cpacs" not in st.session_state:
        # Try to load from cpacs_path if available
        cpacs_path = None
        if "cpacs_path" in st.session_state:
            cpacs_path = Path(st.session_state["cpacs_path"])
        
        # If still no path, check default location
        if cpacs_path is None or not cpacs_path.exists():
            wkdir = get_wkdir()
            cpacs_path = wkdir / "ToolInput.xml"
        
        if cpacs_path.exists():
            try:
                # Try to load with full CPACS class (3D)
                st.session_state["cpacs"] = CPACS(str(cpacs_path))
                st.session_state["cpacs_path"] = str(cpacs_path)
            except Exception as e:
                # If that fails, use SimpleCPACS for 2D cases
                try:
                    st.session_state["cpacs"] = SimpleCPACS(str(cpacs_path))
                    st.session_state["cpacs_path"] = str(cpacs_path)
                    st.info("📋 Using 2D airfoil mode - some 3D features may not be available")
                except Exception as e2:
                    st.error(f"Failed to load CPACS file: {e2}")
                    return None
        else:
            st.warning("No CPACS file has been selected!")
            return None

    section_edit_aeromap()

    checks(st.session_state, st.tabs)

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
                gui_cond,
            ) in inputs.values():
                # Check gui_cond to determine if this parameter should be shown
                if gui_cond:
                    # Evaluate the condition
                    # Format: "xpath==value" or "xpath!=value"
                    try:
                        if "==" in gui_cond:
                            cond_xpath, cond_value = gui_cond.split("==")
                            cond_xpath = cond_xpath.strip()
                            cond_value = cond_value.strip()
                            # Check if xpath exists and has the specified value
                            if not st.session_state.cpacs.tixi.checkElement(cond_xpath):
                                continue
                            actual_value = st.session_state.cpacs.tixi.getTextElement(cond_xpath)
                            if actual_value != cond_value:
                                continue
                        elif "!=" in gui_cond:
                            cond_xpath, cond_value = gui_cond.split("!=")
                            cond_xpath = cond_xpath.strip()
                            cond_value = cond_value.strip()
                            # Check if xpath exists and does NOT have the specified value
                            if st.session_state.cpacs.tixi.checkElement(cond_xpath):
                                actual_value = st.session_state.cpacs.tixi.getTextElement(cond_xpath)
                                if actual_value == cond_value:
                                    continue
                    except Exception as e:
                        # If condition evaluation fails, skip this parameter
                        log.warning(f"Failed to evaluate gui_cond '{gui_cond}': {e}")
                        continue
                
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
