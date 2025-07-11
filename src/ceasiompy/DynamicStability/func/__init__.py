"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for DynamicStability.func.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

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

AEROTABLE_XPATH = AERO_XPATH + "/Tables/AeroTable"
CTRLTABLE_XPATH = AERO_XPATH + "/Tables/CtrlTable"

TABLE_AEROTABLE_XPATH = AEROTABLE_XPATH + "/Table"
TABLE_CTRLTABLE_XPATH = CTRLTABLE_XPATH + "/Table"

ALPHAMAX_XPATH = AERO_XPATH + "/AlphaMax"

# In /DelCoeff
DELCOEF_XPATH = AERO_XPATH + "/DelCoeff"
FLAPS1_XPATH = DELCOEF_XPATH + "/Flaps1"
FLAPS2_XPATH = DELCOEF_XPATH + "/Flaps2"
AIRBRAKE_XPATH = DELCOEF_XPATH + "/AirBrake"
LANDGEAR_XPATH = DELCOEF_XPATH + "/LandGear"


# List of xpaths for derivatives
ALPHA_PRIM_XPATHS: list[tuple[str, str]] = [
    (AERO_XPATH + "/CMAlphaPrim", "cm_alphaprim"),
    (AERO_XPATH + "/CZAlphaPrim", "cz_alphaprim"),
    (AERO_XPATH + "/CXAlphaPrim", "cx_alphaprim"),
]

BETA_PRIM_XPATHS: list[tuple[str, str]] = [
    (AERO_XPATH + "/CYBetaPrim", "cy_betaprim"),
    (AERO_XPATH + "/CLBetaPrim", "cl_betaprim"),
    (AERO_XPATH + "/CNBetaPrim", "cn_betaprim"),
]

# CSV file names to save
ALPHA_CSV_NAME: str = 'alpha_dot_derivatives.csv'
BETA_CSV_NAME: str = 'beta_dot_derivatives.csv'
