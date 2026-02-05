"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACS2Gmsh module.
"""

# Imports

from ceasiompy.utils import get_module_status

from pathlib import Path

from ceasiompy.utils.commonxpaths import MESH_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

SOFTWARE_NAME = "Pentagrow"

HAS_PENTAGROW = get_module_status(
    default=True,
    needs_soft_name=SOFTWARE_NAME,
)

# ===== Module Status =====
MODULE_STATUS = True
MODULE_TYPE = "Mesher"

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# Specific to CPACS2Gmsh module
CONTROL_SURFACES_LIST = ["aileron", "rudder", "flap"]

# xPaths
GMSH_XPATH = MESH_XPATH + "/gmshOptions"
GMSH_OPEN_GUI_XPATH = GMSH_XPATH + "/open_gui"
GMSH_SYMMETRY_XPATH = GMSH_XPATH + "/symmetry"
GMSH_EXPORT_PROP_XPATH = GMSH_XPATH + "/exportPropellers"
GMSH_FARFIELD_FACTOR_XPATH = GMSH_XPATH + "/farfield_factor"
GMSH_N_POWER_FACTOR_XPATH = GMSH_XPATH + "/n_power_factor"
GMSH_N_POWER_FIELD_XPATH = GMSH_XPATH + "/n_power_field"
GMSH_MESH_TYPE_XPATH = GMSH_XPATH + "/type_mesh"
GMSH_MESH_SIZE_FARFIELD_XPATH = GMSH_XPATH + "/mesh_size/farfield"
GMSH_MESH_SIZE_FUSELAGE_XPATH = GMSH_XPATH + "/mesh_size/fuselage/value"
GMSH_MESH_SIZE_FUSELAGE_XPATH = GMSH_XPATH + "/mesh_size/fuselage/factor"
GMSH_MESH_SIZE_WINGS_XPATH = GMSH_XPATH + "/mesh_size/wings/value"
GMSH_MESH_SIZE_CTRLSURFS_XPATH = GMSH_XPATH + "/mesh_size/controlsurfaces/value"
GMSH_MESH_SIZE_FACTOR_WINGS_XPATH = GMSH_XPATH + "/mesh_size/wings/factor"
GMSH_MESH_SIZE_ENGINES_XPATH = GMSH_XPATH + "/mesh_size/engines"
GMSH_MESH_SIZE_PROPELLERS_XPATH = GMSH_XPATH + "/mesh_size/propellers"
GMSH_REFINE_FACTOR_XPATH = GMSH_XPATH + "/refine_factor"
GMSH_REFINE_TRUNCATED_XPATH = GMSH_XPATH + "/refine_truncated"
GMSH_AUTO_REFINE_XPATH = GMSH_XPATH + "/auto_refine"
GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH = GMSH_XPATH + "/refine_factor_angled_lines"
GMSH_INTAKE_PERCENT_XPATH = GMSH_XPATH + "/intake_percent"
GMSH_EXHAUST_PERCENT_XPATH = GMSH_XPATH + "/exhaust_percent"
GMSH_MESH_FORMAT_XPATH = GMSH_XPATH + "/type_output_penta"
GMSH_NUMBER_LAYER_XPATH = GMSH_XPATH + "/number_layer"
GMSH_H_FIRST_LAYER_XPATH = GMSH_XPATH + "/height_first_layer"
GMSH_MAX_THICKNESS_LAYER_XPATH = GMSH_XPATH + "/max_thickness_layer"
GMSH_GROWTH_FACTOR_XPATH = GMSH_XPATH + "/growth_factor"
GMSH_GROWTH_RATIO_XPATH = GMSH_XPATH + "/growth_ratio"
GMSH_FEATURE_ANGLE_XPATH = GMSH_XPATH + "/feature_angle"
GMSH_CTRLSURF_ANGLE_XPATH = GMSH_XPATH + "/DeflectionAngle"
GMSH_SAVE_CGNS_XPATH = GMSH_XPATH + "/SaveCGNS"
GMSH_MESH_CHECKER_XPATH = GMSH_XPATH + "/MeshChecker"

# 2D Airfoil mesh parameters
GMSH_2D_AIRFOIL_MESH_SIZE_XPATH = GMSH_XPATH + "/airfoil2D/airfoilMeshSize"
GMSH_2D_EXT_MESH_SIZE_XPATH = GMSH_XPATH + "/airfoil2D/externalMeshSize"
GMSH_2D_FARFIELD_RADIUS_XPATH = GMSH_XPATH + "/airfoil2D/farfieldRadius"
GMSH_2D_AOA_XPATH = GMSH_XPATH + "/airfoil2D/angleOfAttack"
GMSH_2D_FARFIELD_TYPE_XPATH = GMSH_XPATH + "/airfoil2D/farfieldType"
GMSH_2D_STRUCTURED_MESH_XPATH = GMSH_XPATH + "/airfoil2D/structuredMesh"
GMSH_2D_FIRST_LAYER_HEIGHT_XPATH = GMSH_XPATH + "/airfoil2D/firstLayerHeight"
GMSH_2D_HEIGHT_LENGTH_XPATH = GMSH_XPATH + "/airfoil2D/heightLength"
GMSH_2D_WAKE_LENGTH_XPATH = GMSH_XPATH + "/airfoil2D/wakeLength"
GMSH_2D_LENGTH_XPATH = GMSH_XPATH + "/airfoil2D/length"
GMSH_2D_NO_BL_XPATH = GMSH_XPATH + "/airfoil2D/noBoundaryLayer"
GMSH_2D_RATIO_XPATH = GMSH_XPATH + "/airfoil2D/growthRatio"
GMSH_2D_NB_LAYERS_XPATH = GMSH_XPATH + "/airfoil2D/numberOfLayers"
GMSH_2D_MESH_FORMAT_XPATH = GMSH_XPATH + "/airfoil2D/meshFormat"
