from pathlib import Path

import ceasiompy.__init__
import streamlit as st

st.set_page_config(page_title="Results", page_icon="📈")
st.title("Results")

# TODO: all this part should be improved
results_dir = Path(st.session_state.workflow.working_dir)
last_workflow = 0
for dir in results_dir.iterdir():
    if "Workflow_" in str(dir):
        last_workflow = max(last_workflow, int(str(dir).split("_")[-1]))

results_dir = Path(results_dir, f"Workflow_0{last_workflow}", "Results")
st.text(f"The Results dir is: {str(results_dir)}")
for dir in results_dir.iterdir():
    if dir.is_dir():
        with st.expander(dir.name, expanded=False):
            st.text(f"")
            for file in dir.iterdir():
                st.markdown(file)

CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]

LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")
st.text(LOGFILE)
with open(LOGFILE, "r") as f:
    lines = f.readlines()

lines_str = "\n".join(lines)

st.text_area("logs", lines_str, height=300, disabled=True)
