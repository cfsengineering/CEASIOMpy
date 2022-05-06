"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Module interfaces functions to deal with CPACS input and output

Python version: >=3.7

| Author : Aaron Dettmann
| Creation: 2019-08-06

TODO:

    * Add somefunction for input/output files
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


import importlib
import inspect
import uuid
from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.paths import MODULES_DIR_PATH
from cpacspy.cpacsfunctions import create_branch, open_tixi

log = get_logger()

MODULE_DIR = Path(__file__).parent

MODNAME_TOP = "ceasiompy"
MODNAME_SPECS = "__specs__"

# =================================================================================================
#   CLASSES
# =================================================================================================


class CPACSRequirementError(Exception):
    pass


class _Entry:

    ONLY_INPUT = [
        "default_value",
        "gui",
        "gui_group",
        "gui_name",
    ]

    def __init__(
        self,
        *,
        var_name="",
        var_type=None,
        default_value=None,
        unit="1",
        descr="",
        xpath="",
        gui=False,
        gui_name="",
        gui_group=None,
    ):
        """Template for an entry which describes a module input or output

        Args:
            var_name        (str): Variable name as used in the module code
            var_type        (type): Type of the expected input or output variable
            default_value   (any): Default input value
            unit            (str): Unit of the required value, e.g. 'm/s'
            descr           (str): Description of the input or output data
            xpath           (str): CPACS node xpath
            gui             (bool): 'True' if entry should appear in GUI
            gui_name        (str): GUI name
            gui_group       (str): Group name for GUI generation
        """

        # General information
        self.var_name = var_name
        self.var_type = var_type
        self.default_value = default_value
        self.unit = unit
        self.descr = descr
        self.xpath = xpath

        # GUI specific
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
                entry.xpath,
                entry.descr,
                entry.gui_group,
            )

        return gui_settings_dict


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_module_path(module_name: str) -> Path:
    """Get the path to the module directory"""

    if module_name not in get_submodule_list():
        raise ValueError(f"Module '{module_name}' not found")

    return Path(MODULES_DIR_PATH, module_name)


def check_cpacs_input_requirements(
    cpacs_file, *, submod_name=None, submodule_level=1, cpacs_inout=None
):
    """Check if the input CPACS file contains the required nodes

    Note:
        * The __specs__ file will be located based on the calling module
        * In most cases this function should be called simply as

        ==> check_cpacs_input_requirements(cpacs_file)

    Args:
        cpacs_file (Path): Path to the CPACS file to check
        submod_name (str): Name of the submod_name (if None, determined from caller)
        submodule_level (int): Levels up where the CEASIOMpy submodule is located
        cpacs_inout (obj): CPACSInOut() instance

    Raises:
        CPACSRequirementError: If one or more paths are required by calling
                               module but not available in CPACS file
    """

    if not isinstance(submodule_level, int) and submodule_level < 1:
        ValueError("'submodule_level' must be a positive integer")

    # If 'cpacs_inout' not provided by caller, we try to determine it
    if cpacs_inout is None:
        if submod_name is None:
            # Get the path of the caller submodule
            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            caller_module_path = Path(mod.__file__).parent

            # Get the CEASIOM_XPATH submodule name
            submod_name = caller_module_path.name
            for _ in range(1, submodule_level):
                submod_name = caller_module_path.name

        # Load the submodule specifications
        specs_module = get_specs_for_module(submod_name, raise_error=True)
        cpacs_inout = specs_module.cpacs_inout

    tixi = open_tixi(str(cpacs_file))
    missing_nodes = []
    for entry in cpacs_inout.inputs:

        if entry.default_value is not None:
            continue
        if tixi.checkElement(entry.xpath) is False:
            missing_nodes.append(entry.xpath)

    if missing_nodes:
        for missing in missing_nodes:
            log.error("The following xpath cannot be found: " + missing)

        raise CPACSRequirementError("CPACS xpath(s) required but does not exist!")


def get_submodule_list():
    """Return a list of CEASIOMpy submodules (only submodule name)

    ['SkinFriction', 'PyTornado', ...]

    Returns:
        A list of submodule names (as strings)
    """

    submodule_list = []
    for module_dir in MODULES_DIR_PATH.iterdir():
        submod_name = module_dir.name

        # Ignore "dunder"-files and dot files
        if submod_name.startswith("__") or submod_name.startswith("."):
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
        module_list.append(".".join((MODNAME_TOP, submod_name)))
    return module_list


def get_toolinput_file_path(module_name):
    """Get the path to the ToolInput.xml CPACS file of a specific module

    Args:
        module_name (str): name of the module as a string

    Retruns:
        toolinput_path (str): Path to the ToolInput CPACS file

    """

    return Path(MODULES_DIR_PATH, module_name, "ToolInput", "ToolInput.xml")


def get_tooloutput_file_path(module_name):
    """Get the path to the ToolOutput.xml CPACS file of a specific module

    Args:
        module_name (str): name of the module as a string

    Retruns:
        tooloutput_path (str): Path to the ToolOutput CPACS file

    """

    return Path(MODULES_DIR_PATH, module_name, "ToolOutput", "ToolOutput.xml")


def get_specs_for_module(module_name, raise_error=False):
    """Return the __specs__ module for a CEASIOMpy module

    Args:
        module_name (str): name of the module as a string
        raise_error (bool): 'True' if error should be raised
                            if __specs__ does not exist
    """

    if not module_name.startswith("ceasiompy."):
        module_name = ".".join((MODNAME_TOP, module_name))

    try:
        specs = importlib.import_module(".".join((module_name, MODNAME_SPECS)))
        return specs
    except ImportError:
        if raise_error:
            raise ImportError(f"{MODNAME_SPECS} module not found for {module_name}")
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
    for mod_name, specs in get_all_module_specs().items():
        if specs is None:
            missing.append(mod_name)
    return missing


def create_default_toolspecific():
    """Create a default XML /toolspecific based on all __spec__ xpath and
    default values. Two CPACS file are created and saved in /utils/doc/

    """

    EMPTY_CPACS_PATH = Path(MODULE_DIR, "doc", "empty_cpacs.xml")

    tixi_in = open_tixi(str(EMPTY_CPACS_PATH))
    tixi_out = open_tixi(str(EMPTY_CPACS_PATH))

    for _, specs in get_all_module_specs().items():
        if specs is not None:
            # Inputs
            for entry in specs.cpacs_inout.inputs:

                xpath = entry.xpath
                if xpath.endswith("/"):
                    xpath = xpath[:-1]

                value_name = xpath.split("/")[-1]
                xpath_parent = xpath[: -(len(value_name) + 1)]

                if not tixi_in.checkElement(xpath):
                    create_branch(tixi_in, xpath_parent)
                    if entry.default_value is not None:
                        value = str(entry.default_value)
                    else:
                        value = "No default value"
                    tixi_in.addTextElement(xpath_parent, value_name, value)

            # Outputs
            for entry in specs.cpacs_inout.outputs:
                xpath = entry.xpath
                create_branch(tixi_out, xpath)

    TOOLSPECIFIC_INPUT_PATH = Path(MODULE_DIR, "doc", "input_toolspecifics.xml")
    TOOLSPECIFIC_OUTPUT_PATH = Path(MODULE_DIR, "doc", "output_toolspecifics.xml")

    tixi_in.save(str(TOOLSPECIFIC_INPUT_PATH))
    tixi_out.save(str(TOOLSPECIFIC_OUTPUT_PATH))


def check_workflow(cpacs_path, submodule_list):
    """Check if a linear workflow can be executed based on given CPACS file

    Note:
        * 'submodule_list' is a list of CEASIOMpy modules to run, example:

        ('PyTornado', 'SkinFriction', 'SU2Run', 'SkinFriction')

        * It is assumed that no XPaths will be deleted in between module, only
          new ones will be created

        * The full workflow will be checked from start to end. If multiple errors
          accumulate all will be shown at the end

    Args:
        cpacs_path (Path): CPACS node path
        submodule_list (list): List of CEASIOMpy module names (order matters!)

    Raises:
        TypeError: If input data has invalid type
        ValueError: If a workflow cannot be executed from start to end
    """

    if not isinstance(cpacs_path, Path):
        raise TypeError("'cpacs_path' must be of type Path")

    if not isinstance(submodule_list, (list, tuple)):
        raise TypeError("'submodule_list' must be of type list or tuple")

    tixi = open_tixi(str(cpacs_path))
    xpaths_from_workflow = set()
    err_msg = False
    for submod_name in submodule_list:
        specs = get_specs_for_module(submod_name)
        if specs is None or not specs.cpacs_inout:
            log.warning(f"No specs found for {submod_name}")
            continue
        # Required inputs
        for entry in specs.cpacs_inout.inputs:
            # The required xpath can either be in the original CPACS file
            # OR in the xpaths produced during the workflow exectution
            if not tixi.checkElement(entry.xpath) and entry.xpath not in xpaths_from_workflow:
                err_msg = True
                log.warning(
                    f"xpath '{entry.xpath}' required by module '{submod_name}' but not found!"
                )
            xpaths_from_workflow.add(entry.xpath)

        # Generated output
        for entry in specs.cpacs_inout.outputs:
            xpaths_from_workflow.add(entry.xpath)

    if err_msg:
        raise ValueError(err_msg)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    # The python script could be run to generate the default toolspecific file
    create_default_toolspecific()
