"""
CEASIOMpy: Conceptual Aircraft Design Software

Entry point for the Streamlit UI with explicit page ordering.
"""

# Imports
import streamlit as st

# Main
def main() -> None:
    """Reorder files pages correctly."""
    page_home = st.Page(
        "pages/00_🏠_Home.py",
        title="Home",
        icon="🏠",
    )
    page_geometry = st.Page(
        "01_✈️_Geometry.py",
        title="Geometry",
        icon="✈️",
        default=True,
    )
    page_workflow = st.Page(
        "pages/02_ ➡_Workflow.py",
        title="Workflow",
        icon="➡️",
    )
    page_settings = st.Page(
        "pages/03_⚙️_Settings.py",
        title="Settings",
        icon="⚙️",
    )
    page_run = st.Page(
        "pages/04_▶️_Run_Workflow.py",
        title="Run Workflow",
        icon="▶️",
    )
    page_results = st.Page(
        "pages/05_📈_Results.py",
        title="Results",
        icon="📈",
    )

    pg = st.navigation(
        [
            page_home,
            page_geometry,
            page_workflow,
            page_settings,
            page_run,
            page_results,
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
