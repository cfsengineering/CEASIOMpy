import streamlit as st
from ceasiompy.utils.moduleinterfaces import get_submodule_list

st.set_page_config(page_title="Workflow", page_icon="➡")


# Custom CSS
st.markdown(
    """
    <style>
    .css-1awtkze {
        border-radius:3px;
        background-color:#ff7f2a;
        padding: 6px;
    }
    .css-1awtkze:after {
    content:'';
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -20px;
    margin-top: 2px;
    width: 0;
    height: 0;
    border-top: solid 10px #9e9e93;
    border-left: solid 10px transparent;
    border-right: solid 10px transparent;
    }
    .stButton > button {
        border-radius:10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def section_predefined_workflow():

    st.markdown("#### Predefined Workflows")
    col1, col2, col3 = st.columns([4, 3, 3])

    with col1:
        if st.button("PyTornado → WeightConventional"):
            st.session_state.workflow_modules = ["PyTornado", "WeightConventional"]

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
        st.markdown(" ")
        module = st.selectbox("Module to add to the workflow:", available_module_list)

    with col2:
        st.markdown(" ")
        st.markdown("#")
        if st.button("✔", help="Add this module to the workflow"):
            st.session_state.workflow_modules.append(module)
            st.experimental_rerun()


st.title("Workflow")

section_predefined_workflow()

st.markdown("---")

section_add_module()

st.markdown("---")

st.info("You can use the sidebar to go to the Settings page")
