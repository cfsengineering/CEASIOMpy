"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Settings modifictions GUI for CEASIOMpy

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-09-05
| Last modifiction: 2020-04-24

TODO:

    * Add "mouse over" for description
    * Add other function to 'AeroMap Edition'
    * messagebox and error detection could be improved

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import re
import os

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apm
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

import ceasiompy.utils.moduleinterfaces as mif

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#==============================================================================
#   CLASSES
#==============================================================================

# Not use for now, but could be useful
# class ListBoxChoice(object):
#     def __init__(self, tab, tixi, list=[]):
#
#         self.selected_item = None
#
#         self.tab = tab
#         self.tixi = tixi
#         self.list = list[:]
#
#         self.listBox = tk.Listbox(self.tab, selectmode=tk.SINGLE)
#         self.listBox.grid(column=2, row=10)
#         self.list.sort()
#         for item in self.list:
#             self.listBox.insert(tk.END, item)
#
#         self.chooseButton = tk.Button(self.tab, text='Select', command=self._select)
#         self.chooseButton.grid(column=2, row=11)
#
#         self.cancelButton = tk.Button(self.tab, text='Cancel', command=self._cancel)
#         self.cancelButton.grid(column=3, row=11)
#
#     def _select(self, event=None):
#         try:
#             firstIndex = self.listBox.curselection()[0]
#             self.selected_item = [self.listBox.get(i) for i in self.listBox.curselection()]
#         except IndexError:
#             self.selected_item = None
#
#     def _cancel(self, event=None):
#         self.listBox.selection_clear(0, tk.END)
#
#     # Do we need that?
#     def returnValue(self):
#         self.tab.wait_window()
#         return self.selected_item


class AeroMapTab:
    """ Class to create the AeroMap tab from the infomation in cpacs file. """

    def __init__(self, tabs, tixi):
        """AeroMapTab class

        Args:
            tabs (TODO): TODO
            tixi (handle): Tixi handle
        """

        self.tabs = tabs
        self.tixi = tixi
        row_pos = 0

        self.aerotab = tk.Frame(self.tabs, borderwidth=1)
        tabs.add(self.aerotab, text='AeroMaps')

        aeromap_uid_list = apm.get_aeromap_uid_list(tixi)

        self.selected_list = []
        self.list = aeromap_uid_list

        tk.Label(self.aerotab, text='Existing AeroMaps').grid(column=0, row=row_pos)
        row_pos += 1

        self.listBox = tk.Listbox(self.aerotab, selectmode=tk.SINGLE)
        item_count = len(self.list)
        self.listBox.grid(column=0, row=row_pos, columnspan=3,rowspan=item_count, sticky= tk.W, padx=5, pady=5)
        self.list.sort()
        for item in self.list:
            self.listBox.insert(tk.END, item)
        row_pos += (item_count + 1)

        importButton = tk.Button(self.aerotab, text='Import CSV', command=self._import_csv)
        importButton.grid(column=0, row=row_pos)
        row_pos += 1

        exportButton = tk.Button(self.aerotab, text='Export CSV', command=self._export_csv)
        exportButton.grid(column=0, row=row_pos)
        row_pos += 1

        # updateButton = tk.Button(self.aerotab, text='Update', command=self._update)
        # updateButton.grid(column=0, row=row_pos)
        # row_pos += 1

        deleteButton = tk.Button(self.aerotab, text='Delete', command=self._delete)
        deleteButton.grid(column=0, row=row_pos)
        row_pos += 1


    def _import_csv(self, event=None):
        template_csv_dir = os.path.join(MODULE_DIR,'..','..','test','AeroMaps')
        csv_path = self.filename = filedialog.askopenfilename(initialdir = template_csv_dir, title = "Select a CSV file" )
        new_aeromap_uid = os.path.splitext(os.path.basename(csv_path))[0]
        apm.aeromap_from_csv(self.tixi, new_aeromap_uid, csv_path)
        self.listBox.selection_clear(0, tk.END)

        self._update()

    def _export_csv(self, event=None):
        aeromap_uid_list = [self.listBox.get(i) for i in self.listBox.curselection()]
        csv_path = self.filename = filedialog.asksaveasfilename(initialdir = MODULE_DIR, title = "Save CSV file", defaultextension=".csv")
        apm.aeromap_to_csv(self.tixi, aeromap_uid_list[0], csv_path)
        self.listBox.selection_clear(0, tk.END)

    def _update(self, event=None):
        self.list = apm.get_aeromap_uid_list(self.tixi)
        self.list.sort()
        self.listBox.delete(0, tk.END)
        for item in self.list:
            self.listBox.insert(tk.END, item)

    def _delete(self, event=None):
        firstIndex = self.listBox.curselection()[0]
        self.selected_list = [self.listBox.get(i) for i in self.listBox.curselection()]
        aeromap_uid = self.selected_list[0]
        apm.delete_aeromap(self.tixi,aeromap_uid)
        self._update()

    # def _modify_name(self, event = None):
        #TODO

    def returnValue(self):
        self.master.wait_window()
        return self.selected_list


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

        self.module_name = module_name
        self.tabs = tabs
        self.tixi = tixi
        self.tab = tk.Frame(tabs, borderwidth=1)
        tabs.add(self.tab, text=module_name)

        # Get GUI dict from specs
        specs = mif.get_specs_for_module(module_name)

        self.gui_dict = specs.cpacs_inout.get_gui_dict()

        #canvas has replaced self.tab in the following lines
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
            if (name is not '__AEROMAP_SELECTION' and name is not '__AEROMAP_CHECHBOX'):
                self.name_label = tk.Label(parent, text= name)
                self.name_label.grid(column=0, row=row_pos, sticky= tk.W, padx=5, pady=5)

            # Type and Value
            if dtype is bool:
                self.var_dict[key] = tk.BooleanVar()
                value = cpsf.get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key].set(value)
                bool_entry = tk.Checkbutton(parent, text='', variable=self.var_dict[key])
                bool_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is int:
                value = cpsf.get_value_or_default(self.tixi, xpath, def_value)
                self.var_dict[key] = tk.IntVar()
                self.var_dict[key].set(int(value))
                value_entry = tk.Entry(parent, bd=2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is float:
                value = cpsf.get_value_or_default(self.tixi, xpath, def_value)
                self.var_dict[key] = tk.DoubleVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, bd=2, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

            elif dtype is 'pathtype':

                value = cpsf.get_value_or_default(self.tixi,xpath,def_value)
                self.var_dict[key] = tk.StringVar()
                self.var_dict[key].set(value)
                value_entry = tk.Entry(parent, textvariable=self.var_dict[key])
                value_entry.grid(column=1, row=row_pos, padx=5, pady=5)

                self.key = key
                self.browse_button = tk.Button(parent, text="Browse", command=self._browse_file)
                self.browse_button.grid(column=2, row=row_pos, padx=5, pady=5)


            elif dtype is list:
                if name == '__AEROMAP_SELECTION':

                    # Get the list of all AeroMaps
                    self.aeromap_uid_list = apm.get_aeromap_uid_list(self.tixi)

                    # Try to get the pre-selected AeroMap from the xpath
                    try:
                        selected_aeromap = cpsf.get_value(self.tixi,xpath)
                        selected_aeromap_index = self.aeromap_uid_list.index(selected_aeromap)
                    except:
                        selected_aeromap = ''
                        selected_aeromap_index = 0

                    self.labelframe = tk.LabelFrame(parent, text='Choose an AeroMap')
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky=tk.W, padx=5, pady=5)

                    # The Combobox is directly use as the varaible
                    self.var_dict[key] = ttk.Combobox(self.labelframe, values=self.aeromap_uid_list)
                    self.var_dict[key].current(selected_aeromap_index)
                    self.var_dict[key].grid(column=1, row=row_pos, padx=5, pady=5)


                elif name == '__AEROMAP_CHECHBOX':

                    # Just to find back the name when data are saved
                    self.var_dict[key] = None
                    # __AEROMAP_CHECHBOX is a bit different, data are saved in their own dictionary
                    self.aeromap_var_dict = {}

                    # Get the list of all AeroMaps
                    self.aeromap_uid_list = apm.get_aeromap_uid_list(self.tixi)
                    self.labelframe = tk.LabelFrame(parent, text='Selecte AeroMap(s)')
                    self.labelframe.grid(column=0, row=row_pos, columnspan=3, sticky=tk.W, padx=5, pady=5)

                    # Try to get pre-selected AeroMaps from the xpath
                    try:
                        selected_aeromap = cpsf.get_string_vector(self.tixi,xpath)
                    except:
                        selected_aeromap = ''

                    # Create one checkbox for each AeroMap
                    for aeromap in self.aeromap_uid_list:
                        self.aeromap_var_dict[aeromap] = tk.BooleanVar()

                        #if aeromap in selected_aeromap:
                        # For now, set all to True
                        self.aeromap_var_dict[aeromap].set(True)

                        aeromap_entry = tk.Checkbutton(self.labelframe,text=aeromap,variable=self.aeromap_var_dict[aeromap])
                        aeromap_entry.pack()#side=tk.TOP, anchor='w')

                else: # Other kind of list (not aeroMap)

                    # 'def_value' will be the list of possibilies in this case

                    # Try to get the pre-selected AeroMap from the xpath
                    try: # TODO Should be retested...
                        selected_value = cpsf.get_value(self.tixi,xpath)
                        selected_value_index = def_value.index(selected_value)
                    except:
                        selected_value = ''
                        selected_value_index = 0

                    # The Combobox is directly use as the varaible
                    self.var_dict[key] = ttk.Combobox(parent, values=def_value)
                    self.var_dict[key].current(selected_value_index)
                    self.var_dict[key].grid(column=1, row=row_pos, padx=5, pady=5)

            else:
                value = cpsf.get_value_or_default(self.tixi,xpath,def_value)
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
        # aeromap_uid_list = apm.get_aeromap_uid_list(self.tixi)
        # self.listbox1 = ListBoxChoice(self.tab,self.tixi,aeromap_uid_list) #.returnValue()

    def _browse_file(self):

        self.filename = filedialog.askopenfilename(initialdir = MODULE_DIR, title = "Select A File" )
        self.var_dict[self.key].set(self.filename)


class SettingGUI(tk.Frame):
    """Notre fenêtre principale.
    Tous les widgets sont stockés comme attributs de cette fenêtre."""

    def __init__(self, master, cpacs_path, cpacs_out_path, submodule_list, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.pack(fill=tk.BOTH)

        self.submodule_list = submodule_list
        self.cpacs_out_path = cpacs_out_path

        # Notebook for tabs
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=0, column=0, columnspan=3)  #pack()#expand=1, side=tk.LEFT)

        self.tixi = cpsf.open_tixi(cpacs_path)

        if len(apm.get_aeromap_uid_list(self.tixi)) == 0 :
            log.warning('No AeroMap in this CPACS file')
            aeromap_uid = 'New_AeroMap'
            description = 'AeroMap create by SettingGUI'
            apm.create_empty_aeromap(self.tixi, aeromap_uid, description)

        # Generate AeroMaps Edition tab
        aeromap_tap = AeroMapTab(self.tabs, self.tixi)

        # Generate Auto Tab =============
        self.tab_list = []
        self._update_all()

        # General button
        self.update_button = tk.Button(self, text='Update', command=self._update_all)
        self.update_button.grid(row=1, column=1,sticky='E')
        self.close_button = tk.Button(self, text='Save & Quit', command=self._save_quit)
        self.close_button.grid(row=1, column=2,sticky='W')



    def _update_all(self):

        # Remove existing AutoTab
        if len(self.tab_list) > 0 :
            for i in range(len(self.tab_list)):
                self.tabs.forget(1)
            self.tab_list = []

        # Generate new Auto Tab
        for module_name in self.submodule_list:

            specs = mif.get_specs_for_module(module_name)
            if specs is None:  # Specs does not exist
                continue
            self.gui_dict = specs.cpacs_inout.get_gui_dict()
            if not self.gui_dict:  # Empty dict --> nothing to do
                continue

            tab = AutoTab(self.tabs, self.tixi, module_name)
            self.tab_list.append(tab)


    def _save_quit(self):

        # Iterate over all existing tabs
        for tab in self.tab_list:
            # Iterate in Variable dictionary of each tab
            for key, var in tab.var_dict.items():
                # Get the XPath from the GUI setting dictionary and crate a branch
                name = tab.gui_dict[key][0]
                xpath = tab.gui_dict[key][4]
                cpsf.create_branch(self.tixi,xpath)
                if name == '__AEROMAP_CHECHBOX':
                    aeromap_uid_list_str = ''
                    for aeromap_uid, aeromap_bool in tab.aeromap_var_dict.items():
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

        cpsf.close_tixi(self.tixi, self.cpacs_out_path)

        self.quit()


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


def create_settings_gui(cpacs_path, cpacs_out_path, submodule_list):
    """ Create a GUI with Tkinter to fill CEASIOMpy settings

    Args:
        cpacs_path (str): Path to the CPACS file
        cpacs_out_path (str): Path to the output CPACS file
        submodule_list (list): List of module to inclue in the GUI

    """

    root = tk.Tk()
    root.title('CEASIOMpy Settings GUI')
    root.geometry('600x900+400+50')
    my_setting_gui = SettingGUI(root, cpacs_path, cpacs_out_path, submodule_list)
    my_setting_gui.mainloop()
    root.iconify()
    root.destroy()


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    # Call the function which check if imputs are well define
    mif.check_cpacs_input_requirements(cpacs_path)

    # Get the complete submodule
    submodule_list = mif.get_submodule_list()

    create_settings_gui(cpacs_path, cpacs_out_path, submodule_list)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
