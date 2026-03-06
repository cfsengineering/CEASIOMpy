
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to change settings of a CEASIOMpy workflow.
"""

# Imports
import numpy as np
import pandas as pd
import streamlit as st

from streamlitutils import create_sidebar
from ceasiompy.utils.moduletab import (
    checks,
    get_settings_of,
    section_edit_aeromap,
)

from pandas import DataFrame

from ceasiompy import MAIN_GAP
from constants import BLOCK_CONTAINER

# Constants

HOW_TO_TEXT = (
    "### How to use Settings?\n"
    "1. Edit **custom aeromap** \n"
    "1. Choose each modules' settings \n"
    "1. Go to *Run Workflow*\n"
)

PAGE_NAME = "Simulation Settings"


# Methods

def _render_aeromap_stats(aeromap_df: DataFrame) -> None:
    stats_fields = (
        ("altitude", "Altitude"),
        ("machNumber", "Mach"),
        ("angleOfAttack", "α°"),
        ("angleOfSideslip", "β°"),
    )

    available_fields = [field for field, _ in stats_fields if field in aeromap_df.columns]
    if not available_fields:
        return None

    numeric_df = aeromap_df[available_fields].apply(pd.to_numeric, errors="coerce")
    active_rows = numeric_df.notna().any(axis=1)
    numeric_df = numeric_df.loc[active_rows]
    aeromap_name = st.session_state.get("selected_aeromap_id", None)
    if numeric_df.empty:
        st.markdown(f"#### Aeromap {aeromap_name if aeromap_name is not None else ''} Stats")
        st.caption("No valid aeromap points.")
        return None

    aeromap_name = st.session_state.get("selected_aeromap_id", None)
    st.markdown(f"#### Aeromap {aeromap_name + ' ' if aeromap_name is not None else ''}Stats")
    st.caption(f"{len(numeric_df)} valid point{'s' if len(numeric_df) > 1 else ''}")
    stat_cols = st.columns(len(stats_fields))

    for idx, (field, label) in enumerate(stats_fields):
        with stat_cols[idx]:
            st.markdown(f"**{label}**")
            if field not in numeric_df:
                st.caption("Missing data")
                continue

            values = numeric_df[field].dropna().to_numpy(dtype=float, copy=False)
            if values.size == 0:
                st.caption("No data")
                continue

            st.caption(f"min: {values.min():.3g} | max: {values.max():.3g}")

            if values.size == 1 or np.all(values == values[0]):
                st.caption("Flat distribution")
            else:
                st.caption("Distribution")

            chart_df = DataFrame(
                {
                    field: values,
                    "_group": np.zeros(values.size, dtype=np.int8),
                },
            )
            st.vega_lite_chart(
                chart_df,
                {
                    "mark": {"type": "boxplot", "extent": "min-max", "size": 20},
                    "encoding": {
                        "x": {"field": "_group", "type": "nominal", "axis": None},
                        "y": {"field": field, "type": "quantitative", "title": None},
                    },
                    "height": 170,
                },
                width="stretch",
            )


def _section_settings() -> None:
    if "workflow_modules" not in st.session_state:
        st.warning("No module selected!")
        return

    if not len(st.session_state.workflow_modules):
        st.warning("You must first build a workflow in the corresponding tab.")

    st.markdown("---")

    left_col, right_col = st.columns(
        spec=2,
        gap=MAIN_GAP,
    )
    with left_col:
        # Show aeromap section for both 2D and 3D modes
        section_edit_aeromap()

    with right_col:
        aeromap_df = st.session_state.get("aeromap_df", None)
        if aeromap_df is not None:
            _render_aeromap_stats(aeromap_df)

    checks(st.session_state, st.tabs)

    # Load each module iteratively
    for _, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):
        with tab:
            get_settings_of(module)


# Main

if __name__ == "__main__":

    # Define interface
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
        .css-1awtkze {
            border-radius:3px;
            background-color: #9e9e93;
            padding: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    # Check if CPACS file exists (either in session state or on disk)
    display_settings = "cpacs" in st.session_state
    if not display_settings:
        st.warning("No CPACS file has been selected!")

    if display_settings:
        _section_settings()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
