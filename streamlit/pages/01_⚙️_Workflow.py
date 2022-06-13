from collections import OrderedDict
import os
from pathlib import Path

import streamlit as st
from ceasiompy.utils.commonpaths import CEASIOMPY_PATH
from ceasiompy.utils.moduleinterfaces import get_specs_for_module, get_submodule_list
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacsfunctions import add_value
from cpacspy.cpacspy import CPACS

st.set_page_config(page_title="Workflow", page_icon="⚙️")


def update_value(xpath, key):

    if key in st.session_state:
        value = st.session_state[key]
        add_value(st.session_state.cpacs.tixi, xpath, value)


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

    st.markdown("#### Add a module")

    # Get available modules
    module_list = get_submodule_list()
    module_list.remove("utils")
    module_list = sorted(module_list)

    if "workflow_modules" not in st.session_state:
        st.session_state["workflow_modules"] = []

    col1, col2, col3 = st.columns([8, 1, 1])

    with col1:
        module = st.selectbox("Select Module to the workflow:", module_list)

    with col2:
        st.markdown("#")
        if st.button("✔"):
            st.session_state.workflow_modules.append(module)


def save_cpacs_file():

    saved_cpacs_file = Path(st.session_state.workflow.working_dir, "test_cpacs.xml")
    st.session_state.cpacs.save_cpacs(saved_cpacs_file, overwrite=True)
    st.session_state.workflow.cpacs_in = saved_cpacs_file
    st.session_state.cpacs = CPACS(saved_cpacs_file)


def section_your_workflow():
    st.markdown("#### Your Workflow")
    # st.write("The module bellow will be executed in order:")

    add_module_expander()

    if not len(st.session_state.workflow_modules):
        st.warning("No module has been added to the workflow.")

    _, col1, col2, col3 = st.columns([9, 1, 1, 1])

    with col1:

        if st.button("❌", help="Remove last module") and len(st.session_state.workflow_modules):
            st.session_state.workflow_modules.pop()
            st.experimental_rerun()

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


def add_module_expander():

    for m, module in enumerate(st.session_state.workflow_modules):

        with st.expander(module, expanded=False):
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
                        st.selectbox(
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
                        st.selectbox(
                            name,
                            value=default_value,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == bool:
                        # key = f"{module}-{name.replace(' ', '_')}"
                        st.checkbox(
                            name,
                            value=default_value,
                            key=key,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )

                    elif var_type == "pathtype":
                        st.error("Pathtype not implemented yet")

                    else:
                        # key = f"{module}-{name.replace(' ', '_')}"
                        st.text_input(
                            name,
                            value=default_value,
                            key=key,
                            help=descr,
                            on_change=update_value(xpath, key),
                        )


if not "streamlit_path" in st.session_state:
    st.session_state["streamlit_path"] = Path(CEASIOMPY_PATH, "streamlit")

os.chdir(st.session_state["streamlit_path"])
# os.chdir(Path(CEASIOMPY_PATH, "streamlit"))

st.title("Workflow")

# Workflow
st.session_state.workflow = Workflow()
st.session_state.workflow.working_dir = Path("../WKDIR/test_st").absolute()  # TODO


# CPACS file
# st.session_state.cpacs_file = st.sidebar.file_uploader("Select a CPACS file", type=["xml"])
# if not st.session_state.cpacs_file:
#     st.error("No CPACS file has been selected.")
# else:
#     cpacs_new_path = Path(st.session_state.workflow.working_dir, st.session_state.cpacs_file.name)

#     with open(cpacs_new_path, "wb") as f:
#         f.write(st.session_state.cpacs_file.getbuffer())

#     # st.session_state.workflow.cpacs_in = cpacs_new_path
#     st.session_state.cpacs = CPACS(cpacs_new_path)

cpacs_new_path = Path("/home/jungo/github/CEASIOMpy/WKDIR/test_st/D150_simple.xml")
if not "cpacs" in st.session_state:
    st.session_state.cpacs = CPACS(cpacs_new_path)


section_predefined_workflow()

section_add_module()

section_your_workflow()
