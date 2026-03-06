"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for airfoil2gmsh module.
"""

# Imports

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True
MODULE_TYPE = "Mesher"

DESCRIPTION = """Module to generate 2D unstructured,
hybrid and structured mesh around an airfoil with GMSH.
"""

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# 2D Airfoil mesh parameters
AIRFOIL2GMSH = CEASIOMPY_XPATH + f"/{MODULE_NAME}"
AIRFOIL2GMSH_AIRFOIL_MESH_SIZE_XPATH = AIRFOIL2GMSH + "/airfoilMeshSize"
AIRFOIL2GMSH_EXT_MESH_SIZE_XPATH = AIRFOIL2GMSH + "/externalMeshSize"
AIRFOIL2GMSH_FARFIELD_RADIUS_XPATH = AIRFOIL2GMSH + "/farfieldRadius"
AIRFOIL2GMSH_AOA_XPATH = AIRFOIL2GMSH + "/angleOfAttack"
AIRFOIL2GMSH_FARFIELD_TYPE_XPATH = AIRFOIL2GMSH + "/farfieldType"
AIRFOIL2GMSH_STRUCTURED_MESH_XPATH = AIRFOIL2GMSH + "/structuredMesh"
AIRFOIL2GMSH_FIRST_LAYER_HEIGHT_XPATH = AIRFOIL2GMSH + "/firstLayerHeight"
AIRFOIL2GMSH_HEIGHT_LENGTH_XPATH = AIRFOIL2GMSH + "/heightLength"
AIRFOIL2GMSH_WAKE_LENGTH_XPATH = AIRFOIL2GMSH + "/wakeLength"
AIRFOIL2GMSH_LENGTH_XPATH = AIRFOIL2GMSH + "/length"
AIRFOIL2GMSH_NO_BL_XPATH = AIRFOIL2GMSH + "/noBoundaryLayer"
AIRFOIL2GMSH_RATIO_XPATH = AIRFOIL2GMSH + "/growthRatio"
AIRFOIL2GMSH_NB_LAYERS_XPATH = AIRFOIL2GMSH + "/numberOfLayers"
