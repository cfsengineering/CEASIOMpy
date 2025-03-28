"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author: Leon Deligny
| Creation: 27 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from typing import List

from ceasiompy import *
from ceasiompy.SaveAeroCoefficients import *

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_legend(groupby_list: List, value) -> None:
    """Write legend with the correct format for the plot.

    Args:
        groupby_list (list): List of parameter which will be use to group plot data
        value (...): If one value (str of float), if multiple value (tuple)
    """

    groupby_name_list = []
    for name in groupby_list:
        if name in FEATURE_DICT.keys():
            groupby_name_list.append(FEATURE_DICT[name])
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
            if name in FEATURE_DICT.keys():
                name = FEATURE_DICT[name]
            else:
                name = param
                
            legend += name + "=" + str(value_i)

        if i + 1 != len(groupby_list):
            legend += "\n"

    return legend


def subplot_options(ax, ylabel: str, xlabel: str) -> None:
    """Set xlabel, ylabel and grid on a specific subplot.

    Args:
        ax (Axes objects): Axes of the concerned subplot
        xlabel (str): x label name
        ylabel (str): y label name
    """

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid()


def deal_with_feature(title, criterion, aeromap, groupby_list, feature: str, crit: float) -> None:
    feature_ = FEATURE_DICT[feature]
    if len(aeromap[feature].unique()) == 1:
        title += f" - {feature_} = " + str(aeromap[feature].loc[0])
        groupby_list.remove(feature)
    elif crit not in NONE_LIST:
        criterion = criterion & (aeromap.angleOfSideslip == crit)
        title += f" - {feature_} = " + str(crit)
        groupby_list.remove(feature)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
