"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Tool to create workflow for CEASIOMpy with or without GUI

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2020-04-21

TODO:

    * Modifiy Opimisation Tab to restrict selection to only Module to run
    * Add logs in this file

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_submodule_list
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH, WKDIR_PATH
from ceasiompy.utils.workflowclasses import Workflow

log = get_logger()

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


class Tab(tk.Frame):
    """Class to create tab in the WorkflowCreator GUI"""

    def __init__(self, master, name, **kwargs):

        tk.Frame.__init__(self, master, **kwargs)

        self.name = name

        # Get list of available modules
        self.modules_list = get_submodule_list()
        self.modules_list.sort()

        self.modules_list.remove("SettingsGUI")
        self.modules_list.insert(0, "SettingsGUI")

        self.modules_list.remove("CPACSUpdater")
        self.modules_list.remove("WorkflowCreator")
        self.modules_list.remove("utils")

        self.selected_list = []

        row_pos = 0

        if name == "Optimisation":

            label_optim = tk.Label(self, text="Optimisation method")
            label_optim.grid(column=0, row=0, columnspan=1, pady=10)

            # The Combobox is directly use as the variable
            optim_choice = ["None", "DOE", "OPTIM"]
            self.optim_choice_CB = ttk.Combobox(self, values=optim_choice, width=15)
            self.optim_choice_CB.grid(column=4, row=row_pos)
            row_pos += 1

        # ListBox with all available modules
        tk.Label(self, text="Available modules").grid(column=0, row=row_pos, pady=5)
        self.LB_modules = tk.Listbox(
            self, selectmode=tk.SINGLE, width=25, height=len(self.modules_list)
        )
        item_count = len(self.modules_list)
        self.LB_modules.grid(column=0, row=row_pos + 1, columnspan=3, rowspan=15, padx=10, pady=3)
        for item in self.modules_list:
            self.LB_modules.insert(tk.END, item)

        # Button
        addButton = tk.Button(self, text="   Add >   ", command=self._add)
        addButton.grid(column=4, row=row_pos + 1)
        removeButton = tk.Button(self, text="< Remove", command=self._remove)
        removeButton.grid(column=4, row=row_pos + 2)
        upButton = tk.Button(self, text="    Up  ^   ", command=self._up)
        upButton.grid(column=4, row=row_pos + 3)
        downButton = tk.Button(self, text="  Down v  ", command=self._down)
        downButton.grid(column=4, row=row_pos + 4)

        # ListBox with all selected modules
        tk.Label(self, text="Selected modules").grid(column=5, row=row_pos)
        self.LB_selected = tk.Listbox(
            self, selectmode=tk.SINGLE, width=25, height=len(self.modules_list)
        )
        self.LB_selected.grid(column=5, row=row_pos + 1, columnspan=3, rowspan=15, padx=10, pady=3)
        for item in self.selected_list:
            self.LB_selected.insert(tk.END, item)
            row_pos += item_count + 1

    def _add(self, event=None):
        """Function of the button add: to pass a module from Available module
        list to Selected module list"""

        try:
            select_item = [self.LB_modules.get(i) for i in self.LB_modules.curselection()]
            self.selected_list.append(select_item[0])
            self.LB_selected.insert(tk.END, select_item)
        except IndexError:
            self.selected_item = None

    def _remove(self, event=None):
        """Function of the button remove: to remove a module from the Selected
        module list"""

        sel = self.LB_selected.curselection()
        for index in sel[::-1]:
            self.LB_selected.delete(index)

    def _up(self, event=None):
        """Function of the button up: to move upward a module in the Selected
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
        """Function of the button down: to move downward a module in the
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

        self.workflow = Workflow()

        space_label = tk.Label(self, text=" ")
        space_label.grid(column=0, row=0)

        # Input Working directory
        self.label = tk.Label(self, text="  Working Directory")
        self.label.grid(column=0, row=1)

        self.wkdir_path_var = tk.StringVar()
        self.wkdir_path_var.set(self.workflow.working_dir)
        value_entry = tk.Entry(self, textvariable=self.wkdir_path_var, width=45)
        value_entry.grid(column=1, row=1)

        self.browse_button = tk.Button(self, text="Browse", command=self._browse_dir)
        self.browse_button.grid(column=2, row=1, pady=5)

        # Input CPACS file
        self.label = tk.Label(self, text="  Input CPACS file")
        self.label.grid(column=0, row=2)

        self.path_var = tk.StringVar()
        self.path_var.set(self.workflow.cpacs_in)
        value_entry = tk.Entry(self, textvariable=self.path_var, width=45)
        value_entry.grid(column=1, row=2)

        self.browse_button = tk.Button(self, text="Browse", command=self._browse_file)
        self.browse_button.grid(column=2, row=2, pady=5)

        # Notebook for tabs
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(column=0, row=3, columnspan=3, padx=10, pady=10)

        self.TabModToRun = Tab(self, "Module to run")
        self.TabOptim = Tab(self, "Optimisation")

        self.tabs.add(self.TabModToRun, text=self.TabModToRun.name)
        self.tabs.add(self.TabOptim, text=self.TabOptim.name)

        # General buttons
        self.close_button = tk.Button(self, text="Save & Quit", command=self._save_quit)
        self.close_button.grid(column=2, row=4)

    def _browse_file(self):

        self.filename = filedialog.askopenfilename(
            initialdir=CPACS_FILES_PATH, title="Select a CPACS file"
        )
        self.path_var.set(self.filename)

    def _browse_dir(self):

        self.wkdir = filedialog.askdirectory(
            initialdir=WKDIR_PATH, title="Select a Working Directory"
        )
        self.wkdir_path_var.set(self.wkdir)

    def _save_quit(self):

        self.workflow.optim_method = self.TabOptim.optim_choice_CB.get()
        if not self.workflow.optim_method:
            self.workflow.optim_method = "None"

        self.workflow.modules_list = [
            item[0] for item in self.TabModToRun.LB_selected.get(0, tk.END)
        ]
        self.workflow.module_optim = [item[0] for item in self.TabOptim.LB_selected.get(0, tk.END)]
        if not self.workflow.module_optim:
            self.workflow.module_optim = ["NO"] * len(self.workflow.modules_list)

        # CPACS file
        if self.path_var.get() == "":
            messagebox.showerror("ValueError", "Yon must select an input CPACS file!")
            raise TypeError("No CPACS file has been define !")

        self.workflow.cpacs_in = Path(self.path_var.get())

        if self.wkdir_path_var.get() == "":
            messagebox.showerror("ValueError", "Yon must select a Woking Directory!")
            raise TypeError("No Working directory has been define !")

        # Working directory
        self.workflow.working_dir = Path(self.wkdir_path_var.get())

        if not self.workflow.working_dir.exists():
            self.workflow.working_dir.mkdir()

        if list(self.workflow.working_dir.glob("*.cfg")):

            answer = messagebox.askokcancel(
                title="Confirmation",
                message="Be careful a CEASIOMpy configuration file (.cfg) already exist in this"
                " working directory, it will be overwritten!",
                icon=messagebox.WARNING,
            )

            if not answer:
                return

        self.quit()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def create_wf_gui():
    """Create a GUI with Tkinter to fill the workflow to run."""

    root = tk.Tk()
    root.title("Workflow Creator")
    root.geometry("730x750+400+150")
    gui = WorkFlowGUI()
    gui.mainloop()
    workflow = gui.workflow

    root.iconify()  # Not super solution but only way to make it close on Mac
    root.destroy()

    return workflow


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute")
