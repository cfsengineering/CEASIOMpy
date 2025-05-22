"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for AeroFrame new module.
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

# ===== xPaths =====

# FramAT
FRAMAT_XPATH = CEASIOMPY_XPATH + "/structure/FramAT"
FRAMAT_MATERIAL_XPATH = FRAMAT_XPATH + "/MaterialProperties"
FRAMAT_SECTION_XPATH = FRAMAT_XPATH + "/SectionProperties"
FRAMAT_MESH_XPATH = FRAMAT_XPATH + "/BeamMesh"
FRAMAT_RESULTS_XPATH = FRAMAT_XPATH + "/Results"

# AeroFrame
AEROFRAME_XPATH = CEASIOMPY_XPATH + "/aeroelasticity/AeroFrame"
AEROFRAME_SETTINGS = AEROFRAME_XPATH + "/Settings"
