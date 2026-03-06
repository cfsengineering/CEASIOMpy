"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SU2Run module.
"""

# Imports

from ceasiompy.utils import get_module_status

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

DESCRIPTION = """Create a full wing from a 2D airfoil.
"""

# Name of used software
SOFTWARE_NAME = "SU2_CFD"
REQUIRED_VERSION = "8.1.0"

# ===== Module Status =====
MODULE_STATUS = get_module_status(
    default=True,
    needs_soft_name=SOFTWARE_NAME,
)

MODULE_TYPE = "Geometry"

# xPaths
TO_THREED_XPATH = CEASIOMPY_XPATH + "/to3d"

# First Section Geometry

# Size
TO_THREED_SPAN_XPATH = TO_THREED_XPATH + "/span"
TO_THREED_CHORD_XPATH = TO_THREED_XPATH + "/chord"

# Angles
TO_THREED_TWIST_XPATH = TO_THREED_XPATH + "/twist"
TO_THREED_SWEEP_XPATH = TO_THREED_XPATH + "/sweep"
TO_THREED_DIHEDRAL_XPATH = TO_THREED_XPATH + "/dihedral"
