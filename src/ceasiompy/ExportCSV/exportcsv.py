"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to export Aeromap (or other data?) to CSV

| Author: Aidan Jungo
| Creation: 2021-04-07
| Modified: Leon Deligny
| Date: 03 April 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath
from cpacspy.cpacspy import CPACS
from cpacspy.aeromap import AeroMap

from ceasiompy import log
from ceasiompy.utils.guixpaths import AEROMAP_TO_EXPORT_XPATH

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:

    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, AEROMAP_TO_EXPORT_XPATH)

    if not aeromap_uid_list:
        aeromap_uid_list = cpacs.get_aeromap_uid_list()

    for aeromap_uid in aeromap_uid_list:
        aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
        csv_path = Path(wkdir, f"{aeromap_uid}.csv")
        aeromap.export_csv(csv_path)
        log.info(f"Aeromap {aeromap_uid} has been saved to \n {csv_path}")
