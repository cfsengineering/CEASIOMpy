"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Settings modifictions GUI for CEASIOMpy

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-09-05
| Last modifiction: 2019-09-09

TODO:

    * In developement module !!!!
    *  ...
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


#==============================================================================
#   CLASSES
#==============================================================================

class ListBoxChoice(object):
    def __init__(self, tab, tixi, list=[]):

        self.selected_item = None

        self.tab = tab
        self.tixi = tixi
        self.list = list[:]

        self.listBox = tk.Listbox(self.tab, selectmode=tk.SINGLE)
        self.listBox.grid(column=1, row=10)
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
    """ Class to crate automatically tabs from the infomation in the __specs__
        file of each module. """

    def __init__(self, tabs, tixi, module_name):

        self.tabs = tabs
        self.tixi = tixi
        self.tab = tk.Frame(tabs)
        tabs.add(self.tab, text=module_name)

        module_name_label = tk.Label(self.tab, text= module_name + ' Settings', font='Helvetica 12 bold')
        module_name_label.grid(column=0, row=0, columnspan=2, sticky= tk.W)

        # Get dict from the __specs__ file
        try:
            specs = importlib.import_module('ceasiompy.' + module_name + '.__specs__')
            gui_settings_dict = specs.GUI_SETTINGS
        except:
            raise ValueError(f"--> GUI_SETTINGS NOT found for '{module_name}'")

        # Crate a dummy dictionary
        # gui_settings_dict = {
        # 'test1':[1,int,'m/s',xpath,'description'],
        # 'test2':[2.3,float,'deg',xpath,'description'],
        # 'test3':['aaa',str,None,xpath,'description'],
        # 'test4':[True,bool,None,xpath,'description']
        # }

        var_list = []
        row_pos = 2

        for key, [def_value,dtype,unit,xpath,description] in gui_settings_dict.items():

            # Name
            name_label = tk.Label(self.tab, text= key)
            name_label.grid(column=0, row=row_pos)

            # Type and Value
            if dtype is bool:
                # value = get_value_or_default(self.tixi,xpath,def_value)
                # how to deal with boolean
                value = def_value
                var_list.append(tk.BooleanVar())
                var_list[-1].set(value)
                bool_entry = tk.Checkbutton(self.tab, text='', variable=var_list[-1])
                bool_entry.grid(column=1, row=row_pos)

            elif dtype is int:
                value = get_value_or_default(self.tixi,xpath,def_value)
                var_list.append(tk.IntVar())
                var_list[-1].set(value)
                value_entry = tk.Entry(self.tab, bd =2, textvariable=var_list[-1])
                value_entry.grid(column=1, row=row_pos)

            elif dtype is float:
                value = get_value_or_default(self.tixi,xpath,def_value)
                var_list.append(tk.DoubleVar())
                var_list[-1].set(value)
                value_entry = tk.Entry(self.tab, bd =2, textvariable=var_list[-1])
                value_entry.grid(column=1, row=row_pos)

            elif dtype is list:
                if 'AeroMap' in key :
                    aeromap_uid_list = get_aeromap_uid_list(self.tixi)
                    labelframe = tk.LabelFrame(self.tab, text="AeroMap to calculate")
                    labelframe.grid(column=0, row=row_pos, columnspan=2)
                    aeromap_var_list = []
                    for aeromap in aeromap_uid_list:
                        aeromap_var_list.append(tk.BooleanVar())
                        if def_value == aeromap:
                            var_list[-1].set(True)
                        bool_entry = tk.Checkbutton(labelframe, text=aeromap, variable=aeromap_var_list[-1])
                        bool_entry.pack(side= tk.TOP, anchor='w')


                        #Selected ones
                        # value = get_string_vector(self.tixi,xpath)

                # var_list.append(tk.StringVar())
                # var_list[-1].set(value)
                # value_entry = tk.Entry(self.tab, bd =2, textvariable=var_list[-1])
                # value_entry.grid(column=1, row=row_pos)


            else:
                value = get_value_or_default(self.tixi,xpath,def_value)
                var_list.append(tk.StringVar())
                var_list[-1].set(value)
                value_entry = tk.Entry(self.tab, bd =2, textvariable=var_list[-1])
                value_entry.grid(column=1, row=row_pos)

            # Units
            if unit and unit != '1' :
                name_label = tk.Label(self.tab, text= unit)
                name_label.grid(column=2, row=row_pos)

            row_pos += 1

        self.var_list = var_list

        self.greet_button = tk.Button(self.tab, text="Print", command=self.print_values)
        self.greet_button.grid(column=1, row=row_pos)

        # call listbox
        # aeromap_uid_list = get_aeromap_uid_list(self.tixi)
        # self.listbox1 = ListBoxChoice(self.tab,self.tixi,aeromap_uid_list) #.returnValue()

    def print_values(self):
        print("Print!  ------")
        for var in self.var_list:
            print(var.get())
        print("------------")


class CEASIOMpyGUI:
    def __init__(self, master):

        # GUI =============
        self.master = master
        self.master.title("CESAIOMpy Settings GUI")
        self.master.geometry("600x600+500+300")

        self.tabs = ttk.Notebook(self.master)
        self.tabs.pack(side=tk.TOP,fill='both')
        self.tabs.pack(expand=1, fill='both')


        # CPACS =============

        MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
        cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'


        self.tixi = open_tixi(cpacs_path)


        # Generate Tab =============
        module_name = 'PyTornado'
        tab1 = AutoTab(self.tabs,self.tixi, module_name)

        module_name = 'SkinFriction'
        tab2 = AutoTab(self.tabs,self.tixi, module_name)


        # General button =============
        self.greet_button = tk.Button(self.master, text="Do things", command=self.greet)
        self.greet_button.pack(side= tk.LEFT)

        self.close_button = tk.Button(self.master, text="Close", command=self.save_quit)
        self.close_button.pack(side=tk.RIGHT)

    def greet(self):
        print("Things have been done!")

    def save_quit(self):
        cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'
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

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)


    # Call Tkinter Class
    root = tk.Tk()
    my_gui = CEASIOMpyGUI(root)
    root.mainloop()

# Inspierd from https://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
