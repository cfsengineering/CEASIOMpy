"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main scripts for Database module.

| Author: Leon Deligny
| Creation: 03-Mar-2025

"""

# Imports

from cpacspy.cpacsfunctions import get_value
from ceasiompy.database.func.storing import store_data

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.database import DATABASE_STOREDATA_XPATH

# Main


def main(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    # Check if we store data
    if get_value(tixi, DATABASE_STOREDATA_XPATH):
        store_data(tixi)
    else:
        log.info("Did not call database.")
