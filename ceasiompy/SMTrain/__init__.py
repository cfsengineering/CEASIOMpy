"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy import log
from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
module_status = True

# ===== Include GUI =====
include_gui = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Level Notations =====
LEVEL_ONE = "One Level"
LEVEL_TWO = "Two levels"

# ===== List of potential objectives =====
OBJECTIVES_LIST = ["cl", "cd", "cs", "cmd", "cml", "cms"]

# xPaths
SMTRAIN_XPATH = CEASIOMPY_XPATH + "/SMTrain"

SMTRAIN_OBJECTIVE_XPATH = SMTRAIN_XPATH + "/Objective"

SMTRAIN_AEROMAP_DOE_XPATH = SMTRAIN_XPATH + "/aeromapForDoe"

SMTRAIN_DOE = SMTRAIN_XPATH + "/DesignOfExperiment"
SMTRAIN_NEWDOE = SMTRAIN_DOE + "/NewDoe"
SMTRAIN_THRESHOLD_XPATH = SMTRAIN_DOE + "/rmseThreshold"
SMTRAIN_AVL_OR_SU2_XPATH = SMTRAIN_DOE + "/useAVLorSU2"

SMTRAIN_NSAMPLES_XPATH = SMTRAIN_DOE + "/nSamples"

SMTRAIN_SM_XPATH = SMTRAIN_XPATH + "/SurrogateModelPath"
SMTRAIN_FIDELITY_LEVEL_XPATH = SMTRAIN_XPATH + "/FidelityLevel"
SMTRAIN_TRAIN_PERC_XPATH = SMTRAIN_XPATH + "/TrainingPercentage"
SMTRAIN_PLOT_XPATH = SMTRAIN_XPATH + "/ValidationPlot"
SMTRAIN_NEW_DATASET = SMTRAIN_XPATH + "/NewDataset"

SMTRAIN_AEROMAP_FOR_TRAINING_XPATH = SMTRAIN_XPATH + "/AeromapForTraining"
SMTRAIN_NEWDATASET_FRAC_XPATH = SMTRAIN_XPATH + "/NewDatasetFraction"

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
