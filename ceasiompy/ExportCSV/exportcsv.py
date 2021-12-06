"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to export Aeromap (or other data?) to CSV

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2021-04-07
| Last modifiction: 2021-10-20

TODO:

    * export of other data...
    *

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.moduleinterfaces as mi

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_string_vector

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def export_aeromaps(cpacs_path, cpacs_out_path):

    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    wkdir = ceaf.get_wkdir_or_create_new(tixi)

    aeromap_to_export_xpath = "/cpacs/toolspecific/CEASIOMpy/export/aeroMapToExport"

    aeromap_uid_list = []
    aeromap_uid_list = get_string_vector(tixi, aeromap_to_export_xpath)

    for aeromap_uid in aeromap_uid_list:

        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        csv_dir_path = os.path.join(wkdir, "CSVresults")
        if not os.path.isdir(csv_dir_path):
            os.mkdir(csv_dir_path)

        csv_path = os.path.join(csv_dir_path, aeromap_uid + ".csv")

        aeromap.export_csv(csv_path)

    tixi.save(cpacs_out_path)


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":

    log.info("----- Start of " + MODULE_NAME + " -----")

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # Call the function which check if imputs are well define
    mi.check_cpacs_input_requirements(cpacs_path)

    export_aeromaps(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")
