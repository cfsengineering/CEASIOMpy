"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for PyAVL.func functions.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# =================================================================================================
#    IMPORTS
# =================================================================================================

from ceasiompy import log
from ceasiompy.utils.commonxpath import CEASIOMPY_XPATH

# =================================================================================================
#    CONSTANTS
# =================================================================================================

# config.py
FORCE_FILES = ["ft", "fn", "fs", "fe", "st", "sb"]

# results.py
AVL_COEFS = {
    "CLtot": (1, "cl"),
    "CDtot": (1, "cd"),
    "CYtot": (1, "cs"),
    "Cltot": (2, "cmd"),
    "Cmtot": (2, "cms"),
    "Cntot": (2, "cml"),
    "Cma": (1, "cms_a"),
    "Clb": (2, "cmd_b"),
    "Cnb": (2, "cml_b"),
}

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
AVL_NB_CPU_XPATH = AVL_XPATH + "NbCPU"

# Geometry settings
AVL_CTRLSURF_ANGLES_XPATH = AVL_XPATH + "/ControlSurfaceAngles"
AVL_FUSELAGE_XPATH = AVL_XPATH + "/IntegrateFuselage"

# Plot settings
AVL_PLOT_XPATH = AVL_XPATH + "/SavePlots"
AVL_PLOTLIFT_XPATH = AVL_XPATH + "/PlotLift"

# Dynamic Stability
AVL_TABLE_XPATH = AVL_XPATH + "/Table"
AVL_CTRLTABLE_XPATH = AVL_XPATH + "/CtrlTable"

# Vortex distribution
AVL_VORTEX_DISTR_XPATH = AVL_XPATH + "/VortexDistribution"
AVL_NCHORDWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nchordwise"
AVL_NSPANWISE_XPATH = AVL_VORTEX_DISTR_XPATH + "/Nspanwise"
AVL_DISTR_XPATH = AVL_VORTEX_DISTR_XPATH + "/Distribution"

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
