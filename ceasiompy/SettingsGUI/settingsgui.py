"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Settings modifictions GUI for CEASIOMpy

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-09-05
| Last modifiction: 2019-09-10

TODO:

    * Add "mouse over" for description
    * Add 'AeroMap Edit'
    * Fix  'get_value' for boolean
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import numpy
import matplotlib
import importlib

import tkinter as tk
from tkinter import ttk

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl,close_tixi,    \
                                           create_branch, copy_branch, add_uid,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector, get_float_vector, \
                                           add_string_vector,get_string_vector,\
                                           aircraft_name

from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                         create_empty_aeromap, check_aeromap,  \
                                         save_parameters, save_coefficients,   \
                                         get_aeromap, merge_aeroMap,           \
                                         aeromap_from_csv, aeromap_to_csv,     \
                                         delete_aeromap



from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================

# Not use for now, but could be useful
class ListBoxChoice(object):
    def __init__(self, tab, tixi, list=[]):

        self.selected_item = None

        self.tab = tab
        self.tixi = tixi
        self.list = list[:]

        self.listBox = tk.Listbox(self.tab, selectmode=tk.SINGLE)
        self.listBox.grid(column=2, row=10)
        self.list.sort()
        for item in self.list:
            self.listBox.insert(tk.END, item)

        self.chooseButton = tk.Button(self.tab, text='Select', command=self._select)
        self.chooseButton.grid(column=2, row=11)

        self.cancelButton = tk.Button(self.tab, text='Cancel', command=self._cancel)
        self.cancelButton.grid(column=3, row=11)

    def _select(self, event=None):
        try:
            firstIndex = self.listBox.curselection()[0]
            self.selected_item = [self.listBox.get(i) for i in self.listBox.curselection()]
            print(self.selected_item)
        except IndexError:
            self.selected_item = None

    def _cancel(self, event=None):
        self.listBox.selection_clear(0, tk.END)

    # Do we need that?
    def returnValue(self):
        self.tab.wait_window()
        return self.selected_item


class AutoTab:
    """ Class to create automatically tabs from the infomation in the __specs__
        file of each module. """

    def __init__(self, tabs, tixi, module_name):

        self.tabs = tabs
        self.tixi = tixi
        self.tab = tk.Frame(tabs,borderwidth=1)
        tabs.add(self.tab, text=module_name)

        space_label = tk.Label(self.tab, text= ' ')
        space_label.grid(column=0, row=0)

        # Get dict from the __specs__ file
        try:
            specs = importlib.import_module('ceasiompy.' + module_name + '.__specs__')
            self.gui_settings_dict = specs.cpacs_inout.get_gui_dict()
        except:
            raise ValueError(f"--> GUI_SETTINGS NOT found for '{module_name}'")

        # Imported dictionary must have this form
        # xpath = '/cpacs/vehicles/aircraft/model'
        # self.gui_settings_dict = {
        # 'test1':[1,int,'m/s',xpath,'description','groupe'],
        # 'test2':[2.3,float,'deg',xpath,'description','groupe'],
        # 'test3':['aaa',str,None,xpath,'description',None],
        # 'test4':[True,bool,None,xpath,'description',None]
        # }

        self.var_dict = {}
        self.group_dict = {}
        row_pos = 1

        for key, [def_value,dtype,unit,xpath,description,group] in self.gui_settings_dict.items():

            # Create a LabelFrame for new groupe
            if group:
                if not group in self.group_dict:
                    self.labelframe = tk.LabelFrame(self.tab, text=group)
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3,sticky= tk.W, padx=5, pady=5)
                    self.group_dict[group] = self.labelframe
                parent = self.group_dict[group]
            else: # if not a group, use tab as parent
                parent = self.tab

            # Name label for variable
            name_label = tk.Label(parent, text= key)
            name_label.grid(column=0, row=row_pos, sticky= tk.W, padx=5, pady=5)

            # Type and Value
            if dtype is bool:
                self.var_dict[key] = tk.BooleanVar()
                # TODO: NOT working because get_value not recognize Boolean type
                # value = get_value_or_default(self.tixi,xpath,def_value)
                value = def_value
                self.var_dict[key].set(value)
                bool_entry = tk.Checkbutton(parent, text='', variable=self.var_dict[key])
                bool_entry.grid(column=1, row=row_pos,padx=5, pady=5)

            elif dtype is int:
                value = get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key] = tk.IntVar()
                self.var_dict[key].set(int(value))
                value_entry = tk.Entry(parent, bd =2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is float:
                value = get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key] = tk.DoubleVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, bd =2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is list:
                pass
                if 'AeroMap' in key :
                    self.var_dict[key] = 'AeroMapListType'
                    aeromap_uid_list = get_aeromap_uid_list(self.tixi)
                    self.labelframe = tk.LabelFrame(parent, text="AeroMap to calculate")
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky= tk.W, padx=5, pady=5)
                    self.aeromap_var_dict = {}

                    # Pre selected aeromap from the coresponding CPACS node
                    try:
                        selected_aeromap = get_string_vector(self.tixi,xpath)
                    except:
                        selected_aeromap = ''

                    for aeromap in aeromap_uid_list:
                        self.aeromap_var_dict[aeromap] = tk.BooleanVar()

                        if aeromap in selected_aeromap:
                            self.aeromap_var_dict[aeromap].set(True)
                        aeromap_entry = tk.Checkbutton(self.labelframe, text=aeromap, variable=self.aeromap_var_dict[aeromap])
                        aeromap_entry.pack(side= tk.TOP, anchor='w')
                else: # if it's a list of someting else than aeromap
                    log.warning('This function is not implemented yet!')
                    # TODO: see what to do in this case...

            else:
                value = get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key] = tk.StringVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            # Units
            if unit and unit != '1' :
                unit_label = tk.Label(parent, text= unit)
                unit_label.grid(column=2, row=row_pos, padx=5, pady=5)

            row_pos += 1

        # call listbox , Not used for now, could be useful...
        # aeromap_uid_list = get_aeromap_uid_list(self.tixi)
        # self.listbox1 = ListBoxChoice(self.tab,self.tixi,aeromap_uid_list) #.returnValue()

class CEASIOMpyGUI:
    def __init__(self, master, cpacs_path, cpacs_out_path):

        # GUI =============
        self.master = master
        self.master.title("CESAIOMpy Settings GUI")
        self.master.geometry("600x600+500+300")

        self.tabs = ttk.Notebook(self.master)
        self.tabs.pack(side=tk.TOP,fill='both')
        self.tabs.pack(expand=1, fill='both')

        # CPACS =============
        self.tixi = open_tixi(cpacs_path)

        # Generate Tab =============
        # TODO: @Aaron : add your function, get_submodule (in comment for now)
        self.module_name_list = ['PyTornado', 'SkinFriction','ModuleTemplate']
        self.tab_list = []

        for module_name in self.module_name_list:
            self.tab_list.append(AutoTab(self.tabs,self.tixi, module_name))

        # General button =============
        self.close_button = tk.Button(self.master, text="Close", command=self.save_quit)
        self.close_button.pack(side=tk.RIGHT)

    # Do we need a button for someting else ...?
    #     self.greet_button = tk.Button(self.master, text="Do things", command=self.greet)
    #     self.greet_button.pack(side= tk.LEFT)
    #
    # def greet(self):
    #     print("Things have been done!")

    def save_quit(self):

        # Iterate over all existing tabs
        for tab in self.tab_list:
            # Iterate in Variable dictionary of each tab
            for key, var in tab.var_dict.items():
                # Get the XPath from the GUI setting dictionary and crate a branch
                xpath = tab.gui_settings_dict[key][3]
                create_branch(self.tixi,xpath)

                if var == 'AeroMapListType':
                    aeromap_uid_list_str = ''
                    for aeromap_uid, aeromap_bool in tab.aeromap_var_dict.items():
                        if aeromap_bool.get():
                            aeromap_uid_list_str += aeromap_uid + ';'
                    self.tixi.updateTextElement(xpath,aeromap_uid_list_str)
                else:
                    self.tixi.updateTextElement(xpath,str(var.get()))

        close_tixi(self.tixi,cpacs_out_path)
        self.master.quit()


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)

    # Call Tkinter Class
    root = tk.Tk()
    my_gui = CEASIOMpyGUI(root,cpacs_path,cpacs_out_path)
    root.mainloop()

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')



### OLD function, to delete soon
    # def save_in_cpacs(self):
    #     for key, var in self.var_dict.items():
    #
    #         # Get the XPath from the GUI setting dictionary
    #         xpath = self.gui_settings_dict[key][3]
    #
    #         create_branch(self.tixi,xpath)
    #
    #         if var == 'AeroMapListType':
    #             aeromap_uid_list_str = ''
    #             for aeromap_uid, aeromap_bool in self.aeromap_var_dict.items():
    #                 if aeromap_bool.get():
    #                     aeromap_uid_list_str += aeromap_uid + ';'
    #             self.tixi.updateTextElement(xpath,aeromap_uid_list_str)
    #         else:
    #             self.tixi.updateTextElement(xpath,str(var.get()))
