from pathlib import Path
import streamlit as st
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import SMUSE_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = False

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "SurrogateModels")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name="model_file",
    var_type="pathtype",
    default_value="-",
    descr="File that contains a trained model",
    xpath=SMUSE_XPATH + "/modelFile",
    gui=include_gui,
    gui_name="Model to use",
    gui_group="Prediction options",
)

cpacs_inout.add_input(
    var_name="Aeromap only",
    var_type=bool,
    default_value="False",
    unit=None,
    descr="""Indicate wether or not the parameters are all contained in an aeromap, in which case
    the workflow only has to be run once.""",
    xpath=SMUSE_XPATH + "/AeroMapOnly",
    gui=include_gui,
    gui_name="Aeromap only",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    descr="To which aeroMap the model shall take andn write the entries",
    xpath=SMUSE_XPATH + "/aeroMapUID",
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

# ----- Output -----

# cpacs_inout.add_output(
#     var_name='output',
#     default_value='-',
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
