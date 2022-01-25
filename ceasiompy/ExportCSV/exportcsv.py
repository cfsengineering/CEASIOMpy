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

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path

import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.utils.xpath import CEASIOMPY_XPATH

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_string_vector

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_NAME = os.path.basename(os.getcwd())


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def export_aeromaps(cpacs_path, cpacs_out_path):

    cpacs = CPACS(cpacs_path)

    aeromap_to_export_xpath = CEASIOMPY_XPATH + "/export/aeroMapToExport"

    aeromap_uid_list = []
    aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_export_xpath)

    results_dir = Path(Path.cwd(), "Results", "ExportCSV")

    if not results_dir.exists():
        results_dir.mkdir(parents=True)

    for aeromap_uid in aeromap_uid_list:
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        csv_path = Path(results_dir, f"{aeromap_uid}.csv")
        aeromap.export_csv(csv_path)

        log.info(f"Aeromap(s) has been saved to {csv_path}")

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


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
