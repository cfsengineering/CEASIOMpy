"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Module interfaces functions to deal with CPACS input and output

Python version: >=3.6

| Author : Aaron Dettmann
| Creation: 2019-08-06
| Last modifiction: 2019-09-10

TODO:

    * Add somefunction for input/output files
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
from glob import glob

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi

# Shortcut for XPath definition
CEASIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'
AIRCRAFT_XPATH = '/cpacs/vehicles/aircraft'


#==============================================================================
#   CLASSES
#==============================================================================

class CPACSRequirementError(Exception):
    pass


class _Entry:

    # TODO: Use a dict instead of class?

    ONLY_INPUT = [
        'default_value',
        'gui',
        'gui_group',
        'gui_name',
    ]

    def __init__(
        self, *,
        var_name='',
        var_type=None,
        default_value=None,
        unit='1',
        descr='',
        cpacs_path='',
        gui=False,
        gui_name='',
        gui_group=None
    ):
        """Template for an entry which describes a module input or output

        Args:
            var_name (str): Variable name as used in the module code
            var_type (type): Type of the expected input or output variable
            default_value (any): Default input value
            unit (str): Unit of the required value, e.g. 'm/s'
            descr (str): Description of the input or output data
            cpacs_path (str): CPACS node path
            gui (bool): 'True' if entry should appear in GUI
            gui_name (str): GUI name
            gui_group (str): Group name for GUI generation
        """

        # ----- General information -----
        self.var_name = var_name
        self.var_type = var_type
        self.default_value = default_value
        self.unit = unit
        self.descr = descr
        self.cpacs_path = cpacs_path

        # ----- GUI specific -----
        self.gui = gui
        self.gui_name = gui_name
        self.gui_group = gui_group


class CPACSInOut:

    def __init__(self):
        """
        Class summarising the input and output data

        Attributes:
            inputs (list): List of CPACS inputs
            outputs (list): List of CPACS output
        """

        self.inputs = []
        self.outputs = []

    def add_input(self, **kwargs):
        """Add a new entry to the inputs list"""

        entry = _Entry(**kwargs)
        self.inputs.append(entry)

    def add_output(self, **kwargs):
        """Add a new entry to the outputs list"""

        for entry_name in _Entry.ONLY_INPUT:
            if kwargs.get(entry_name, None) is not None:
                raise ValueError(f"Output '{entry_name}' must be None")

        entry = _Entry(**kwargs)
        self.outputs.append(entry)

    def get_gui_dict(self):
        """Return a dictionary which can be processed by the GUI engine"""

        # TODO: process groups

        gui_settings_dict = {}
        for entry in self.inputs:
            if not entry.gui:
                continue

            gui_settings_dict[entry.gui_name] = (
                entry.default_value,
                entry.var_type,
                entry.unit,
                entry.cpacs_path,
                entry.descr,
                entry.gui_group,
            )

        return gui_settings_dict


#==============================================================================
#   FUNCTIONS
#==============================================================================

def check_cpacs_input_requirements(cpacs_file, cpacs_inout, module_file_name):
    """
    Check if the input CPACS file contains the required nodes
    """

    # log = get_logger(module_file_name.split('.')[0])

    required_inputs = cpacs_inout.inputs
    tixi = open_tixi(cpacs_file)

    missing_nodes = []
    for entry in required_inputs:
        if entry.default_value is not None:
            continue
        if tixi.checkElement(entry.cpacs_path) is False:
            missing_nodes.append(entry.cpacs_path)

    if missing_nodes:
        missing_str = ''
        for missing in missing_nodes:
            missing_str += '==> ' + missing + '\n'

        msg = f"CPACS path required but does not exist\n{missing_str}"
        # log.error(msg)
        raise CPACSRequirementError(msg)

    # TODO: close tixi handle?


def get_module_list():
    """
    Return a list of submodule in the CEASIOMpy module

    Returns:
        A list of module names (as strings)
    """

    import ceasiompy.__init__

    ignore_submods = [
        '__init__.py',
        '__version__.py',
        '__pycache__',
    ]

    # Path for main CEASIOMpy library
    lib_dir = os.path.dirname(ceasiompy.__init__.__file__)

    dirnames = glob(os.path.join(lib_dir, '*'))
    module_list = []
    for dirname in dirnames:
        submod_name = os.path.basename(dirname)
        if submod_name in ignore_submods:
            continue
        module_name = 'ceasiompy.' + submod_name
        module_list.append(module_name)

    return module_list


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute')

    # TODO: maybe add function to mange input/ouput, check double, write default /toolspecific ...
