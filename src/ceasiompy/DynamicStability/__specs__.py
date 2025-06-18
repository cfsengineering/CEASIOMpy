"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of DynamicStability.

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE
from ceasiompy.SU2Run import SOFTWARE_NAME as SU2_SOFTWARE
from ceasiompy.DynamicStability import (
    INCLUDE_GUI,
    DYNAMICSTABILITY_NCHORDWISE_XPATH,
    DYNAMICSTABILITY_NSPANWISE_XPATH,
    DYNAMICSTABILITY_VISUALIZATION_XPATH,
    DYNAMICSTABILITY_CGRID_XPATH,
    DYNAMICSTABILITY_SOFTWARE_XPATH,
    DYNAMICSTABILITY_XREF_XPATH,
    DYNAMICSTABILITY_YREF_XPATH,
    DYNAMICSTABILITY_ZREF_XPATH,
    DYNAMICSTABILITY_DEFAULTREF_XPATH,
    DYNAMICSTABILITY_OPEN_SDSA_XPATH,
    DYNAMICSTABILITY_AEROMAP_UID_XPATH,
    DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH,
    DYNAMICSTABILITY_BETA_DERIVATIVES_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    unit=None,
    descr="Name of the aero map for dot-derivatives calculatations",
    xpath=DYNAMICSTABILITY_AEROMAP_UID_XPATH,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="alpha_alpha_dot_derivatives",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Compute Alpha, Alpha-dot derivatives",
    xpath=DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Alpha, Alpha-dot derivatives",
    gui_group="Dot Derivatives Type",
)

cpacs_inout.add_input(
    var_name="beta_beta_dot_derivatives",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Compute Beta, Beta-dot derivatives",
    xpath=DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Beta, Beta-dot derivatives",
    gui_group="Dot Derivatives Type",
)

cpacs_inout.add_input(
    var_name="open_sdsa",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="If you want to open SDSA with the data from ceasiompy.db"
    "(You need to make around 6000 computations for sdsa to work properly)",
    xpath=DYNAMICSTABILITY_OPEN_SDSA_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Open SDSA",
    gui_group="Open SDSA",
)

cpacs_inout.add_input(
    var_name="dynamic_stability_software_data",
    var_type=list,
    default_value=[f"{AVL_SOFTWARE}", f"{SU2_SOFTWARE}"],
    unit=None,
    descr="Which data from ceasiompy.db to use.",
    xpath=DYNAMICSTABILITY_SOFTWARE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Use data from which software",
    gui_group="Software Settings",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=DYNAMICSTABILITY_NCHORDWISE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of chordwise vortices",
    gui_group="Aerogrid Settings",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=50,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=DYNAMICSTABILITY_NSPANWISE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of spanwise vortices",
    gui_group="Aerogrid Settings",
)

cpacs_inout.add_input(
    var_name="dlm_aerogrid_visualization",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Visualization of the aerogrid the DLM is going to use",
    xpath=DYNAMICSTABILITY_VISUALIZATION_XPATH,
    gui=INCLUDE_GUI,
    gui_name="aerogrid visualization",
    gui_group="Visualization",
)

cpacs_inout.add_input(
    var_name="c_grid",
    var_type=str,
    default_value="C:/Program Files/SDSA/Grid/test.inp",
    unit=None,
    descr="Select the cGrid path",
    xpath=DYNAMICSTABILITY_CGRID_XPATH,
    gui=INCLUDE_GUI,
    gui_name="cGrid path",
    gui_group="cGrid Setting",
)

cpacs_inout.add_input(
    var_name="use_default",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="If you want the default (leave on True) or want to specify (False)",
    xpath=DYNAMICSTABILITY_DEFAULTREF_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Default Reference Point",
    gui_group="Refence Point Setting",
)

cpacs_inout.add_input(
    var_name="dynstab_xref",
    var_type=float,
    default_value=0.0,
    unit=None,
    descr="Select the x-ref for aero coefs",
    xpath=DYNAMICSTABILITY_XREF_XPATH,
    gui=INCLUDE_GUI,
    gui_name="X Reference",
    gui_group="Refence Point Setting",
)

cpacs_inout.add_input(
    var_name="dynstab_yref",
    var_type=float,
    default_value=0.0,
    unit=None,
    descr="Select the y-ref for aero coefs",
    xpath=DYNAMICSTABILITY_YREF_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Y Reference",
    gui_group="Refence Point Setting",
)

cpacs_inout.add_input(
    var_name="dynstab_zref",
    var_type=float,
    default_value=0.0,
    unit=None,
    descr="Select the z-ref for aero coefs",
    xpath=DYNAMICSTABILITY_ZREF_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Z Reference",
    gui_group="Refence Point Setting",
)
