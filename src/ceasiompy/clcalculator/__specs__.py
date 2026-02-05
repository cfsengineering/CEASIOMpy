"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CLCalculator.
"""

# Imports
import streamlit as st

from ceasiompy.utils.ceasiompyutils import safe_remove
from ceasiompy.utils.guiobjects import (
    list_vartype,
    float_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy.clcalculator import (
    MASS_TYPES,
    CLCALC_MASS_TYPE_XPATH,
    CLCALC_LOAD_FACT_XPATH,
    CLCALC_CRUISE_ALT_XPATH,
    CLCALC_CRUISE_MACH_XPATH,
    CLCALC_CUSTOM_MASS_XPATH,
    CLCALC_PERC_FUEL_MASS_XPATH,
)


# Functions

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.container(
        border=True,
    ):

        mass_type = list_vartype(
            tixi=tixi,
            xpath=CLCALC_MASS_TYPE_XPATH,
            name="Mass Type",
            default_value=MASS_TYPES,
            key="mass_type",
            description="Type of mass to use for CL calculation.",
        )

        if mass_type == "Custom":
            float_vartype(
                tixi=tixi,
                xpath=CLCALC_CUSTOM_MASS_XPATH,
                description="Mass value user specified (custom).",
                name="Mass Value.",
                default_value=1.0,
                key="custom_mass",
            )
        else:
            safe_remove(tixi, xpath=CLCALC_CUSTOM_MASS_XPATH)

        if mass_type == r"%% fuel mass":
            float_vartype(
                tixi=tixi,
                xpath=CLCALC_PERC_FUEL_MASS_XPATH,
                default_value=100.0,
                name="Percent fuel mass.",
                description="Percentage of fuel mass between mTOM and mZFM.",
                key="percent_fuel_mass",
            )
        else:
            safe_remove(tixi, xpath=CLCALC_PERC_FUEL_MASS_XPATH)

    with st.container(
        border=True,
    ):
        st.markdown("#### Cruise Settings")

        float_vartype(
            tixi=tixi,
            xpath=CLCALC_CRUISE_MACH_XPATH,
            default_value=0.78,
            description="Aircraft cruise Mach number.",
            name="Cruise Mach",
            key="mach_cruise",
        )

        float_vartype(
            tixi=tixi,
            xpath=CLCALC_CRUISE_ALT_XPATH,
            default_value=1000.0,
            description="Aircraft cruise altitude.",
            name="Cruise Altitude",
            key="altitude_cruise",
        )

        float_vartype(
            tixi=tixi,
            xpath=CLCALC_LOAD_FACT_XPATH,
            default_value=1.05,
            description="Load factor cruise of aircraft.",
            name="Load Factor",
            key="load_factor_cruise",
        )
