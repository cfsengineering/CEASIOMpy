"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

<<<<<<< HEAD
Initialization for CPACSCreator module.
=======
Initialization for CLCalculator module.
>>>>>>> general_updates

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

<<<<<<< HEAD
=======
from ceasiompy.utils.commonxpaths import (
    CLCALC_XPATH,
    MASSBREAKDOWN_XPATH,
)

>>>>>>> general_updates
# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

<<<<<<< HEAD
# ===== Add a Results Directory =====
RES_DIR = True

=======
>>>>>>> general_updates
# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

<<<<<<< HEAD
# ===== CPACSCreator names =====
CPACSCREATOR_NAMES_LIST = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]
=======
# ===== Add a Results Directory =====
RES_DIR = True

# ===== Air heat capacity ratio [-] =====
GAMMA = 1.401

# ===== Mass types =====
MASS_TYPES = ["mTOM", "mZFM", "Custom", r"%% fuel mass"]

# ===== xPaths =====

CLCALC_MASS_TYPE_XPATH = CLCALC_XPATH + "/massType"
CLCALC_CRUISE_ALT_XPATH = CLCALC_XPATH + "/cruiseAltitude"
CLCALC_CRUISE_MACH_XPATH = CLCALC_XPATH + "/cruiseMach"
CLCALC_LOAD_FACT_XPATH = CLCALC_XPATH + "/loadFactor"

MTOM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass"
MZFM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass"

CLCALC_PERC_FUEL_MASS_XPATH = CLCALC_XPATH + "/percentFuelMass"
CLCALC_CUSTOM_MASS_XPATH = CLCALC_XPATH + "/customMass"
>>>>>>> general_updates
