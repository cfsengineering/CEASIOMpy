import streamlit as st

st.title("Settings")


for module in st.session_state.module_add:
    with st.expander(module):
        st.write("Settings for:")
        st.write(module)


st.button("Save Settings and Run Workflow")
