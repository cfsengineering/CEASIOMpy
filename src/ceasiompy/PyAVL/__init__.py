"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for PyAVL module.
"""

# Imports
import streamlit as st

from ceasiompy.utils import get_module_status

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
MODULE_TYPE = "Solver"

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
AVL_ROTRATES_XPATH = AVL_XPATH + "/RotationRates"
AVL_FREESTREAM_MACH_XPATH = AVL_XPATH + "/FreestreamMach"

# Geometry settings
AVL_CTRLSURF_ANGLES_XPATH = AVL_XPATH + "/ControlSurfaceAngles"
AVL_FUSELAGE_XPATH = AVL_XPATH + "/IntegrateFuselage"

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

# === Constants ===

AVL_TABLE_FILES: set[str] = {
    "fe.txt",
    "fn.txt",
    "fs.txt",
    "ft.txt",
    "sb.txt",
    "st.txt",
}
