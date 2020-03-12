"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS aeroMaps

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2019-08-19
| Last modifiction: 2020-02-21

TODO:

    * Add option to save figures in ToolOutput folder
    * Use aeromap with Pandas to sort easily the data
    * Plot more coefficient (vs sideslip angle, damping derivatives, control surfaces)

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from tkinter import *
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

        # self.modalPane.destroy()
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


def plot_aero_coef(cpacs_path,cpacs_out_path):
    """Function to plot available aerodynamic coefficients from aeroMap.

    Function 'plot_aero_coef' plot aerodynamic coefficients (CL,CD,Cm) of the
    aeroMap selected in the CPACS file or if not define, ask the user to select
    them.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    # Open TIXI handle
    tixi = cpsf.open_tixi(cpacs_path)

    # Prepare subplots
    figure_1 = plt.figure(figsize=(12, 12))
    subplot1 = figure_1.add_subplot(221)
    subplot2 = figure_1.add_subplot(222)
    subplot3 = figure_1.add_subplot(223)
    subplot4 = figure_1.add_subplot(224)

    LINE_STYLE = ['bo-','ro-','go-','co-','mo-','ko-','yo-']

    # Get aeroMap list to plot
    aeromap_to_plot_xpath = PLOT_XPATH + '/aeroMapToPlot'
    aeromap_uid_list = []
    try:
        aeromap_uid_list = cpsf.get_string_vector(tixi,aeromap_to_plot_xpath)
    except:
        # If aeroMapToPlot is not define, open GUI to select which ones shoud be
        aeromap_uid_list = call_select_aeromap(tixi)
        cpsf.create_branch(tixi,aeromap_to_plot_xpath)
        cpsf.add_string_vector(tixi,aeromap_to_plot_xpath,aeromap_uid_list)

    for i, aeromap_uid in enumerate(aeromap_uid_list):

        log.info('"' + aeromap_uid + '" will be added to the plot.')

        # Get aeroMap to plot and replace missing results with zeros
        AeroCoef = apmf.get_aeromap(tixi,aeromap_uid)
        AeroCoef.complete_with_zeros()
        AeroCoef.print_coef_list()

        # Subplot1
        x1 = AeroCoef.aoa
        y1 = AeroCoef.cl
        subplot1.plot(x1,y1,LINE_STYLE[i])

        # Subplot2
        x2 = AeroCoef.aoa
        y2 = AeroCoef.cms
        subplot2.plot(x2,y2,LINE_STYLE[i])

        # Subplot3
        x3 = AeroCoef.aoa
        y3 = AeroCoef.cd
        subplot3.plot(x3,y3,LINE_STYLE[i])

        # Subplot4
        x4 = AeroCoef.aoa
        if any(AeroCoef.cd) == 0.0:
            cl_cd = [0]*len(AeroCoef.aoa)
        else:
            cl_cd = res = [cl/cd for cl, cd in zip(AeroCoef.cl, AeroCoef.cd)]
        y4 = cl_cd
        subplot4.plot(x4,y4,LINE_STYLE[i])

    # Labels
    subplot1.set_xlabel('Angle of attack')
    subplot1.set_ylabel('Lift coefficient')
    subplot2.set_xlabel('Angle of attack')
    subplot2.set_ylabel('Moment coefficient')
    subplot3.set_xlabel('Angle of attack')
    subplot3.set_ylabel('Drag coefficient')
    subplot4.set_xlabel('Angle of attack')
    subplot4.set_ylabel('Efficiency CL/CD')

    # Legend
    figure_1.legend(aeromap_uid_list)

    # Grid
    subplot1.grid()
    subplot2.grid()
    subplot3.grid()
    subplot4.grid()

    cpsf.close_tixi(tixi,cpacs_out_path)

    plt.show()


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # Plot aerodynamic coefficients
    plot_aero_coef(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
