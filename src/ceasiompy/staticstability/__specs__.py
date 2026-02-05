"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of StaticStability.
"""

# Imports
import streamlit as st

from ceasiompy.utils.guiobjects import bool_vartype

from cpacspy.cpacspy import CPACS

from ceasiompy.staticstability import STATICSTABILITY_LR_XPATH


# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.container(
        border=True,
    ):
        bool_vartype(
            tixi=tixi,
            name="Linear Regression",
            default_value=False,
            xpath=STATICSTABILITY_LR_XPATH,
            key="static_stability_linear_regression_bool",
            description="Use linear regression or the derivative's values",
        )
