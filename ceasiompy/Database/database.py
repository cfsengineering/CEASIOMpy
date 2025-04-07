"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main scripts for Database module.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 03-Mar-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import bool_
from ceasiompy.Database.func.storing import store_data

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpath import DATABASE_STOREDATA_XPATH

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    # Check if we store data
    if bool_(get_value(tixi, DATABASE_STOREDATA_XPATH)):
        store_data(tixi)
    else:
        log.info("Did not call database.")


if __name__ == "__main__":
    # If you want to test your new functions
    # or classes go in the tests folder of this module.
    # You will add data to ceasiompy.db if you run this module.
    log.info("Nothing to execute.")
