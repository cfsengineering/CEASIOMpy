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

from glob import glob
import importlib
import os
import uuid
from pathlib import Path
import inspect

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi

# Shortcut for XPath definition
CEASIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'
AIRCRAFT_XPATH = '/cpacs/vehicles/aircraft'

MODNAME_TOP = 'ceasiompy'
MODNAME_SPECS = '__specs__'

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

            # Every GUI element is identified by a random key
            gui_settings_dict[str(uuid.uuid4())] = (
                entry.gui_name,
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

def check_cpacs_input_requirements(cpacs_file, *, submod_name=None, submodule_level=1, cpacs_inout=None):
    """ Check if the input CPACS file contains the required nodes

    Note:
        * The __specs__ file will be located based on the calling module
        * In most cases this function should be called simply as

        ==> check_cpacs_input_requirements(cpacs_file)

    Args:
        cpacs_file (str): Path to the CPACS file to check
        submod_name (str): Name of the submod_name (if None, determined from caller)
        submodule_level (int): Levels up where the CEASIOMpy submodule is located
        cpacs_inout (obj): CPACSInOut() instance

    Raises:
        CPACSRequirementError: If one or more paths are required by calling
                               module but not available in CPACS file
    """

    # log = get_logger(module_file_name.split('.')[0])

    if not isinstance(submodule_level, int) and submodule_level < 1:
        ValueError("'submodule_level' must be a positive integer")

    # If 'cpacs_inout' not provided by caller, we try to determine it
    if cpacs_inout is None:
        if submod_name is None:
            # Get the path of the caller submodule
            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            caller_module_path = os.path.dirname(os.path.abspath(mod.__file__))

            # Get the CEASIOM_XPATH submodule name
            parent_path, submod_name = os.path.split(caller_module_path)
            for _ in range(1, submodule_level):
                parent_path, submod_name = os.path.split(parent_path)

        # Load the submodule specifications
        specs_module = get_specs_for_module(submod_name, raise_error=True)
        cpacs_inout = specs_module.cpacs_inout

    tixi = open_tixi(cpacs_file)
    missing_nodes = []
    for entry in cpacs_inout.inputs:
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


def get_submodule_list():
    """Return a list of CEASIOMpy submodules (only submodule name)

    ['SkinFriction', 'PyTornado', ...]

    Returns:
        A list of submodule names (as strings)
    """

    import ceasiompy.__init__

    # Path for main CEASIOMpy library
    lib_dir = os.path.dirname(ceasiompy.__init__.__file__)

    dirnames = glob(os.path.join(lib_dir, '*'))
    submodule_list = []
    for dirname in dirnames:
        submod_name = os.path.basename(dirname)

        # Ignore "dunder"-files
        if submod_name.startswith('__'):
            continue

        submodule_list.append(submod_name)

    return submodule_list


def get_module_list():
    """Return a list of CEASIOMpy modules (full name)

    ['ceasiompy.SkinFriction', 'ceasiompy.PyTornado', ...]

    Returns:
        A list of module names (as strings)
    """

    module_list = []
    for submod_name in get_submodule_list():
        module_list.append('.'.join((MODNAME_TOP, submod_name)))
    return module_list


def get_specs_for_module(module_name, raise_error=False):
    """Return the __specs__ module for a CEASIOMpy module

    Args:
        module_name (str): name of the module as a string
        raise_error (bool): 'True' if error should be raised
                            if __specs__ does not exist
    """

    if not module_name.startswith('ceasiompy.'):
        module_name = '.'.join((MODNAME_TOP, module_name))

    try:
        specs = importlib.import_module('.'.join((module_name, MODNAME_SPECS)))
        return specs
    except ImportError:
        if raise_error:
            raise ImportError(f'{MODNAME_SPECS} module not found for {module_name}')
        return None


def get_all_module_specs():
    """Return a dictionary with module names (keys) and specs files (values)

    Note:
        * If the __specs__ module for a CEASIOMpy cannot
          be located the module will be None

    The dictionary has the form:

    {
        'SkinFriction': pytornado_specs_module,
        'PyTornado': pytornado_specs_module,
        'SomeModuleWithoutSpecsFile': None,
        ...
    }

    Returns:
        all_specs (dict): Dictionary containing all module specs
    """

    all_specs = {}
    for submod_name in get_submodule_list():
        specs = get_specs_for_module(submod_name, raise_error=False)
        all_specs[submod_name] = specs
    return all_specs


def find_missing_specs():
    """Return modules that do not have any __specs__ file

    Returns:
        missing (list): List with names of modules for which __specs__ file is missing
    """

    missing = []
    for modname, specs in get_all_module_specs().items():
        if specs is None:
            missing.append(modname)
    return missing

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute')

    # TODO: maybe add function to mange input/ouput, check double, write default /toolspecific ...
