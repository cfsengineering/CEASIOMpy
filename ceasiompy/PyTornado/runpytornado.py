"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This is a wrapper module for PyTornado. PyTornado allows to perform aerodynamic
analyses using the vortex-lattice method (VLM). Note that PyTornado is being
developed in a separate repository on Github. For installation guides and
general documentation refer to:

* https://github.com/airinnova/pytornado

Please report any issues with PyTornado or this wrapper here:

* https://github.com/airinnova/pytornado/issues

PyTornado support:

* AeroperformanceMap analyses

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-08-12
| Last modifiction: 2019-08-23
"""

import os
import shutil
from importlib import import_module

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])

# ===== Paths =====
DIR_MODULE = os.path.dirname(os.path.abspath(__file__))
DIR_PYT_WKDIR = os.path.join(DIR_MODULE, 'wkdir')
DIR_PYT_AIRCRAFT = os.path.join(DIR_PYT_WKDIR, 'aircraft')
DIR_PYT_SETTINGS = os.path.join(DIR_PYT_WKDIR, 'settings')
FILE_PYT_AIRCRAFT = os.path.join(DIR_PYT_AIRCRAFT, 'ToolInput.xml')
FILE_PYT_SETTINGS = os.path.join(DIR_PYT_SETTINGS, 'cpacs_run.json')

if __name__ == '__main__':
    log.info("Running PyTornado...")

    try:
        pytornado = import_module('pytornado.stdfun.run')
    except ModuleNotFoundError:
        err_msg = """\n
        | PyTornado was not found. CEASIOMpy cannot run an analysis.
        | Make sure that PyTornado is correctly installed. Please refer to:
        |
        | * https://github.com/airinnova/pytornado
        """
        log.error(err_msg)
        raise ModuleNotFoundError(err_msg)

    # ===== Setup =====
    # check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)
    cpacs_in_path = DIR_MODULE + '/ToolInput/ToolInput.xml'
    cpacs_out_path = DIR_MODULE + '/ToolOutput/ToolOutput.xml'
    shutil.copy(src=cpacs_in_path, dst=FILE_PYT_AIRCRAFT)

    # ===== PyTornado analysis =====
    args = pytornado.StdRunArgs()
    args.run = FILE_PYT_SETTINGS
    pytornado.standard_run(args)

    # ===== Clean up =====
    shutil.copy(src=FILE_PYT_AIRCRAFT, dst=cpacs_out_path)
    log.info("PyTornado analysis completed")
