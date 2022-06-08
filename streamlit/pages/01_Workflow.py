from pathlib import Path
from ceasiompy.utils.moduleinterfaces import get_specs_for_module, get_submodule_list
import streamlit as st
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import add_value
from ceasiompy.utils.workflowclasses import Workflow


def update_value(xpath, key):

    if key not in st.session_state:
        st.error("No value for this key")
        return
    else:
        value = st.session_state[key]

    add_value(st.session_state.cpacs.tixi, xpath, value)


def add_module_expander(module):

    with st.expander(module, expanded=False):
        st.text("")
        specs = get_specs_for_module(module)
        inputs = specs.cpacs_inout.get_gui_dict()

        if not inputs:
            st.warning("No specs found for this module")
            return

        # TODO: how to separate groups
        # groups = {v[6] for _, v in inputs.items()}
        # st.table(groups)

        for name, default_value, var_type, unit, xpath, descr, group in inputs.values():

            col1, col2, col3 = st.columns([6, 1, 1])

            with col1:
                aeromap_list = st.session_state.cpacs.get_aeromap_uid_list()
                if name == "__AEROMAP_SELECTION":
                    st.selectbox(
                        "Select an aeromap",
                        key=f"{module}-selec-aeromap",
                        options=aeromap_list,
                    )
                elif name == "__AEROMAP_CHECHBOX":
                    st.multiselect(
                        "Select one or several aeromaps",
                        key=f"{module}-selec-aeromap",
                        options=aeromap_list,
                    )

                # TODO: not all type has been covered

                elif var_type == list:
                    st.selectbox(name, default_value, help=descr)
                elif var_type == bool:
                    st.checkbox(name, default_value, help=descr)
                else:
                    key = f"{module}-{name.replace(' ', '_')}"
                    st.text_input(
                        name,
                        default_value,
                        key=key,
                        help=descr,
                        on_change=update_value(xpath, key),
                    )

            with col2:
                if unit not in ["", "1", None]:
                    st.markdown("#")
                    st.markdown(f"{unit}")

            # TODO: to remove when groups are better organized
            with col3:
                st.markdown(group)


st.title("CEASIOMpy Workflow")

# Workflow
st.session_state.workflow = Workflow()
st.session_state.workflow.working_dir = Path("../WKDIR/test_st").absolute()  # TODO

# CPACS file
st.session_state.cpacs_file = st.sidebar.file_uploader("Select a CPACS file", type=["xml"])
if not st.session_state.cpacs_file:
    st.error("No CPACS file has been selected.")
else:
    cpacs_new_path = Path(st.session_state.workflow.working_dir, st.session_state.cpacs_file.name)

    with open(cpacs_new_path, "wb") as f:
        f.write(st.session_state.cpacs_file.getbuffer())

    st.session_state.workflow.cpacs_in = cpacs_new_path
    st.session_state.cpacs = CPACS(cpacs_new_path)


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

with col3:
    st.markdown("#")
    if st.button("❌") and len(st.session_state.workflow_modules) > 0:
        st.session_state.workflow_modules.pop()

st.markdown("#### Predefined Workflows")
col1, col2, col3 = st.columns([3, 3, 1])

with col1:
    if st.button("PyTornado → PlotAeroCoefficents"):
        st.session_state.workflow_modules = ["PyTornado", "PlotAeroCoefficients"]

with col2:
    if st.button("CPACS2GMSH → SU2Run"):
        st.session_state.workflow_modules = ["SettingsGUI", "CPACS2GMSH", "SU2Run"]


st.markdown("### Your Workflow")
# st.write("The module bellow will be executed in order:")

for i, module in enumerate(st.session_state.workflow_modules):
    add_module_expander(module)

if not len(st.session_state.workflow_modules):
    st.warning("No module has been added to the workflow.")


col1, col2, col3 = st.columns([3, 1, 1])

with col2:

    if st.button("save CPACS"):
        st.session_state.cpacs.save_cpacs(
            Path(st.session_state.workflow.working_dir, "test_cpacs.xml"), overwrite=True
        )

with col3:
    if st.button("Run Workflow"):
        st.session_state.workflow.modules_list = st.session_state.workflow_modules
        st.session_state.workflow.optim_method = "None"
        st.session_state.workflow.module_optim = ["NO"] * len(
            st.session_state.workflow.modules_list
        )

        st.session_state.workflow.write_config_file()
        st.session_state.workflow.set_workflow()
        st.session_state.workflow.run_workflow()
