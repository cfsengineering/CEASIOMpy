"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS v3 aeroMaps

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2019-08-19

TODO:

    * Add option to save figures in ToolOutput folder
    * add plot vs Mach, vs sideslip angle, damping derivatives, CS deflections

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Label, Tk, Listbox, END, Button, MULTIPLE, BOTH, Frame, BOTTOM, RIGHT

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (
    add_string_vector,
    create_branch,
    get_string_vector,
    get_value_or_default,
)

import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.utils.xpath import PLOT_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

NONE_LIST = ["None", "NONE", "No", "NO", "N", "n", "-", " ", ""]

# ==============================================================================
#   CLASSES
# ==============================================================================


class ListBoxChoice(object):
    def __init__(self, master=None, title="Title", message="Message", list=[]):

        self.selected_list = []
        self.master = master
        self.list = list[:]
        self.master.geometry("300x250")  # Width x Height
        self.master.grab_set()
        self.master.bind("<Return>", self._select)
        self.master.bind("<Escape>", self._cancel)
        self.master.title(title)
        Label(self.master, text=message).pack(padx=5, pady=5)

        self.listBox = Listbox(self.master, selectmode=MULTIPLE)
        self.listBox.pack(fill=BOTH)
        self.list.sort()
        for item in self.list:
            self.listBox.insert(END, item)

        buttonFrame = Frame(self.master)
        buttonFrame.pack(side=BOTTOM)

        chooseButton = Button(buttonFrame, text="Select", command=self._select)
        chooseButton.pack()

        cancelButton = Button(buttonFrame, text="Cancel", command=self._cancel)
        cancelButton.pack(side=RIGHT)

    def _select(self, event=None):
        try:
            self.selected_list = [self.listBox.get(i) for i in self.listBox.curselection()]
        except IndexError:
            self.selected_list = None

        self.master.destroy()

    def _cancel(self, event=None):
        self.listBox.selection_clear(0, END)

    def returnValue(self):
        self.master.wait_window()
        return self.selected_list


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def open_select_aeromap_gui(cpacs):
    """Function to select one or several aeroMap to plot wit a GUI

    Function 'open_select_aeromap_gui' open a GUI with all the available aeroMaps
    to plot and retruns a list of those selected by the user.

    Args:
        cpacs (oject): CPACS Object (from cpacspy)

    Returns:
        selected_aeromap_list (list) : List of selected aeroMap
    """

    aeromap_uid_list = cpacs.get_aeromap_uid_list()

    root = Tk()
    selected_aeromap_list = ListBoxChoice(
        root, "Select aeroMap", "Select aeroMap(s) to plot \t \t", aeromap_uid_list
    ).returnValue()

    return selected_aeromap_list


def write_legend(groupby_list, value):
    """Write legen with the correct fromat for the plot.

    Args:
        groupby_list (list): List of parameter whih will be use to group plot data
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


def plot_aero_coef(cpacs_path, cpacs_out_path):
    """Plot Aero coefficients from the chosen aeroMap in the CPACS file

    Function 'plot_aero_coef' can plot one or several aeromap from the CPACS
    file according to some user option, these option will be shown in the the
    SettingGUI or default values will be used.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
    """

    # Open TIXI handle
    cpacs = CPACS(cpacs_path)

    # Get aeroMap list to plot
    aeromap_to_plot_xpath = PLOT_XPATH + "/aeroMapToPlot"
    aeromap_uid_list = []

    # Option to select aeromap manualy
    manual_selct = get_value_or_default(cpacs.tixi, PLOT_XPATH + "/manualSelection", False)
    if manual_selct:
        aeromap_uid_list = open_select_aeromap_gui(cpacs)
        create_branch(cpacs.tixi, aeromap_to_plot_xpath)
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, aeromap_uid_list)

    else:
        try:
            aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_plot_xpath)
        except ValueError:
            # If aeroMapToPlot is not define, select manualy anyway
            aeromap_uid_list = open_select_aeromap_gui(cpacs)
            create_branch(cpacs.tixi, aeromap_to_plot_xpath)
            add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, aeromap_uid_list)

    # Create DataFrame from aeromap(s)
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

    # Default options
    title = cpacs.ac_name
    criterion = pd.Series([True] * len(aeromap.index))
    groupby_list = ["uid", "machNumber", "altitude", "angleOfSideslip"]

    # Get criterion from CPACS
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

    # Plot settings
    fig, axs = plt.subplots(2, 3)
    fig.suptitle(title, fontsize=14)
    fig.set_figheight(8)
    fig.set_figwidth(15)
    fig.subplots_adjust(left=0.06)
    axs[0, 1].axhline(y=0.0, color="k", linestyle="-")  # Line at Cm=0

    # Plot aerodynamic coerfficients
    for value, grp in aeromap.loc[criterion].groupby(groupby_list):

        legend = write_legend(groupby_list, value)

        axs[0, 0].plot(grp["angleOfAttack"], grp["cl"], "x-", label=legend)
        axs[1, 0].plot(grp["angleOfAttack"], grp["cd"], "x-")
        axs[0, 1].plot(grp["angleOfAttack"], grp["cms"], "x-")
        axs[1, 1].plot(grp["angleOfAttack"], grp["cl"] / grp["cd"], "x-")
        axs[0, 2].plot(grp["cd"], grp["cl"], "x-")
        axs[1, 2].plot(grp["cl"], grp["cl"] / grp["cd"], "x-")

    # Set subplot options
    subplot_options(axs[0, 0], "CL", "AoA")
    subplot_options(axs[1, 0], "CD", "AoA")
    subplot_options(axs[0, 1], "Cm", "AoA")
    subplot_options(axs[1, 1], "CL/CD", "AoA")
    subplot_options(axs[0, 2], "CL", "CD")
    subplot_options(axs[1, 2], "CL/CD", "CL")

    fig.legend(loc="upper right")
    plt.show()


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("----- Start of " + os.path.basename(__file__) + " -----")

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    plot_aero_coef(cpacs_path, cpacs_out_path)

    log.info("----- End of " + os.path.basename(__file__) + " -----")
