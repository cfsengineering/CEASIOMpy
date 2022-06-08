import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Results", page_icon="📈")
st.title("Results")

results_dir = Path(st.session_state.workflow.current_wkflow_dir, "Results")

st.text(f"The Results dir is: {results_dir}")

for dir in results_dir.iterdir():
    if dir.is_dir():
        with st.expander(dir.name, expanded=False):
            st.text(f"")
            for file in dir.iterdir():
                st.text(file)
