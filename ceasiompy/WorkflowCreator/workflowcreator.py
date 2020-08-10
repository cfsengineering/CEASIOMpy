"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Tool to create workflow for CEASIOMpy with or without GUI

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-04-21
| Last modifiction: 2020-07-02

TODO:

    * more options for optim ?

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import sys
import shutil

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog

import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.Optimisation.optimisation import routine_launcher
from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   IMPORTS
# ==============================================================================

class WorkflowOptions:
    """ Class to pass option of the workflow """

    def __init__(self):

        cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
        if os.path.isfile(cpacs_path):
            self.cpacs_path = cpacs_path
        else:
             self.cpacs_path = ''

        self.optim_method = 'None' # 'None', 'Optim', 'DoE'
        self.module_pre = []
        self.module_optim = []
        self.module_post = []


class Tab(tk.Frame):
    """ Class to create tab in the WorkflowCreator GUI """

    def __init__(self, master, name, **kwargs):

        tk.Frame.__init__(self, master, **kwargs)

        self.name = name

        # Get list of available modules
        self.modules_list = mi.get_submodule_list()
        self.modules_list.sort()

        self.modules_list.remove('SettingsGUI')
        self.modules_list.insert(0,'SettingsGUI')

        self.modules_list.remove('CPACSUpdater')
        self.modules_list.remove('WorkflowCreator')
        self.modules_list.remove('utils')
        try:
            self.modules_list.remove('WKDIR')
        except:
            log.info('No WKDIR yet.')

        self.selected_list = []

        row_pos = 0

        if name == 'Optim':

            label_optim = tk.Label(self, text='Optimisation method')
            label_optim.grid(column=0, row=0, columnspan=1,pady=10)

            # The Combobox is directly use as the varaible
            optim_choice = ['None', 'DoE', 'Optim']
            self.optim_choice_CB = ttk.Combobox(self, values=optim_choice, width=15)
            self.optim_choice_CB.grid(column=4, row=row_pos)
            row_pos += 1

        # ListBox with all available modules
        tk.Label(self, text='Available modules').grid(column=0, row=row_pos, pady=5)
        self.LB_modules = tk.Listbox(self, selectmode=tk.SINGLE, width=25, height=len(self.modules_list))
        item_count = len(self.modules_list)
        self.LB_modules.grid(column=0, row=row_pos+1, columnspan=3, rowspan=15, padx=10, pady=3)
        for item in self.modules_list:
            self.LB_modules.insert(tk.END, item)

        # Button
        addButton = tk.Button(self, text='   Add >   ', command=self._add)
        addButton.grid(column=4, row=row_pos+1)
        removeButton = tk.Button(self, text='< Remove', command=self._remove)
        removeButton.grid(column=4, row=row_pos+2)
        upButton = tk.Button(self, text='    Up  ^   ', command=self._up)
        upButton.grid(column=4, row=row_pos+3)
        downButton = tk.Button(self, text='  Down v  ', command=self._down)
        downButton.grid(column=4, row=row_pos+4)

        # ListBox with all selected modules
        tk.Label(self, text='Selected modules').grid(column=5, row=row_pos)
        self.LB_selected = tk.Listbox(self, selectmode=tk.SINGLE, width=25, height=len(self.modules_list))
        self.LB_selected.grid(column=5, row=row_pos+1, columnspan=3, rowspan=15, padx=10, pady=3)
        for item in self.selected_list:
            self.LB_selected.insert(tk.END, item)
            row_pos += (item_count + 1)

    def _add(self, event=None):
        """ Function of the button add: to pass a module from Available module
            list to Selected module list"""

        try:
            select_item = [self.LB_modules.get(i) for i in self.LB_modules.curselection()]
            self.selected_list.append(select_item[0])
            self.LB_selected.insert(tk.END, select_item)
        except IndexError:
            self.selected_item = None

    def _remove(self, event=None):
        """ Function of the button remove: to remove a module from the Selected
            module list"""

        sel = self.LB_selected.curselection()
        for index in sel[::-1]:
            self.LB_selected.delete(index)

    def _up(self, event=None):
        """ Function of the button up: to move upward a module in the Selected
            module list"""

        pos_list = self.LB_selected.curselection()

        if not pos_list:
            return

        for pos in pos_list:
            if pos == 0:
                continue
            item = self.LB_selected.get(pos)
            self.LB_selected.delete(pos)
            self.LB_selected.insert(pos - 1, item)

    def _down(self, event=None):
        """ Function of the button down: to move downward a module in the
            Selected module list."""

        pos_list = self.LB_selected.curselection()

        if not pos_list:
            return

        for pos in pos_list:
            if pos == self.LB_selected.size():
                continue
            item = self.LB_selected.get(pos)
            self.LB_selected.delete(pos)
            self.LB_selected.insert(pos + 1, item)


class WorkFlowGUI(tk.Frame):
    def __init__(self, master=None, **kwargs):

        tk.Frame.__init__(self, master, **kwargs)
        self.pack(fill=tk.BOTH)

        self.Options = WorkflowOptions()

        space_label = tk.Label(self, text=' ')
        space_label.grid(column=0, row=0)

        # Input CPACS file
        self.label = tk.Label(self, text='  Input CPACS file')
        self.label.grid(column=0, row=1)

        self.path_var = tk.StringVar()
        self.path_var.set(self.Options.cpacs_path)
        value_entry = tk.Entry(self, textvariable=self.path_var, width= 45)
        value_entry.grid(column=1, row=1)

        self.browse_button = tk.Button(self, text="Browse", command=self._browse_file)
        self.browse_button.grid(column=2, row=1, pady=5)

        # Notebook for tabs
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(column=0, row=2, columnspan=3,padx=10,pady=10)

        self.TabPre = Tab(self, 'Pre')
        self.TabOptim = Tab(self, 'Optim')
        self.TabPost = Tab(self, 'Post')

        self.tabs.add(self.TabPre, text=self.TabPre.name)
        self.tabs.add(self.TabOptim, text=self.TabOptim.name)
        self.tabs.add(self.TabPost, text=self.TabPost.name)

        # General buttons
        self.close_button = tk.Button(self, text='Save & Quit', command=self._save_quit)
        self.close_button.grid(column=2, row=3)


    def _browse_file(self):

        cpacs_template_dir = os.path.join(MODULE_DIR,'..','..','test','CPACSfiles')
        self.filename = filedialog.askopenfilename(initialdir = cpacs_template_dir, title = "Select a CPACS file" )
        self.path_var.set(self.filename)

    def _save_quit(self):

        self.Options.optim_method = self.TabOptim.optim_choice_CB.get()

        self.Options.module_pre = [item[0] for item in self.TabPre.LB_selected.get(0, tk.END)]
        self.Options.module_optim = [item[0] for item in self.TabOptim.LB_selected.get(0, tk.END)]
        self.Options.module_post = [item[0] for item in self.TabPost.LB_selected.get(0, tk.END)]

        self.Options.cpacs_path = self.path_var.get()
        if self.path_var.get() == '':
            messagebox.showerror('ValueError', 'Yon must select an input CPACS file!')
            raise TypeError('No CPACS file has been define !')

        self.quit()


# ==============================================================================
#    MAIN
# ==============================================================================

def create_wf_gui():
    """ Create a GUI with Tkinter to fill the workflow to run

    Args:
        cpacs_path (str): Path to the CPACS file
        cpacs_out_path (str): Path to the output CPACS file
        module_list (list): List of module to inclue in the GUI

    """

    root = tk.Tk()
    root.title('Workflow Creator')
    root.geometry('475x495+400+300')
    my_gui = WorkFlowGUI()
    my_gui.mainloop()
    disg = my_gui.Options

    root.iconify() # Not super solution but only way to make it close on Mac
    root.destroy()

    return disg


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path_out = mi.get_tooloutput_file_path(MODULE_NAME)

    gui = False

    if len(sys.argv) > 1:
        if sys.argv[1] == '-gui':
            gui = True
        else:
            print(' ')
            print('Not valid argument!')
            print('You can use the option -gui to run this module with a user interface.')
            print(' ')
            sys.exit()

    if gui:
        Opt = create_wf_gui()
    else:
        ####### USER INPUT ########
        ### Available Module:
        # Settings: 'SettingsGUI'
        # Geometry and mesh: 'CPACSCreator','CPACS2SUMO','SUMOAutoMesh'
        # Weight and balance: 'WeightConventional','WeightUnconventional','BalanceConventional','BalanceUnconventional'
        # Aerodynamics: 'CLCalculator','PyTornado','SkinFriction','PlotAeroCoefficients','SU2MeshDef','SU2Run'
        # Mission analysis: 'Range','StabilityStatic'

        Opt = WorkflowOptions()

        # These options can be modified here if WorkflowCreator is used without GUI
        # Opt.cpacs_path = '../../test/CPACSfiles/simpletest_cpacs.xml'
        Opt.module_pre = []
        Opt.module_optim = ['WeightConventional', 'PyTornado']

        Opt.optim_method = 'DoE' # DoE, Optim, None
        Opt.module_post = []

    # Copy ToolInput.xml in ToolInput dir if not already there
    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    if not Opt.cpacs_path == cpacs_path:
        shutil.copy(Opt.cpacs_path, cpacs_path)
        Opt.cpacs_path = cpacs_path

    # Create a new wkdir
    tixi = cpsf.open_tixi(Opt.cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    cpsf.close_tixi(tixi, Opt.cpacs_path)

    # Run Pre-otimisation workflow
    if Opt.module_pre:
        wkf.run_subworkflow(Opt.module_pre, Opt.cpacs_path)

        if not Opt.module_optim and not Opt.module_post:
            shutil.copy(mi.get_tooloutput_file_path(Opt.module_pre[-1]), cpacs_path_out)

    # Run Optimisation workflow
    if Opt.module_optim:
        if Opt.module_pre:
            wkf.copy_module_to_module(Opt.module_pre[-1], 'out', 'Optimisation', 'in')
        else:
            wkf.copy_module_to_module('WorkflowCreator', 'in', 'Optimisation', 'in')

        if Opt.optim_method != 'None':
            routine_launcher(Opt)
        else:
            log.warning('No optimization method has been selected!')
            log.warning('The modules will be run as a simple workflow')
            wkf.run_subworkflow(Opt.module_optim)

        if not Opt.module_post:
            shutil.copy(mi.get_tooloutput_file_path(Opt.module_optim[-1]), cpacs_path_out)

    # Run Post-optimisation workflow
    if Opt.module_post:

        if Opt.module_optim:
            wkf.copy_module_to_module(Opt.module_optim[-1], 'out', Opt.module_post[0], 'in')
        elif Opt.module_pre:
            wkf.copy_module_to_module(Opt.module_pre[-1], 'out', Opt.module_post[0], 'in')
        else:
            wkf.copy_module_to_module('WorkflowCreator', 'in', Opt.module_post[0], 'in')

        # wkf.copy_module_to_module('CPACSUpdater','out',Opt.module_post[0],'in')  usefuel?
        wkf.run_subworkflow(Opt.module_post)
        shutil.copy(mi.get_tooloutput_file_path(Opt.module_post[-1]), cpacs_path_out)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
