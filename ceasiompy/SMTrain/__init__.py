"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Level Notations =====
LEVEL_ONE = "One level"
LEVEL_TWO = "Two levels"
w = "Three levels"

# ===== List of potential objectives =====
OBJECTIVES_LIST = ["cl", "cd", "cs", "cmd", "cml", "cms"]

# ===== List of an aeromap (basic) features =====
AEROMAP_FEATURES = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

# ===== xPaths =====
SMTRAIN_XPATH = CEASIOMPY_XPATH + "/SMTrain"

# Enriching dataset from previously computed values with AVL
SMTRAIN_AVL_DATABASE_XPATH = SMTRAIN_XPATH + "/AVLDatabase"

# Mesh for SU2 enriching data
SMTRAIN_USED_SU2_MESH_XPATH = SMTRAIN_XPATH + "/Usedsu2mesh"

# Surrogate model settings
SMTRAIN_OBJECTIVE_XPATH = SMTRAIN_XPATH + "/Objective"
SMTRAIN_FIDELITY_LEVEL_XPATH = SMTRAIN_XPATH + "/FidelityLevel"
SMTRAIN_TRAIN_PERC_XPATH = SMTRAIN_XPATH + "/TrainingPercentage"

# Plot
SMTRAIN_PLOT_XPATH = SMTRAIN_XPATH + "/ValidationPlot"

# Design Of Experiment
SMTRAIN_DOE = SMTRAIN_XPATH + "/DesignOfExperiment"
# SMTRAIN_NEWDOE = SMTRAIN_DOE + "/NewDoe"
SMTRAIN_THRESHOLD_XPATH = SMTRAIN_DOE + "/rmseThreshold"
SMTRAIN_NSAMPLES_XPATH = SMTRAIN_DOE + "/nSamples"

# Range
SMTRAIN_MAX_ALT = SMTRAIN_XPATH + "/MaxAltitude"
SMTRAIN_MAX_MACH = SMTRAIN_XPATH + "/MaxMach"
SMTRAIN_MAX_AOA = SMTRAIN_XPATH + "/MaxAngleOfAttack"
SMTRAIN_MAX_AOS = SMTRAIN_XPATH + "/MaxAngleOfSideslip"

# SMTRAIN_NEW_DATASET = SMTRAIN_XPATH + "/NewDataset"
# SMTRAIN_NEWDATASET_FRAC_XPATH = SMTRAIN_XPATH + "/NewDatasetFraction"

SMTRAIN_TRAINING_AEROMAP_XPATH = SMTRAIN_XPATH + "/AeromapForTraining"
