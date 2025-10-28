"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for ThermoData module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.guixpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True


# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# xpaths
THERMODATA_XPATH = CEASIOMPY_XPATH + "/ThermoData"
THERMODATA_TEMPERATUREOUTLET_XPATH = THERMODATA_XPATH + "/TemperatureOutlet"
THERMODATA_PRESSUREOUTLET_XPATH = THERMODATA_XPATH + "/PressureOutlet"
