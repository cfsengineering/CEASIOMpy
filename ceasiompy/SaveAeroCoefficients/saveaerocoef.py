"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS v3 aeroMaps

Python version: >=3.8

| Author: Aidan jungo
| Creation: 2019-08-19

TODO:
    * add plot vs Mach, vs sideslip angle, damping derivatives, CS deflections

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pandas as pd

from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.SaveAeroCoefficients.func.plot import plot
from ceasiompy.SaveAeroCoefficients.func.utils import deal_with_feature

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    get_aeromap_list_from_xpath,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonxpath import PLOT_XPATH, AIRCRAFT_NAME_XPATH, AEROMAP_TO_PLOT_XPATH

from ceasiompy.SaveAeroCoefficients import MODULE_NAME

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Save Aero coefficients from the chosen aeroMap in the CPACS file.
    """

    # Define variables
    tixi = cpacs.tixi
    groupby_list = ["uid", "machNumber", "altitude", "angleOfSideslip"]

    # Get list of aeromaps
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, AEROMAP_TO_PLOT_XPATH)
    aeromap_df_list = []
    for aeromap_uid in aeromap_uid_list:
        aeromap_df = cpacs.get_aeromap_by_uid(aeromap_uid).df
        aeromap_df["uid"] = aeromap_uid
        aeromap_df_list.append(aeromap_df)
    aeromap = pd.concat(aeromap_df_list, ignore_index=True)

    if len(aeromap_uid_list) > 1:
        uid_crit = None
    else:
        uid_crit = aeromap_uid_list[0]

    title = tixi.getTextElement(AIRCRAFT_NAME_XPATH)
    criterion = pd.Series([True] * len(aeromap.index))

    crit_xpath = PLOT_XPATH + "/criterion"
    alt_crit = get_value_or_default(tixi, crit_xpath + "/alt", "None")
    mach_crit = get_value_or_default(tixi, crit_xpath + "/mach", "None")
    aos_crit = get_value_or_default(tixi, crit_xpath + "/aos", "None")

    deal_with_feature(title, criterion, aeromap, groupby_list, "altitude", alt_crit)
    deal_with_feature(title, criterion, aeromap, groupby_list, "machNumber", mach_crit)
    deal_with_feature(title, criterion, aeromap, groupby_list, "angleOfSideslip", aos_crit)

    if uid_crit is not None and len(groupby_list) > 1:
        criterion = criterion & (aeromap.uid == uid_crit)
        title += " - " + uid_crit
        groupby_list.remove("uid")

    # Generate plots
    plot(wkdir, groupby_list, title, aeromap, criterion)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
