<<<<<<< HEAD
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACSUpdater.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 14-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.geometryfunctions import get_segments

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.utils.commonxpath import (
    CPACSUPDATER_CTRLSURF_XPATH,
    CPACSUPDATER_ADD_CTRLSURFACES_XPATH,
)

from ceasiompy import log
from ceasiompy.CPACSUpdater import include_gui
from ceasiompy.CPACSUpdater import *

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   CALL
# ==============================================================================

# ----- Input -----
cpacs_inout.add_input(
    var_name='add_control_surfaces',
    var_type=bool,
    default_value=True,
    unit=None,
    descr='Adds control surfaces',
    xpath=CPACSUPDATER_ADD_CTRLSURFACES_XPATH,
    gui=include_gui,
    gui_name='Add Control Surfaces',
    gui_group='Control Surfaces Settings',
)

if "cpacs" in st.session_state:
    segments_list = get_segments(st.session_state.cpacs.tixi)

    for (wing_name, segment_name) in segments_list:
        cpacs_inout.add_input(
            var_name=f"control_surface_{wing_name}_{segment_name}",
            var_type=list,
            default_value=CONTROL_SURFACES_LIST,
            unit=None,
            descr=f"Type of control surface to add at specific wing and segment of wing.",
            xpath=CPACSUPDATER_CTRLSURF_XPATH + f"/{wing_name}/{segment_name}",
            gui=include_gui,
            gui_name=f"Control Surface for segment {segment_name} of wing {wing_name}",
            gui_group='Control Surfaces Settings',
        )

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
=======
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = False

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----

# TODO

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
# for direction in ['x', 'y', 'z']:
#     cpacs_inout.add_input(
#         var_name=direction,
#         var_type=float,
#         default_value=None,
#         unit='1',
#         descr=f"Fuselage scaling on {direction} axis",
#         xpath=AIRCRAFT_XPATH + f'/model/fuselages/fuselage/transformation/scaling/{direction}',
#         gui=include_gui,
#         gui_name=f'{direction.capitalize()} scaling',
#         gui_group='Fuselage scaling',
#     )
#
# cpacs_inout.add_input(
#     var_name='test',
#     var_type=str,
#     default_value='This is a test',
#     unit=None,
#     descr='This is a test of description',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myTest',
#     gui=include_gui,
#     gui_name='My test',
#     gui_group='Group Test',
# )
#
# cpacs_inout.add_input(
#     var_name='aeromap_uid',
#     var_type=list,
#     default_value=None,
#     xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/aeroMapUID',
#     gui=include_gui,
#     gui_name='__AEROMAP_SELECTION',
# )
#
# cpacs_inout.add_input(
#     var_name='aeromap_uid',
#     var_type=list,
#     default_value=None,
#     xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate',
#     gui=include_gui,
#     gui_name='__AEROMAP_CHECKBOX',
# )
#
# cpacs_inout.add_input(
#     var_name='other_var',
#     var_type=list,
#     default_value= [2,33,444],
#     unit='[unit]',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myList',
#     gui=include_gui,
#     gui_name='Choice',
#     gui_group='My Selection'
# )
#
# # ----- Output -----
#
# cpacs_inout.add_output(
#     var_name='output',
#     default_value=None,
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
>>>>>>> origin/main
