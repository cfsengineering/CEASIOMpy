"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This is a wrapper module for AeroFrame. AeroFrame allows to perform
partitioned aeroelastic analyses. Any CFD and structure model can be used
provided that a corresponding AeroFrame wrapper has been written.

Note that AeroFrame is being developed in a separate repository on Github.
For installation guides and general documentation refer to:

* https://github.com/airinnova/aeroframe

Please report any issues with AeroFrame or this wrapper here:

* https://github.com/airinnova/aeroframe/issues

Python version: >=3.7

| Author: Aaron Dettmann
| Creation: 2019-09-25

"""

# TODO
# - make working directories

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path

import aeroframe.stdfun.run as af
from ceasiompy.utils.ceasiomlogger import get_logger

# from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

DIR_TOOL_INPUT = Path(MODULE_DIR, "ToolInput")
DIR_AEROFRAME_WKDIR = Path(MODULE_DIR, "wkdir")

FILE_SU2_DISP = Path(DIR_TOOL_INPUT, "disp.dat")
FILE_SU2_CONF = Path(DIR_TOOL_INPUT, "ToolInput.cfg")
FILE_SU2_CONF = Path(DIR_TOOL_INPUT, "ToolInput.su2")

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("----- Start of " + MODULE_NAME + " -----")

    af.standard_run(args=af.StdRunArgs(dest=DIR_AEROFRAME_WKDIR, verbose=True))

    log.info("----- End of " + MODULE_NAME + " -----")
