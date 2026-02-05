"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import streamlit as st

from ceasiompy.utils.guiobjects import (
    list_vartype,
    float_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonxpaths import (
    RANGE_XPATH,
    ENGINE_TYPE_XPATH,
)

# Variable


def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.container(
        border=True,
    ):
        float_vartype(
            tixi=tixi,
            xpath=RANGE_XPATH + "/NetForce",
            description="Engine net force.",
            default_value=2000.0,
            name="NetForce",
            key="thermodat_net_force",
        )

        list_vartype(
            tixi=tixi,
            xpath=ENGINE_TYPE_XPATH,
            default_value=["Turbojet", "Turbofan"],
            description="",
            name="Turbojet or Turbofan",
            key="thermoda_turbo_fan_jet",
        )
