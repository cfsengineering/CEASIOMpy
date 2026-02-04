"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SkinFriction.
"""

# Imports
import streamlit as st

from cpacspy.cpacspy import CPACS

from ceasiompy.utils.guiobjects import (
    int_vartype,
    float_vartype,
)

from ceasiompy.utils.commonxpaths import (
    RANGE_CRUISE_ALT_XPATH,
    RANGE_CRUISE_MACH_XPATH,
)


# Functions

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.container(
        border=True,
    ):

        st.markdown("#### Cruise Settings")

        float_vartype(
            tixi=tixi,
            default_value=0.78,
            description="Cruise mach of aircraft.",
            name="Aircraft cruise mach",
            xpath=RANGE_CRUISE_MACH_XPATH,
            key="skinfriction_cruise_mach",
        )

        int_vartype(
            tixi=tixi,
            default_value=0.78,
            description="Cruise altitude of aircraft.",
            name="Aircraft cruise altitude",
            xpath=RANGE_CRUISE_ALT_XPATH,
            key="skinfriction_cruise_altitude",
        )
