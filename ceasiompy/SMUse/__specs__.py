"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SMUse.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.utils.commonxpaths import SM_XPATH
from ceasiompy.SMUse import (
    INCLUDE_GUI,
    SMUSE_DATASET_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="model_file",
    var_type="pathtype",
    default_value="-",
    descr="File that contains a trained model",
    xpath=SM_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Model to use",
    gui_group="Model",
    # Temporary work around
    test_value=(
        "/home/runner/work/CEASIOMpy/CEASIOMpy/WKDIR/Workflow_004"
        "/Results/SMTrain/surrogateModel_cl.pkl"
    ),
    expanded=False,
)

cpacs_inout.add_input(
    var_name="prediction_dataset",
    var_type=list,
    default_value=None,
    unit=None,
    descr=(
        "Datasets on which to make the predictions, "
        "First aeromap: First level of fidelity. "
        "Second aeromap: Second level of fidelity. "
        "Third aeromap: Second level of fidelity. ",
    ),
    xpath=SMUSE_DATASET_XPATH,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Selected Aeromap",
    test_value=["test_apm"],
)
