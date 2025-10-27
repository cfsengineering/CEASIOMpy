"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS v3 aeroMaps

TODO:
    * add plot vs Mach, vs sideslip angle, damping derivatives, CS deflections
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pandas as pd

from ceasiompy.utils.terminal import call_main
from ceasiompy.SaveAeroCoefficients.func.plot import plot
from ceasiompy.SaveAeroCoefficients.func.utils import deal_with_feature
from ceasiompy.SaveAeroCoefficients.func.responsesurface import plot_response_surface
from cpacspy.cpacsfunctions import (
    get_string_vector,
    get_value_or_default,
)

from pathlib import Path
from ceasiompy.utils.guisettings import GUISettings
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy.SaveAeroCoefficients import (
    CRIT_XPATH,
    MODULE_NAME,
)
from ceasiompy.utils.cpacsxpaths import AIRCRAFT_NAME_XPATH
from ceasiompy.utils.guixpaths import (
    RS_XPATH,
    AEROMAP_TO_PLOT_XPATH,
)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Save Aero coefficients from the chosen aeroMap in the CPACS file.
    """

    # Define variables
    groupby_list = ["uid", "machNumber", "altitude", "angleOfSideslip"]

    # Get list of aeromaps
    aeromap_uid_list = get_string_vector(gui_settings.tixi, AEROMAP_TO_PLOT_XPATH)
    aeromap_df_list = []
    for aeromap_uid in aeromap_uid_list:
        aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
        aeromap_df = aeromap.df
        aeromap_df["uid"] = aeromap_uid
        aeromap_df_list.append(aeromap_df)
    aeromap = pd.concat(aeromap_df_list, ignore_index=True)

    if len(aeromap_uid_list) > 1:
        uid_crit = None
    else:
        uid_crit = aeromap_uid_list[0]

    title = cpacs.tixi.getTextElement(AIRCRAFT_NAME_XPATH)
    criterion = pd.Series([True] * len(aeromap.index))

    alt_crit = get_value_or_default(gui_settings.tixi, CRIT_XPATH + "/alt", "None")
    mach_crit = get_value_or_default(gui_settings.tixi, CRIT_XPATH + "/mach", "None")
    aos_crit = get_value_or_default(gui_settings.tixi, CRIT_XPATH + "/aos", "None")

    deal_with_feature(title, criterion, aeromap, groupby_list, "altitude", alt_crit)
    deal_with_feature(title, criterion, aeromap, groupby_list, "machNumber", mach_crit)
    deal_with_feature(title, criterion, aeromap, groupby_list, "angleOfSideslip", aos_crit)

    if uid_crit is not None and len(groupby_list) > 1:
        criterion = criterion & (aeromap.uid == uid_crit)
        title += " - " + uid_crit
        groupby_list.remove("uid")

    plot(results_dir, groupby_list, title, aeromap, criterion)

    if get_value_or_default(gui_settings.tixi, RS_XPATH + "/Plot", False):
        plot_response_surface(cpacs, results_dir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
