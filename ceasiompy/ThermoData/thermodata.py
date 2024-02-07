"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate outlet conditions fot turbojet and turbofan engines by using the open source code PyCycle
and saving those conditions in a text file

| Author: Giacomo Benedetti and Francesco Marcucci
| Creation: 2023-12-12
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
from pathlib import Path

from ceasiompy.ThermoData.func.run_func import (
    thermo_data_run,
)

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.moduleinterfaces import (
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    CLCALC_XPATH,
    ENGINE_TYPE_XPATH,
)
from ceasiompy.utils.commonnames import (
    ENGINE_BOUNDARY_CONDITIONS,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory


log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    results_dir = get_results_directory("ThermoData")

    thermo_data_run(cpacs_path, cpacs_out_path, results_dir)

    folder_name = "reports"

    shutil.rmtree(folder_name)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
