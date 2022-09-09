from pathlib import Path

import ceasiompy.__init__
import streamlit as st

CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

st.set_page_config(page_title="Results", page_icon="📈")
st.title("Results")

st.info("The results page is under construction, it can not be use yet!")


def show_logs():

    st.markdown("#### Logfile")

    with open(LOGFILE, "r") as f:
        lines = f.readlines()

    lines_str = "\n".join(lines)

    st.text_area("logs", lines_str, height=300, disabled=True)


def show_results():

    st.markdown("#### Results")

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    # TODO: all this part should be improved
    results_dir = Path(st.session_state.workflow.working_dir)
    last_workflow = 0
    for dir in results_dir.iterdir():
        if "Workflow_" in str(dir):
            last_workflow = max(last_workflow, int(str(dir).split("_")[-1]))

    results_dir = Path(results_dir, f"Workflow_{str(last_workflow).rjust(3, '0')}", "Results")
    st.text(f"The Results dir is: {str(results_dir)}")
    for dir in results_dir.iterdir():
        if dir.is_dir():
            with st.expander(dir.name, expanded=False):
                st.text("")
                for file in dir.iterdir():
                    st.markdown(file)


show_logs()
show_results()
