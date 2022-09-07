import os
from collections import OrderedDict
from pathlib import Path

import streamlit as st
from ceasiompy.utils.commonpaths import CEASIOMPY_PATH
from ceasiompy.utils.moduleinterfaces import (get_specs_for_module,
                                              get_submodule_list)
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacsfunctions import add_string_vector, add_value
from cpacspy.cpacspy import CPACS
from directory_picker import st_directory_picker

st.set_page_config(page_title="Workflow", page_icon="⚙️")


def update_value(xpath, key):

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


def section_select_working_dir():

    st.markdown("#### Working directory")

    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()
    st.session_state.workflow.working_dir = st_directory_picker(
        Path("../WKDIR/test_st").absolute()
    )


def section_select_cpacs():

    st.markdown("#### CPACS file")

    st.session_state.cpacs_file = st.file_uploader("Select a CPACS file", type=["xml"])

    if st.session_state.cpacs_file:

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )

        with open(cpacs_new_path, "wb") as f:
            f.write(st.session_state.cpacs_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        st.session_state.cpacs = CPACS(cpacs_new_path)

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")

        if "cpacs" not in st.session_state:
            st.session_state.cpacs = CPACS(cpacs_new_path)

    else:
        st.warning("No CPACS file has been selected!")


def section_predefined_workflow():

    st.markdown("#### Predefined Workflows")
    col1, col2, col3 = st.columns([3, 3, 3])

    with col1:
        if st.button("PyTornado → Plots"):
            st.session_state.workflow_modules = ["PyTornado", "PlotAeroCoefficients"]

    with col2:
        if st.button("CPACS2GMSH → SU2Run"):
            st.session_state.workflow_modules = ["CPACS2GMSH", "SU2Run"]

    with col3:
        if st.button("SUMO → SU2Run"):
            st.session_state.workflow_modules = ["CPACS2SUMO", "SUMOAutoMesh", "SU2Run"]


def section_add_module():

    st.markdown("#### Your workflow")

    if "workflow_modules" not in st.session_state:
        st.session_state["workflow_modules"] = []

    if len(st.session_state.workflow_modules):
        for i, module in enumerate(st.session_state.workflow_modules):

            col1, col2, col3, _ = st.columns([6, 1, 1, 5])

            with col1:
                st.markdown(f"**{module}**")

            with col2:
                if st.button("⬆️", key=f"move{i}", help="Move up") and i != 0:
                    st.session_state.workflow_modules.pop(i)
                    st.session_state.workflow_modules.insert(i - 1, module)
                    st.experimental_rerun()

            with col3:
                if st.button("❌", key=f"del{i}", help=f"Remove {module} from the workflow"):
                    st.session_state.workflow_modules.pop(i)
                    st.experimental_rerun()

    else:
        st.warning("No module has been added to the workflow.")

    module_list = get_submodule_list()
    module_list.remove("utils")
    available_module_list = sorted(module_list)

    col1, col2 = st.columns(2)

    with col1:
        module = st.selectbox("Module to add to the workflow:", available_module_list)

    with col2:
        st.markdown("#")
        if st.button("✔", help="Add this module to the workflow"):
            st.session_state.workflow_modules.append(module)
            st.experimental_rerun()


def section_your_workflow():
    st.markdown("#### Settings")

    if "workflow_modules" not in st.session_state:
        st.warning("No module selected!")

    add_module_tab()

    if not len(st.session_state.workflow_modules):
        st.warning("No module has been added to the workflow.")

    _, col2, col3 = st.columns([10, 1, 1])

    with col2:

        if st.button("💾", help="Save CPACS"):
            save_cpacs_file()

    with col3:

        if st.button("▶️", help="Run the workflow "):

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


def add_module_tab():

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
                st.warning("No specs found for this module")
                return

            groups = list(OrderedDict.fromkeys([v[6] for _, v in inputs.items()]))

            groups_container = OrderedDict()
            for group in groups:
                groups_container[group] = st.container()

                with groups_container[group]:
                    st.markdown(f"**{group}**")

            for name, default_value, var_type, unit, xpath, descr, group in inputs.values():

                with groups_container[group]:

                    key = f"{m}_{module}_{name.replace(' ', '')}-"

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


st.title("Workflow")

section_select_working_dir()

st.markdown("---")

section_select_cpacs()

st.markdown("---")

section_predefined_workflow()

section_add_module()

st.markdown("---")

section_your_workflow()
