"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This is a wrapper module for AeroFrame. AeroFrame allows to perform
partiotioned aeroelastic analyses. Any CFD and structure model can be used
provided that a corresponding AeroFrame wrapper has been written.

Note that AeroFrame is being developed in a separate repository on Github.
For installation guides and general documentation refer to:

* https://github.com/airinnova/aeroframe

Please report any issues with AeroFrame or this wrapper here:

* https://github.com/airinnova/aeroframe/issues

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-09-25
| Last modification: 2019-09-25
"""

import os

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

log = get_logger(__file__.split('.')[0])


if __name__ == '__main__':
    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    check_cpacs_input_requirements(cpacs_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
