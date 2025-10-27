"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for AeroFrame new module.
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

# ===== Name of Software used =====
SOFTWARE_NAME = "avl"

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

aeroframe = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=True,
)

# ===== xPaths =====

# FramAT
FRAMAT_XPATH = CEASIOMPY_XPATH + "/structure/FramAT"
FRAMAT_MATERIAL_XPATH = FRAMAT_XPATH + "/MaterialProperties"
FRAMAT_SECTION_XPATH = FRAMAT_XPATH + "/SectionProperties"
FRAMAT_MESH_XPATH = FRAMAT_XPATH + "/BeamMesh"
FRAMAT_RESULTS_XPATH = FRAMAT_XPATH + "/Results"

FRAMAT_TIP_DEFLECTION_XPATH = FRAMAT_RESULTS_XPATH + "/TipDeflection"

FRAMAT_YOUNGMODULUS_XPATH = FRAMAT_MATERIAL_XPATH + "/YoungModulus"
FRAMAT_SHEARMODULUS_XPATH = FRAMAT_MATERIAL_XPATH + "/ShearModulus"

FRAMAT_NB_NODES_XPATH = FRAMAT_MESH_XPATH + "/NumberNodes"

FRAMAT_DENSITY_XPATH = FRAMAT_MATERIAL_XPATH + "/Density"

FRAMAT_AREA_XPATH = FRAMAT_SECTION_XPATH + "/Area"

FRAMAT_IX_XPATH = FRAMAT_SECTION_XPATH + "/Ix"
FRAMAT_IY_XPATH = FRAMAT_SECTION_XPATH + "/Iy"

FRAMAT_NB_CPU_XPATH = FRAMAT_XPATH + "/NbCPU"

# AeroFrame
AEROFRAME_XPATH = CEASIOMPY_XPATH + "/aeroelasticity/AeroFrame"
AEROFRAME_SETTINGS = AEROFRAME_XPATH + "/Settings"

AEROFRAME_TOLERANCE_XPATH = AEROFRAME_SETTINGS + "/Tolerance"
AEROFRAME_MAXNB_ITERATIONS_XPATH = AEROFRAME_SETTINGS + "/MaxNumberIterations"
