"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Settings modifictions GUI for CEASIOMpy

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-09-05
| Last modifiction: 2019-09-12

TODO:

    * Add "mouse over" for description
    * Add 'AeroMap Edition'
    * Fix  'get_value' for boolean
    * messagebox and error detection could be improved
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import re
import os

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch, copy_branch, add_uid,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector,get_float_vector,  \
                                           add_string_vector,get_string_vector,\
                                           aircraft_name

from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                         create_empty_aeromap, check_aeromap,  \
                                         save_parameters, save_coefficients,   \
                                         get_aeromap, merge_aeroMap,           \
                                         aeromap_from_csv, aeromap_to_csv,     \
                                         delete_aeromap

import ceasiompy.utils.moduleinterfaces as mif




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
        """Tab class

        Note:
            A tab will only be created if the module actually has
            any settings which are to be shown

        Args:
            tabs (TODO): TODO
            tixi (handle): Tixi handle
            module_name (str): String of the module name for which a tab is to be created
        """

        self.var_dict = {}
        self.group_dict = {}

        # ----- Safely try to get the specs module -----
        specs = mif.get_specs_for_module(module_name)
        if specs is None:  # Specs does not exist
            return
        self.gui_dict = specs.cpacs_inout.get_gui_dict()
        if not self.gui_dict:  # Empty dict --> nothing to do
            return

        self.module_name = module_name
        self.tabs = tabs
        self.tixi = tixi
        self.tab = tk.Frame(tabs, borderwidth=1)
        tabs.add(self.tab, text=module_name)

        space_label = tk.Label(self.tab, text=' ')
        space_label.grid(column=0, row=0)

        row_pos = 1

        for key, (name, def_value, dtype, unit, xpath, description, group) in self.gui_dict.items():
            # Create a LabelFrame for new groupe
            if group:
                if not group in self.group_dict:
                    self.labelframe = tk.LabelFrame(self.tab, text=group)
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3,sticky= tk.W, padx=5, pady=5)
                    self.group_dict[group] = self.labelframe
                parent = self.group_dict[group]
            else:  # if not a group, use tab as parent
                parent = self.tab

            # Name label for variable
            self.name_label = tk.Label(parent, text= name)
            self.name_label.grid(column=0, row=row_pos, sticky= tk.W, padx=5, pady=5)

            # Type and Value
            if dtype is bool:
                self.var_dict[key] = tk.BooleanVar()
                # TODO: NOT working because get_value not recognize Boolean type
                # value = get_value_or_default(self.tixi,xpath,def_value)
                value = def_value
                self.var_dict[key].set(value)
                bool_entry = tk.Checkbutton(parent, text='', variable=self.var_dict[key])
                bool_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is int:
                value = get_value_or_default(self.tixi, xpath, def_value)
                self.var_dict[key] = tk.IntVar()
                self.var_dict[key].set(int(value))
                value_entry = tk.Entry(parent, bd=2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is float:
                value = get_value_or_default(self.tixi, xpath, def_value)
                self.var_dict[key] = tk.DoubleVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, bd=2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is list:
                if name == '__AEROMAP_SELECTION':

                    # Get the list of all AeroMaps
                    aeromap_uid_list = get_aeromap_uid_list(self.tixi)

                    # Try to get the pre-selected AeroMap from the xpath
                    try:
                        selected_aeromap = get_value(self.tixi,xpath)
                        selected_aeromap_index = aeromap_uid_list.index(selected_aeromap)
                    except:
                        selected_aeromap = ''
                        selected_aeromap_index = 0

                    self.labelframe = tk.LabelFrame(parent, text="Choose an AeroMap")
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky=tk.W, padx=5, pady=5)

                    # The Combobox is directly use as the varaible
                    self.var_dict[key] = ttk.Combobox(self.labelframe, values=aeromap_uid_list)
                    self.var_dict[key].current(selected_aeromap_index)
                    self.var_dict[key].grid(column=1, row=row_pos, padx=5, pady=5)

                elif name == '__AEROMAP_CHECHBOX':

                    # Just to find back the name when data are saved
                    self.var_dict[key] = None
                    # __AEROMAP_CHECHBOX is a bit different, data are saved in their own dictionary
                    self.aeromap_var_dict = {}

                    # Get the list of all AeroMaps
                    aeromap_uid_list = get_aeromap_uid_list(self.tixi)
                    self.labelframe = tk.LabelFrame(parent, text="Selecte AeroMap(s)")
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky=tk.W, padx=5, pady=5)

                    # Try to get pre-selected AeroMaps from the xpath
                    try:
                        selected_aeromap = get_string_vector(self.tixi,xpath)
                    except:
                        selected_aeromap = ''

                    # Create one checkbox for each AeroMap
                    for aeromap in aeromap_uid_list:
                        self.aeromap_var_dict[aeromap] = tk.BooleanVar()
                        if aeromap in selected_aeromap:
                            self.aeromap_var_dict[aeromap].set(True)
                        aeromap_entry = tk.Checkbutton(self.labelframe,text=aeromap,variable=self.aeromap_var_dict[aeromap])
                        aeromap_entry.pack(side=tk.TOP, anchor='w')

                else: # Other kind of list (not aeroMap)

                    # 'def_value' will be the list of possibilies in this case

                    # Try to get the pre-selected AeroMap from the xpath
                    try:
                        selected_value = get_value(self.tixi,xpath)
                        selected_value_index = aeromap_uid_list.index(selected_value)
                    except:
                        selected_value = ''
                        selected_value_index = 0


                    # The Combobox is directly use as the varaible
                    self.var_dict[key] = ttk.Combobox(parent, values=def_value)
                    self.var_dict[key].current(selected_value_index)
                    self.var_dict[key].grid(column=1, row=row_pos, padx=5, pady=5)

            else:
                value = get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key] = tk.StringVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            # Units
            if unit and unit != '1':
                unit_label = tk.Label(parent, text=pretty_unit(unit))
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
        self.master.geometry("500x750+500+200")

        self.tabs = ttk.Notebook(self.master)
        self.tabs.pack(side=tk.TOP, fill='both')
        self.tabs.pack(expand=1, fill='both')

        # CPACS =============
        self.tixi = open_tixi(cpacs_path)

        if len(get_aeromap_uid_list(self.tixi)) == 0 :
            log.warning('No AeroMap in this CPACS file')
            aeromap_uid = 'New_AeroMap'
            description = 'AeroMap create by SettingGUI'
            create_empty_aeromap(self.tixi, aeromap_uid, description)

        # Generate Tab =============
        # Get a list of ALL CESAIOMpy submodules
        self.tab_list = []
        for module_name in mif.get_submodule_list():
            tab = AutoTab(self.tabs, self.tixi, module_name)
            self.tab_list.append(tab)

        # tab = AutoTab(self.tabs, self.tixi, 'PyTornado')
        # self.tab_list.append(tab)
        # tab = AutoTab(self.tabs, self.tixi, 'SkinFriction')
        # self.tab_list.append(tab)

        # General button =============
        self.close_button = tk.Button(self.master, text="Save & Quit", command=self.save_quit)
        self.close_button.pack(side=tk.RIGHT)


    def save_quit(self):

        # Iterate over all existing tabs
        for tab in self.tab_list:
            # Iterate in Variable dictionary of each tab
            for key, var in tab.var_dict.items():
                # Get the XPath from the GUI setting dictionary and crate a branch
                name = tab.gui_dict[key][0]
                xpath = tab.gui_dict[key][4]
                create_branch(self.tixi,xpath)
                if name == '__AEROMAP_CHECHBOX':
                    aeromap_uid_list_str = ''
                    for aeromap_uid, aeromap_bool in tab.aeromap_var_dict.items():
                        print('for loop')
                        if aeromap_bool.get():
                            aeromap_uid_list_str += aeromap_uid + ';'
                    if aeromap_uid_list_str == '':
                        messagebox.showerror('ValueError', 'In the Tab "' + \
                                       tab.module_name + '", no value has been selected for "' + \
                                       name + '" ')
                        raise TypeError('No value has been selected for ' + name + ' !')
                    self.tixi.updateTextElement(xpath, aeromap_uid_list_str)

                # '__AEROMAP_SELECTION' and list Type value will be saved as any other variable
                else:
                    if str(var.get()) == '':
                        # Not working when it expect an 'int' or a 'float'
                        messagebox.showerror('ValueError', 'In the Tab "' + \
                                       tab.module_name + '", no value has been entered for "' + \
                                       name + '" ')
                        raise TypeError('No value has been entered for ' + name + ' !')

                    try:
                        self.tixi.updateTextElement(xpath, str(var.get()))
                    except:

                        messagebox.showerror('TypeError', 'In the Tab "' + \
                                       tab.module_name + '", the value "' + \
                                       name + '" has not the correct type!')
                        raise TypeError(name + ' has not the correct type!')

        close_tixi(self.tixi, cpacs_out_path)
        self.master.quit()


#==============================================================================
#   FUNCTIONS
#==============================================================================

def pretty_unit(unit_string):
    """Prettify a unit string

    Args:
        unit_string (str): Unit string

    Returns:
        pretty_unit (str): Prettified unit string
    """

    unit_string = pretty_exponent(unit_string)
    unit_string = wrap_in_brackets(unit_string, space=1)
    return unit_string


def pretty_exponent(string):
    """Prettify a numeric exponent in a string

    Args:
        string (str): String to prettify

    returns:
        pretty_string (str): Prettified string
    """

    # TODO: to be improved...

    def make_exp(string):
        # There must be a better way...
        replace_table = ('0⁰', '1¹', '2²', '3³', '4⁴', '5⁵', '6⁶', '7⁷', '8⁸', '9⁹')
        for sub in replace_table:
            string = string.replace(sub[0], sub[1])
        return string

    number_exp = re.compile('\^[0-9]*')
    matches = number_exp.findall(string)

    for match in matches:
        string = string.replace(match, make_exp(match[1:]))

    return string


def wrap_in_brackets(string, brackets='[]', space=0):
    """Add enclosing square brackets to a string if not yet existing

    Examples:

    >>> wrap_in_brackets("test")
    '[test]'
    >>> wrap_in_brackets("[m/s]")
    '[m/s]'
    >>> wrap_in_brackets("[m/s")
    '[m/s]'
    >>> wrap_in_brackets("m/s")
    '[m/s]'

    Args:
        string (str): String to wrap
        brackets (str): String of length 2 with opening/closing bracket
        space (int): Number of spaces between bracket and string
    """

    # Cut leading/trailing brackets
    while string.startswith(brackets[0]):
        string = string[1:]
    while string.endswith(brackets[1]):
        string = string[:-1]

    return f"[{' '*space}{string}{' '*space}]"


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    # Call the function which check if imputs are well define
    mif.check_cpacs_input_requirements(cpacs_path)

    # Call Tkinter Class
    root = tk.Tk()
    my_gui = CEASIOMpyGUI(root, cpacs_path, cpacs_out_path)
    root.mainloop()

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')



# Old code to delete when everything Works

# elif dtype is list:
#     if 'AeroMap' in name:
#         self.var_dict[key] = 'AeroMapListType'
#         aeromap_uid_list = get_aeromap_uid_list(self.tixi)
#         self.labelframe = tk.LabelFrame(parent, text="AeroMap to calculate")
#         self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky=tk.W, padx=5, pady=5)
#         self.aeromap_var_dict = {}
#
#         # Pre selected aeromap from the coresponding CPACS node
#         try:
#             selected_aeromap = get_string_vector(self.tixi,xpath)
#         except:
#             selected_aeromap = ''
#
#         for aeromap in aeromap_uid_list:
#             self.aeromap_var_dict[aeromap] = tk.BooleanVar()
#
#             if aeromap in selected_aeromap:
#                 self.aeromap_var_dict[aeromap].set(True)
#             aeromap_entry = tk.Checkbutton(self.labelframe,text=aeromap,variable=self.aeromap_var_dict[aeromap])
#             aeromap_entry.pack(side=tk.TOP, anchor='w')
#     else: # if it's a list of someting else than aeromap
#         if def_value == '__all_aeromaps':
#             value_list = get_aeromap_uid_list(self.tixi)
#         else:
#             value_list = def_value
#         self.combobox = ttk.Combobox(parent, values=value_list)
#         self.combobox.grid(column=1, row=row_pos, padx=5, pady=5)
