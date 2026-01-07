"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for PyAVL module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils import get_module_status

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================


# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Name of Software used =====
SOFTWARE_NAME = "avl"

# ===== Module Status =====
MODULE_STATUS = get_module_status(
    default=True,
    needs_soft_name=SOFTWARE_NAME,
)

# =================================================================================================
#    xPaths
# =================================================================================================

# Main branch
AVL_XPATH = CEASIOMPY_XPATH + "/avl"

# AeroMap settings
AVL_AEROMAP_UID_XPATH = AVL_XPATH + "/aeroMapUID"
AVL_ROTRATES_XPATH = AVL_XPATH + "/RotationRates"
AVL_FREESTREAM_MACH_XPATH = AVL_XPATH + "/FreestreamMach"

# Software setting
AVL_NB_CPU_XPATH = AVL_XPATH + "/NbCPU"

# Geometry settings
AVL_CTRLSURF_ANGLES_XPATH = AVL_XPATH + "/ControlSurfaceAngles"
AVL_FUSELAGE_XPATH = AVL_XPATH + "/IntegrateFuselage"

# Plot settings
AVL_PLOT_XPATH = AVL_XPATH + "/SavePlots"

# Dynamic Stability
AVL_TABLE_XPATH = AVL_XPATH + "/Table"
AVL_CTRLTABLE_XPATH = AVL_XPATH + "/CtrlTable"

# Vortex distribution
AVL_VORTEX_DISTR_XPATH = AVL_XPATH + "/VortexDistribution"
AVL_NCHORDWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nchordwise"
AVL_NSPANWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nspanwise"
AVL_DISTR_XPATH = AVL_VORTEX_DISTR_XPATH + "/Distribution"

# Specific for Dynamic Stability computation
AVL_EXPAND_VALUES_XPATH = AVL_XPATH + "/ExpandValues"
