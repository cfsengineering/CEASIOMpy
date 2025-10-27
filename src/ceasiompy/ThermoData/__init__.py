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
from ceasiompy.utils.ceasiompymodules import CEASIOMpyModule

from ceasiompy.utils.guixpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

thermodata = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=True,
)

# xpaths
THERMODATA_XPATH = CEASIOMPY_XPATH + "/ThermoData"
THERMODATA_BC_XPATH = THERMODATA_XPATH + "/BC"
THERMODATA_TEMPERATUREOUTLET_XPATH = THERMODATA_XPATH + "/TemperatureOutlet"
THERMODATA_PRESSUREOUTLET_XPATH = THERMODATA_XPATH + "/PressureOutlet"
