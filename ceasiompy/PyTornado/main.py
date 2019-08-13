"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-08-12
| Last modifiction: 2019-08-12
"""

import os

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])

# PyTornado is an external dependency. Assuming PyTornado is not installed.
PYTORNADO_FOUND = True
try:
    import pytornado.stdfun as pyt
except ModuleNotFoundError:
    PYTORNADO_FOUND = False
    log.warning("PyTornado was not found")


if __name__ == '__main__':
    log.info("Running PyTornado...")

    # Abort if PyTornado is not properly installed
    if not PYTORNADO_FOUND:
        err_msg = "PyTornado was not found. Cannot run an analysis."
        log.error(err_msg)
        raise ModuleNotFoundError(err_msg)

    # CEASIOMpy paths
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)

    # ========== PyTornado main analysis ==========

    ##### TEST ##### TEST ##### TEST
    this_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.join(this_dir, "wkdir/"))
    args = pyt.StdRunArgs()
    args.run = 'test_wing'
    pyt.standard_run(args)
    ##### TEST ##### TEST ##### TEST

    log.info("PyTornado analysis completed")
