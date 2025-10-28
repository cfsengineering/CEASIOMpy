"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SMUse.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.geometry import get_geometry_aeromaps_uid

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.utils.guixpaths import SM_XPATH
from ceasiompy.SMUse import (
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
    default_value=get_geometry_aeromaps_uid(),
    unit=None,
    # TODO: Write now can only do first aeromap
    descr=(
        "Datasets on which to make the predictions, " "First aeromap: First level of fidelity."
    ),
    xpath=SMUSE_DATASET_XPATH,

    gui_name="__AEROMAP_SELECTION",
    gui_group="Selected Aeromap",
)
