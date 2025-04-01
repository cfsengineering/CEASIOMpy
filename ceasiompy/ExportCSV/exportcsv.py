"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to export Aeromap (or other data?) to CSV

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2021-04-07

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from cpacspy.cpacsfunctions import get_value_or_default

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    get_aeromap_list_from_xpath,
)

from cpacspy.aeromap import AeroMap
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpath import AEROMAP_TO_EXPORT_XPATH

from ceasiompy.ExportCSV import MODULE_NAME

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    tixi = cpacs.tixi

    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, AEROMAP_TO_EXPORT_XPATH)

    if not aeromap_uid_list:
        aeromap_uid_list = get_value_or_default(
            tixi, AEROMAP_TO_EXPORT_XPATH, "DefaultAeromap"
        )

    for aeromap_uid in aeromap_uid_list:
        aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
        csv_path = Path(wkdir, f"{aeromap_uid}.csv")
        aeromap.export_csv(csv_path)

        log.info(f"Aeromap(s) has been saved to {csv_path}")


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
