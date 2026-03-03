"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of DynamicStability.

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# Imports

import streamlit as st

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.pyavl import SOFTWARE_NAME as AVL_SOFTWARE
from ceasiompy.su2run import SOFTWARE_NAME as SU2_SOFTWARE
from ceasiompy.dynamicstability import (
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
    DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH,
    DYNAMICSTABILITY_BETA_DERIVATIVES_XPATH,
)

# Variable

cpacs_inout = CPACSInOut()

cpacs_inout.add_input(
    var_name="alpha_alpha_dot_derivatives",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Compute Alpha, Alpha-dot derivatives",
    xpath=DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH,
    gui=True,
    gui_name="Alpha, Alpha-dot derivatives",
    gui_group="Dot Derivatives Type",
)

cpacs_inout.add_input(
    var_name="beta_beta_dot_derivatives",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Compute Beta, Beta-dot derivatives",
    xpath=DYNAMICSTABILITY_BETA_DERIVATIVES_XPATH,
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
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
    gui=True,
    gui_name="Z Reference",
    gui_group="Refence Point Setting",
)
