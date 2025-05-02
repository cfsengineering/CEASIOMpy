"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SU2Run module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy import log
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

# Specific to SU2Run module

# List of control surface scenarios
CONTROL_SURFACE_LIST = ["flap", "rudder", "aileron"]

# Either Euler or Rans simulation
TEMPLATE_TYPE = ["EULER", "RANS"]

# Name of used software
SOFTWARE_NAME = "SU2_CFD"
REQUIRED_VERSION = "8.1.0"

# xPaths
SU2_XPATH = CEASIOMPY_XPATH + "/aerodynamics/su2"
SU2_AEROMAP_UID_XPATH = SU2_XPATH + "/aeroMapUID"
SU2_NB_CPU_XPATH = SU2_XPATH + "/settings/nbCPU"
SU2_EXTRACT_LOAD_XPATH = SU2_XPATH + "/results/extractLoads"
SU2_UPDATE_WETTED_AREA_XPATH = SU2_XPATH + "/results/updateWettedArea"
USED_SU2_MESH_XPATH = SU2_XPATH + "/MeshPath"

SU2_MAX_ITER_XPATH = SU2_XPATH + "/settings/maxIter"
SU2_CFL_NB_XPATH = SU2_XPATH + "/settings/cflNumber/value"
SU2_CFL_ADAPT_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/value"
SU2_CFL_ADAPT_PARAM_DOWN_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/factor_down"
SU2_CFL_ADAPT_PARAM_UP_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/factor_up"
SU2_CFL_MIN_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/min"
SU2_CFL_MAX_XPATH = SU2_XPATH + "/settings/cflNumber/adaptation/max"
SU2_MG_LEVEL_XPATH = SU2_XPATH + "/settings/multigridLevel"

SU2_BC_WALL_XPATH = SU2_XPATH + "/boundaryConditions/wall"
SU2_BC_FARFIELD_XPATH = SU2_XPATH + "/boundaryConditions/farfield"

SU2_FIXED_CL_XPATH = SU2_XPATH + "/fixedCL"
SU2_TARGET_CL_XPATH = SU2_XPATH + "/targetCL"

SU2_DAMPING_DER_XPATH = SU2_XPATH + "/options/calculateDampingDerivatives"
SU2_ROTATION_RATE_XPATH = SU2_XPATH + "/options/rotationRate"

SU2_CONTROL_SURF_XPATH = SU2_XPATH + "/ControlSurfaces"
SU2_CONTROL_SURF_BOOL_XPATH = SU2_CONTROL_SURF_XPATH + "/Bool"
SU2_CONTROL_SURF_ANGLE_XPATH = SU2_CONTROL_SURF_XPATH + "/Angle"
SU2_DEF_MESH_XPATH = SU2_XPATH + "/availableDeformedMesh"

SU2_ACTUATOR_DISK_XPATH = SU2_XPATH + "/options/includeActuatorDisk"
SU2_CONFIG_RANS_XPATH = SU2_XPATH + "/options/config_type"

SU2_DYNAMICDERIVATIVES_XPATH = SU2_XPATH + "/DynamicDerivatives"
SU2_DYNAMICDERIVATIVES_BOOL_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Bool"
SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/TimeSize"
SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Amplitude"
SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/AngularFrequency"
SU2_DYNAMICDERIVATIVES_INNERITER_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/InnerIter"
SU2_DYNAMICDERIVATIVES_DATA_XPATH = SU2_DYNAMICDERIVATIVES_XPATH + "/Data"
SU2_CEASIOMPYDATA_XPATH = SU2_XPATH + "/CeasiompyData"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
