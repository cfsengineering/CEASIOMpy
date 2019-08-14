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
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])

# PyTornado is an external dependency. Assuming PyTornado is not installed.
PYTORNADO_FOUND = True
try:
    import pytornado.stdfun as pyt
except ModuleNotFoundError:
    # ModuleNotFoundError is new in Python 3.6
    # See https://docs.python.org/3/library/exceptions.html
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

    # check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)

    # ========== PyTornado main analysis ==========
    this_dir = os.path.dirname(os.path.abspath(__file__))
    pyt_wkdir = 'wkdir'
    pyt_aircraft_dir = os.path.join(pyt_wkdir, 'aircraft')

    # Create a working directory
    if not os.path.exists(pyt_wkdir):
        os.makedirs(pyt_wkdir)

    # TODO: initialise PyTornado directory

    # Move CPACS INPUT into working directory
    shutil.copy(src=cpacs_path, dst=pyt_aircraft_dir)

    # Run Pytornado in working directory
    os.chdir(os.path.join(this_dir, pyt_wkdir))

    args = pyt.StdRunArgs()
    args.run = 'std_run'
    pyt.standard_run(args)

    log.info("PyTornado analysis completed")
