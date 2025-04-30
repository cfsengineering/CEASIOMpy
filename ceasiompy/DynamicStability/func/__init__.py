"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for DynamicStability.func.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from typing import List

from ceasiompy import log

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# Initialze SDSA xPaths
ROOT_XPATH = "/root"

# In /root
PILOTEYE_XPATH = ROOT_XPATH + "/GeoMass/PilotEye"
CGRID_XPATH = ROOT_XPATH + "/cGrid"
AERO_XPATH = ROOT_XPATH + "/Aero"

# In /aero
REF_XPATH = AERO_XPATH + "/Ref"
STATUS_XPATH = AERO_XPATH + "/GEffect/Status"
AEROTABLE_XPATH = AERO_XPATH + "/Tables/AeroTable/Table"
CTRLTABLE_XPATH = AERO_XPATH + "/Tables/CtrlTable/Table"
ALPHAMAX_XPATH = AERO_XPATH + "/AlphaMax"

# In /DelCoeff
DELCOEF_XPATH = AERO_XPATH + "/DelCoeff"
FLAPS1_XPATH = DELCOEF_XPATH + "/Flaps1"
FLAPS2_XPATH = DELCOEF_XPATH + "/Flaps2"
AIRBRAKE_XPATH = DELCOEF_XPATH + "/AirBrake"
LANDGEAR_XPATH = DELCOEF_XPATH + "/LandGear"


# List of xpaths for derivatives
XPATHS_PRIM: List = [
    (AERO_XPATH + "/CMAlphaPrim", "cm_alphaprim"),
    (AERO_XPATH + "/CZAlphaPrim", "cz_alphaprim"),
    (AERO_XPATH + "/CXAlphaPrim", "cx_alphaprim"),
    (AERO_XPATH + "/CYBetaPrim", "cy_betaprim"),
    (AERO_XPATH + "/CLBetaPrim", "cl_betaprim"),
    (AERO_XPATH + "/CNBetaPrim", "cn_betaprim"),
]

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
