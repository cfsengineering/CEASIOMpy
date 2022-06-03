from ceasiompy.utils.moduleinterfaces import get_submodule_list
import streamlit as st

st.title("Workflow")

module_list = get_submodule_list()

module = st.selectbox("Add Module to the workflow:", module_list)

if "module_add" not in st.session_state:
    st.session_state["module_add"] = []

if st.button("Add Module"):
    st.session_state.module_add.append(module)

st.write("**Added module:**")

for i, module in enumerate(st.session_state.module_add):

    col1, col2 = st.columns(2)

    with col1:
        st.write(module)
    with col2:
        if st.button(f"remove {module}", key=i):
            st.session_state.module_add.remove(module)
