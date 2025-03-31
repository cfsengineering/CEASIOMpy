"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

File to store the common names of files used in CEASIOMpy.

Python version: >=3.8

| Author: Aidan jungo
| Creation: 2022-05-13
| Modified: Leon Deligny
| Date: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy import log

# =================================================================================================
#   CSTS
# =================================================================================================

# CEASIOMpy Colors
CEASIOMPY_BLACK = "#000000"
CEASIOMPY_BLUE = "#278AB0"
CEASIOMPY_GREEN = "1DC690"
CEASIOMPY_ORANGE = "#FF7F2A"
CEASIOMPY_VIOLET = "#A245A2"
CEASIOMPY_BEIGE = "#E0E0D4"

# GMSH
GMSH_ENGINE_CONFIG_NAME = "config_engines.cfg"

# SU2
CONFIG_CFD_NAME = "ConfigCFD.cfg"
CONFIG_DYNSTAB_NAME = "ConfigDYNSTAB.cfg"

SU2_FORCES_BREAKDOWN_NAME = "forces_breakdown.dat"
SU2_DYNSTAB_FORCES_BREAKDOWN_NAME = "forces_breakdown_00000.dat"
SURFACE_FLOW_FILE_NAME = "surface_flow.vtu"
SURFACE_FLOW_FORCE_FILE_NAME = "surface_flow_forces.vtu"
FORCE_FILE_NAME = "forces.csv"

ENGINE_INTAKE_SUFFIX = "_In"
ENGINE_EXHAUST_SUFFIX = "_Ex"

ACTUATOR_DISK_FILE_NAME = "ActuatorDisk.dat"
ACTUATOR_DISK_INLET_SUFFIX = "_AD_Inlet"
ACTUATOR_DISK_OUTLET_SUFFIX = "_AD_Outlet"

# WEIGHT & BALANCE
MTOM_FIGURE_NAME = "MTOM_Prediction.png"

# PYCYCLE
ENGINE_BOUNDARY_CONDITIONS = "EngineBC.dat"

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
