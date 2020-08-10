"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS aeroMaps

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2019-08-19
| Last modifiction: 2020-07-16

TODO:

    * Add option to save figures in ToolOutput folder
    * add plot vs Mach, vs sideslip angle, damping derivatives, CS deflections

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from tkinter import *
import pandas as pd
import matplotlib.pyplot as plt

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.PlotAeroCoefficients.__specs__ import cpacs_inout

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

PLOT_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient'


#==============================================================================
#   CLASSES
#==============================================================================

class ListBoxChoice(object):
    def __init__(self, master=None, title='Title', message='Message', list=[]):

        self.selected_list = []

        self.master = master
        self.list = list[:]

        self.master.geometry("300x250") #Width x Height
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

        chooseButton = Button(buttonFrame, text='Select', command=self._select)
        chooseButton.pack()

        cancelButton = Button(buttonFrame, text='Cancel', command=self._cancel)
        cancelButton.pack(side=RIGHT)

    def _select(self, event=None):
        try:
            firstIndex = self.listBox.curselection()[0]
            self.selected_list = [self.listBox.get(i) for i in self.listBox.curselection()]
        except IndexError:
            self.selected_list = None

        self.master.destroy()

    def _cancel(self, event=None):
        self.listBox.selection_clear(0, END)

    def returnValue(self):
        self.master.wait_window()
        return self.selected_list


#==============================================================================
#   FUNCTIONS
#==============================================================================

def call_select_aeromap(tixi):
    """Function to select the aeroMap to plot

    Function 'call_select_aeromap' open a GUI with the available aeroMap to plot
    and retruns those selected by the user.

    Args:
        tixi (handles): TIXI Handle of the CPACS file

    Returns:
        selected_aeromap_list (list) : List of selected aeroMap

    """

    aeromap_uid_list = apmf.get_aeromap_uid_list(tixi)

    root = Tk()
    selected_aeromap_list = ListBoxChoice(root,'Select aeroMap Picking',
                                          'Select aeroMap(s) to plot \t \t',
                                          aeromap_uid_list).returnValue()

    return selected_aeromap_list


def write_legend(groupby_list, value):
    """Write legen with the correct fromat for the plot.

    Args:
        groupby_list (list): List of parameter whih will be use to group plot data
        value (...): If one value (str of float), if multiple value (tuple)

    """

    legend = ''
    for i, param in enumerate(groupby_list):

        if len(groupby_list) > 1:
            value_i = value[i]
        else:
            value_i = value

        if param is 'uid':
            legend += value_i
        else:
            legend += param + '=' + str(value_i)

        if i+1 != len(groupby_list):
            legend += '\n'

    return legend


def subplot_options(ax,ylabel,xlabel):
    """Set xlabel, ylabel and grit on a specific subplot.

    Args:
        ax (Axes objects): Axes of the concerned subplot
        xlabel (str): x label name
        ylabel (str): y label name
    """

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid()


def plot_aero_coef(cpacs_path,cpacs_out_path):
    """Plot all desire Aero coefficients from a CPACS file

    Function 'plot_aero_coef' can plot one or several aeromap from the CPACS
    file according to some user option, these option will be shown in the the
    SettingGUI or default values will be used.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
    """

    # Open TIXI handle
    tixi = cpsf.open_tixi(cpacs_path)
    aircraft_name = cpsf.aircraft_name(tixi)

    # Get aeroMap list to plot
    aeromap_to_plot_xpath = PLOT_XPATH + '/aeroMapToPlot'
    aeromap_uid_list = []

    # Option to select aeromap manualy
    manual_selct = cpsf.get_value_or_default(tixi,PLOT_XPATH+'/manualSelection',False)
    if manual_selct:
        aeromap_uid_list = call_select_aeromap(tixi)
        cpsf.create_branch(tixi,aeromap_to_plot_xpath)
        cpsf.add_string_vector(tixi,aeromap_to_plot_xpath,aeromap_uid_list)

    else:
        try:
            aeromap_uid_list = cpsf.get_string_vector(tixi,aeromap_to_plot_xpath)
        except:
            # If aeroMapToPlot is not define, select manualy anyway
            aeromap_uid_list = call_select_aeromap(tixi)
            cpsf.create_branch(tixi,aeromap_to_plot_xpath)
            cpsf.add_string_vector(tixi,aeromap_to_plot_xpath,aeromap_uid_list)

    # Create DataFrame from aeromap(s)
    aeromap_df_list = []
    for aeromap_uid in aeromap_uid_list:
        aeromap_df = apmf.get_datafram_aeromap(tixi,aeromap_uid)
        aeromap_df['uid'] = aeromap_uid
        aeromap_df_list.append(aeromap_df)

    aeromap = pd.concat(aeromap_df_list,ignore_index=True)

    if len(aeromap_uid_list) > 1:
        uid_crit = None
    else:
        uid_crit = aeromap_uid_list[0]

    # Default options
    title = aircraft_name
    criterion = pd.Series([True]*len(aeromap.index))
    groupby_list = ['uid','mach','alt', 'aos']
    NONE_LIST = ['None','NONE','No','NO','N','n','-',' ','']

    # Get criterion from CPACS
    crit_xpath = PLOT_XPATH + '/criterion'
    alt_crit = cpsf.get_value_or_default(tixi,crit_xpath+'/alt','None')
    mach_crit = cpsf.get_value_or_default(tixi,crit_xpath+'/mach','None')
    aos_crit = cpsf.get_value_or_default(tixi,crit_xpath+'/aos','None')

    # Modify criterion and title according to user option
    if len(aeromap['alt'].unique()) == 1:
        title += ' - Alt = ' + str(aeromap['alt'].loc[0])
        groupby_list.remove('alt')
    elif alt_crit not in NONE_LIST :
        criterion = criterion & (aeromap.alt == alt_crit)
        title += ' - Alt = ' + str(alt_crit)
        groupby_list.remove('alt')

    if len(aeromap['mach'].unique()) == 1:
        title += ' - Mach = ' + str(aeromap['mach'].loc[0])
        groupby_list.remove('mach')
    elif mach_crit not in NONE_LIST:
        criterion = criterion & (aeromap.mach == mach_crit)
        title += ' - Mach = ' + str(mach_crit)
        groupby_list.remove('mach')

    if len(aeromap['aos'].unique()) == 1:
        title += ' - AoS = ' + str(aeromap['aos'].loc[0])
        groupby_list.remove('aos')
    elif aos_crit not in NONE_LIST:
        criterion = criterion & (aeromap.aos == aos_crit)
        title += ' - AoS = ' + str(aos_crit)
        groupby_list.remove('aos')

    if uid_crit is not None and len(groupby_list) > 1:
        criterion = criterion & (aeromap.uid == uid_crit)
        title += ' - ' + uid_crit
        groupby_list.remove('uid')

    # Plot settings
    fig, axs = plt.subplots(2,3)
    fig.suptitle(title, fontsize=14)
    fig.set_figheight(8)
    fig.set_figwidth(15)
    fig.subplots_adjust(left=0.06)
    axs[0,1].axhline(y=0.0, color='k', linestyle='-') # Line at Cm=0

    # Plot curves
    for value, grp in aeromap.loc[criterion].groupby(groupby_list):

        legend = write_legend(groupby_list, value)

        axs[0,0].plot(grp['aoa'],grp['cl'],'x-',label=legend)
        axs[1,0].plot(grp['aoa'],grp['cd'],'x-')
        axs[0,1].plot(grp['aoa'],grp['cms'],'x-')
        axs[1,1].plot(grp['aoa'],grp['cl']/grp['cd'],'x-')
        axs[0,2].plot(grp['cd'],grp['cl'],'x-')
        axs[1,2].plot(grp['cl'],grp['cl']/grp['cd'],'x-')

    # Set subplot options
    subplot_options(axs[0,0],'CL','AoA')
    subplot_options(axs[1,0],'CD','AoA')
    subplot_options(axs[0,1],'Cm','AoA')
    subplot_options(axs[1,1],'CL/CD','AoA')
    subplot_options(axs[0,2],'CL','CD')
    subplot_options(axs[1,2],'CL/CD','CL')

    fig.legend(loc='upper right')
    plt.show()


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    plot_aero_coef(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
