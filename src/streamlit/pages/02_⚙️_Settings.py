import os
from collections import OrderedDict
from pathlib import Path

import streamlit as st
from ceasiompy.utils.commonpaths import CEASIOMPY_PATH
from ceasiompy.utils.moduleinterfaces import get_specs_for_module, get_submodule_list
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacsfunctions import add_string_vector, add_value
from cpacspy.cpacspy import CPACS


st.set_page_config(page_title="Workflow", page_icon="⚙️")


def update_value(xpath, key):

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")

    if key in st.session_state:
        value = st.session_state[key]

        if isinstance(value, list):
            add_string_vector(st.session_state.cpacs.tixi, xpath, value)
            return

        add_value(st.session_state.cpacs.tixi, xpath, value)


def save_cpacs_file():

    saved_cpacs_file = Path(st.session_state.workflow.working_dir, "CPACS_selected_from_GUI.xml")
    st.session_state.cpacs.save_cpacs(saved_cpacs_file, overwrite=True)
    st.session_state.workflow.cpacs_in = saved_cpacs_file
    st.session_state.cpacs = CPACS(saved_cpacs_file)


def add_module_tab():

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    if "tabs" not in st.session_state:
        st.session_state["tabs"] = []

    if st.session_state.workflow_modules:
        st.session_state.tabs = st.tabs(st.session_state.workflow_modules)

    for m, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):
        with tab:
            st.text("")
            specs = get_specs_for_module(module)
            inputs = specs.cpacs_inout.get_gui_dict()

            if not inputs:
                st.warning("No specs required for this module")
                continue

            groups = list(OrderedDict.fromkeys([v[6] for _, v in inputs.items()]))

            groups_container = OrderedDict()
            for group in groups:
                groups_container[group] = st.container()

                with groups_container[group]:
                    st.markdown(f"**{group}**")

            for name, default_value, var_type, unit, xpath, descr, group in inputs.values():

                with groups_container[group]:

                    key = f"{m}_{module}_{name.replace(' ', '')}_{group.replace(' ', '')}"

                    if unit not in ["", "1", None]:
                        name = f"{name} {unit}"

                    if name == "__AEROMAP_SELECTION":
                        st.radio(
                            "Select an aeromap",
                            key=key,
                            options=st.session_state.cpacs.get_aeromap_uid_list(),
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif name == "__AEROMAP_CHECHBOX":
                        st.multiselect(
                            "Select one or several aeromaps",
                            key=key,
                            options=st.session_state.cpacs.get_aeromap_uid_list(),
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == int or var_type == float:

                        st.number_input(
                            name,
                            value=default_value,
                            key=key,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == list:
                        st.radio(
                            name,
                            options=default_value,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == bool:
                        st.checkbox(
                            name,
                            value=default_value,
                            key=key,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == "pathtype":
                        st.error("Pathtype not implemented yet")
                        # st.file_uploader(
                        #     "Select a file",
                        #     key=key,
                        #     type=["xml"],
                        #     help=descr,
                        #     on_change=update_value(xpath, key),
                        # )

                    else:
                        st.text_input(
                            name,
                            value=default_value,
                            key=key,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )


def section_your_workflow():
    st.markdown("#### Settings")

    if "workflow_modules" not in st.session_state:
        st.warning("No module selected!")

    add_module_tab()

    if not len(st.session_state.workflow_modules):
        st.warning("No module has been added to the workflow.")

    _, col2, col3 = st.columns([6, 1, 1])

    with col2:

        if st.button("Save 💾", help="Save CPACS"):
            save_cpacs_file()

    with col3:

        if st.button("Run ▶️", help="Run the workflow "):

            save_cpacs_file()

            st.session_state.workflow.modules_list = st.session_state.workflow_modules
            st.session_state.workflow.optim_method = "None"
            st.session_state.workflow.module_optim = ["NO"] * len(
                st.session_state.workflow.modules_list
            )
            st.session_state.workflow.write_config_file()

            # Run workflow from an external script
            config_path = Path(st.session_state.workflow.working_dir, "ceasiompy.cfg")
            print(Path().cwd())
            os.system(f"python run_workflow.py {config_path}  &")


section_your_workflow()
