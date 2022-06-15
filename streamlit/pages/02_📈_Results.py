from pathlib import Path

import ceasiompy.__init__
import streamlit as st

st.set_page_config(page_title="Results", page_icon="📈")
st.title("Results")

# results_dir = Path(st.session_state.workflow.current_wkflow_dir, "Results")
# st.text(f"The Results dir is: {results_dir}")
# for dir in results_dir.iterdir():
#     if dir.is_dir():
#         with st.expander(dir.name, expanded=False):
#             st.text(f"")
#             for file in dir.iterdir():
#                 st.text(file)

CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]

LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")
st.text(LOGFILE)
with open(LOGFILE, "r") as f:
    lines = f.readlines()

lines_str = "\n".join(lines)

st.text_area("logs", lines_str, height=300, disabled=True)
