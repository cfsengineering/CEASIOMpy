"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS v3 aeroMaps

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2019-08-19

TODO:

    * add plot vs Mach, vs sideslip angle, damping derivatives, CS deflections

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import PLOT_XPATH
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from cpacspy.cpacsfunctions import (
    add_string_vector,
    create_branch,
    get_string_vector,
    get_value_or_default,
)
from cpacspy.cpacspy import CPACS

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

NONE_LIST = ["None", "NONE", "No", "NO", "N", "n", "-", " ", ""]

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_legend(groupby_list, value):
    """Write legend with the correct format for the plot.

    Args:
        groupby_list (list): List of parameter which will be use to group plot data
        value (...): If one value (str of float), if multiple value (tuple)
    """

    groupby_name_list = []
    for name in groupby_list:
        if name == "machNumber":
            groupby_name_list.append("Mach")
        elif name == "angleOfAttack":
            groupby_name_list.append("AoA")
        elif name == "angleOfSideslip":
            groupby_name_list.append("AoS")
        elif name == "altitude":
            groupby_name_list.append("Alt")
        else:
            groupby_name_list.append(name)

    legend = ""
    for i, param in enumerate(groupby_list):

        if len(groupby_list) > 1:
            value_i = value[i]
        else:
            value_i = value

        if param == "uid":
            legend += value_i
        else:
            if param == "machNumber":
                name = "Mach"
            elif param == "angleOfAttack":
                name = "AoA"
            elif param == "angleOfSideslip":
                name = "AoS"
            elif param == "altitude":
                name = "Alt"
            else:
                name = param
            legend += name + "=" + str(value_i)

        if i + 1 != len(groupby_list):
            legend += "\n"

    return legend


def subplot_options(ax, ylabel, xlabel):
    """Set xlabel, ylabel and grid on a specific subplot.

    Args:
        ax (Axes objects): Axes of the concerned subplot
        xlabel (str): x label name
        ylabel (str): y label name
    """

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid()


def save_aero_coef(cpacs_path, cpacs_out_path):
    """Save Aero coefficients from the chosen aeroMap in the CPACS file

    Function 'save_aero_coef' can save one or several aeromap from the CPACS
    file according to some user defined option, these option will be shown in the the
    GUI interface or default values will be used.

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file
    """

    cpacs = CPACS(cpacs_path)

    aeromap_to_plot_xpath = PLOT_XPATH + "/aeroMapToPlot"
    aeromap_uid_list = []

    try:
        aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_plot_xpath)
    except ValueError:  # if aeroMapToPlot is not define, select all aeromaps
        aeromap_uid_list = cpacs.get_aeromap_uid_list()
        create_branch(cpacs.tixi, aeromap_to_plot_xpath)
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, aeromap_uid_list)

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

    title = cpacs.ac_name
    criterion = pd.Series([True] * len(aeromap.index))
    groupby_list = ["uid", "machNumber", "altitude", "angleOfSideslip"]

    crit_xpath = PLOT_XPATH + "/criterion"
    alt_crit = get_value_or_default(cpacs.tixi, crit_xpath + "/alt", "None")
    mach_crit = get_value_or_default(cpacs.tixi, crit_xpath + "/mach", "None")
    aos_crit = get_value_or_default(cpacs.tixi, crit_xpath + "/aos", "None")

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)

    # Modify criterion and title according to user option
    if len(aeromap["altitude"].unique()) == 1:
        title += " - Alt = " + str(aeromap["altitude"].loc[0])
        groupby_list.remove("altitude")
    elif alt_crit not in NONE_LIST:
        criterion = criterion & (aeromap.altitude == alt_crit)
        title += " - Alt = " + str(alt_crit)
        groupby_list.remove("altitude")

    if len(aeromap["machNumber"].unique()) == 1:
        title += " - Mach = " + str(aeromap["machNumber"].loc[0])
        groupby_list.remove("machNumber")
    elif mach_crit not in NONE_LIST:
        criterion = criterion & (aeromap.machNumber == mach_crit)
        title += " - Mach = " + str(mach_crit)
        groupby_list.remove("machNumber")

    if len(aeromap["angleOfSideslip"].unique()) == 1:
        title += " - AoS = " + str(aeromap["angleOfSideslip"].loc[0])
        groupby_list.remove("angleOfSideslip")
    elif aos_crit not in NONE_LIST:
        criterion = criterion & (aeromap.angleOfSideslip == aos_crit)
        title += " - AoS = " + str(aos_crit)
        groupby_list.remove("angleOfSideslip")

    if uid_crit is not None and len(groupby_list) > 1:
        criterion = criterion & (aeromap.uid == uid_crit)
        title += " - " + uid_crit
        groupby_list.remove("uid")

    fig, axs = plt.subplots(2, 3)
    fig.suptitle(title, fontsize=14)
    fig.set_figheight(8)
    fig.set_figwidth(15)
    fig.subplots_adjust(left=0.06)
    axs[0, 1].axhline(y=0.0, color="k", linestyle="-")  # Line at Cm=0

    for value, grp in aeromap.loc[criterion].groupby(groupby_list):

        legend = write_legend(groupby_list, value)

        axs[0, 0].plot(grp["angleOfAttack"], grp["cl"], "x-", label=legend)
        axs[1, 0].plot(grp["angleOfAttack"], grp["cd"], "x-")
        axs[0, 1].plot(grp["angleOfAttack"], grp["cms"], "x-")
        axs[1, 1].plot(grp["angleOfAttack"], grp["cl"] / grp["cd"], "x-")
        axs[0, 2].plot(grp["cd"], grp["cl"], "x-")
        axs[1, 2].plot(grp["cl"], grp["cl"] / grp["cd"], "x-")

    subplot_options(axs[0, 0], "CL", "AoA")
    subplot_options(axs[1, 0], "CD", "AoA")
    subplot_options(axs[0, 1], "Cm", "AoA")
    subplot_options(axs[1, 1], "CL/CD", "AoA")
    subplot_options(axs[0, 2], "CL", "CD")
    subplot_options(axs[1, 2], "CL/CD", "CL")
    fig.legend(loc="upper right")

    results_dir = get_results_directory("SaveAeroCoefficients")
    fig_name = title.replace(" ", "").replace("=", "") + ".png"
    fig_path = Path(results_dir, fig_name)
    plt.savefig(fig_path)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    save_aero_coef(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
