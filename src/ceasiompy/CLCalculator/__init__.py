"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CLCalculator module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.commonxpaths import (
    CLCALC_XPATH,
    MASSBREAKDOWN_XPATH,
)

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Air heat capacity ratio [-] =====

GAMMA = 1.401

# ===== xPaths =====

CLCALC_MASS_TYPE_XPATH = CLCALC_XPATH + "/massType"
CLCALC_CRUISE_ALT_XPATH = CLCALC_XPATH + "/cruiseAltitude"
CLCALC_CRUISE_MACH_XPATH = CLCALC_XPATH + "/cruiseMach"
CLCALC_LOAD_FACT_XPATH = CLCALC_XPATH + "/loadFactor"

MTOM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass"
MZFM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass"

CLCALC_PERC_FUEL_MASS_XPATH = CLCALC_XPATH + "/percentFuelMass"
CLCALC_XPATH_CUSTOM_MASS_XPATH = CLCALC_XPATH + "/customMass"
