"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SMUse.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.SMUse import include_gui
from ceasiompy.utils.commonxpath import (
    SM_XPATH,
    SMUSE_XPATH,
)
# from ceasiompy.utils.commonxpath import SMTRAIN_XPATH

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
    gui=include_gui,
    gui_name="Model to use",
    gui_group="Model",
)

cpacs_inout.add_input(
    var_name="prediction_dataset",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Aeromap with inputs to be predicted",
    xpath=SMUSE_XPATH + "/predictionDataset",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Predictions Dataset",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
