"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to export Aeromap (or other data?) to CSV

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2021-04-07

TODO:

    * export other data...
    *

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

from ceasiompy.utils.ceasiompyfunctions import get_wkdir_or_create_new
import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.utils.xpath import CEASIOMPY_XPATH

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_string_vector

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def export_aeromaps(cpacs_path, cpacs_out_path, csv_dir_path=None):

    cpacs = CPACS(cpacs_path)
    wkdir = get_wkdir_or_create_new(cpacs.tixi)

    aeromap_to_export_xpath = CEASIOMPY_XPATH + "/export/aeroMapToExport"

    aeromap_uid_list = []
    aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_export_xpath)

    for aeromap_uid in aeromap_uid_list:
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        if not csv_dir_path:
            csv_dir_path = os.path.join(wkdir, "CSVresults")

        if not os.path.isdir(csv_dir_path):
            os.mkdir(csv_dir_path)

        csv_path = os.path.join(csv_dir_path, aeromap_uid + ".csv")
        aeromap.export_csv(csv_path)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# ==============================================================================
#    MAIN
# ==============================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    # Call the function which check if imputs are well define
    mi.check_cpacs_input_requirements(cpacs_path)

    export_aeromaps(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
