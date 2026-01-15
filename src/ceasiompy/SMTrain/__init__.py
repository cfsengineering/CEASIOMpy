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
LEVEL_THREE = "Three levels"

# ===== List of potential objectives =====
OBJECTIVES_LIST = ["cl_cd", "cl", "cd", "cs", "cmd", "cml", "cms"]

# ===== List of an aeromap (basic) features =====
AEROMAP_FEATURES = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

# ===== xPaths =====
SMTRAIN_XPATH = CEASIOMPY_XPATH + "/SMTrain"

SMTRAIN_UPLOAD_AVL_DATABASE_XPATH = SMTRAIN_XPATH + "/Upload_avl_db"

# SMTRAIN_XPATH_CORES = SMTRAIN_XPATH + "/NbCPU"

SMTRAIN_XPATH_AEROMAP = SMTRAIN_XPATH + "/Aeromap"
SMTRAIN_XPATH_PARAMS_AEROMAP = SMTRAIN_XPATH_AEROMAP + "/AeroParams"
SMTRAIN_XPATH_AEROMAP_UID = SMTRAIN_XPATH_AEROMAP + "/Aeromap_uID"
SMTRAIN_XPATH_GEOMETRY = SMTRAIN_XPATH + "/Geometry"
SMTRAIN_XPATH_WINGS = SMTRAIN_XPATH_GEOMETRY + "/wings"


# Enriching dataset from previously computed values with AVL
SMTRAIN_AVL_DATABASE_XPATH = SMTRAIN_XPATH + "/AVLDatabase"

# Surrogate model settings
SMTRAIN_SIMULATION_PURPOSE_XPATH = SMTRAIN_XPATH + "/SimulationPurpose"
SMTRAIN_OBJECTIVE_XPATH = SMTRAIN_XPATH + "/Objective"
SMTRAIN_FIDELITY_LEVEL_XPATH = SMTRAIN_XPATH + "/FidelityLevel"
# SMTRAIN_SELECTED_MODEL = SMTRAIN_XPATH + "/selected_model"
SMTRAIN_MODELS = SMTRAIN_XPATH + "/models"
SMTRAIN_KRG_MODEL = SMTRAIN_MODELS + "/KRG"
SMTRAIN_RBF_MODEL = SMTRAIN_MODELS + "/RBF"
SMTRAIN_TRAIN_PERC_XPATH = SMTRAIN_XPATH + "/TrainingPercentage"

# Plot
SMTRAIN_PLOT_XPATH = SMTRAIN_XPATH + "/ValidationPlot"

# Design Of Experiment Aeropmap
SMTRAIN_DOE_AEROMAP = SMTRAIN_XPATH + "/DesignOfExperiment_aeromap"
SMTRAIN_THRESHOLD_XPATH = SMTRAIN_DOE_AEROMAP + "/rmseThreshold"
SMTRAIN_NSAMPLES_AEROMAP_XPATH = SMTRAIN_DOE_AEROMAP + "/nSamples_aeromap"

# Design Of Experiment Geometry
SMTRAIN_DOE_GEOMETRY = SMTRAIN_XPATH + "/DesignOfExperiment_geometry"
SMTRAIN_NSAMPLES_GEOMETRY_XPATH = SMTRAIN_DOE_GEOMETRY + "/nSamples_geometry"

# Aeromap ranges
SMTRAIN_MAX_ALT = SMTRAIN_XPATH_AEROMAP + "/MaxAltitude"
SMTRAIN_MAX_MACH = SMTRAIN_XPATH_AEROMAP + "/MaxMach"
SMTRAIN_MAX_AOA = SMTRAIN_XPATH_AEROMAP + "/MaxAngleOfAttack"
SMTRAIN_MAX_AOS = SMTRAIN_XPATH_AEROMAP + "/MaxAngleOfSideslip"

# Geometry ranges
SMTRAIN_GEOM_WING_OPTIMISE = SMTRAIN_XPATH_GEOMETRY + "/Wings"

SMTRAIN_MAX_SWEEPANGLE = SMTRAIN_XPATH_GEOMETRY + "/MaxSweepAngle"
SMTRAIN_MAX_DIHEDRALANGLE = SMTRAIN_XPATH_GEOMETRY + "/MaxDIhedralAngle"
SMTRAIN_MAX_LENGTH = SMTRAIN_XPATH_GEOMETRY + "/MaxLength"
SMTRAIN_MAX_TWIST = SMTRAIN_XPATH_GEOMETRY + "/MaxTwist"
SMTRAIN_MAX_CHORD = SMTRAIN_XPATH_GEOMETRY + "/MaxChord"
SMTRAIN_MAX_THICKNESS = SMTRAIN_XPATH_GEOMETRY + "/MaxThickness"

WING_PARAMETERS = [
    "sweepAngle",
    "dihedralAngle",
    "length",
    "twist",
    "chord",
    "thickness"
]

AEROMAP_DEFAULTS = {
    "altitude": {
        "min": 50,
        "max": 1000,
    },
    "machNumber": {
        "min": 0.1,
        "max": 0.85,
    },
    "angleOfAttack": {
        "min": -5.0,
        "max": 5.0,
    },
    "angleOfSideslip": {
        "min": -10.0,
        "max": 10.0,
    },
}
