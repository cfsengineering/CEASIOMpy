"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Module interfaces functions to deal with CPACS input and output

| Author : Aaron Dettmann
| Creation: 2019-08-06

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


import importlib
import inspect
import uuid
from pathlib import Path

from typing import Union

from ceasiompy import log
from ceasiompy.utils.commonpaths import MODULES_DIR_PATH
from cpacspy.cpacsfunctions import create_branch, open_tixi


from ceasiompy.utils import MODULE_DIR

MODNAME_TOP = "ceasiompy"
MODNAME_SPECS = "__specs__"
MODNAME_INIT = "__init__"

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
        test_value=None,
        expanded=True,
    ) -> None:
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
        self.test_value = test_value
        self.unit = self.filter_unit(unit)
        self.descr = descr
        self.xpath = xpath

        # GUI specific
        self.gui = gui
        self.gui_name = gui_name
        self.gui_group = gui_group
        self.expanded = expanded

    def filter_unit(self, unit_entry: Union[None, str]) -> Union[None, str]:
        if unit_entry is None:
            return None
        if not unit_entry.startswith('['):
            unit_entry = '[' + unit_entry
        if not unit_entry.endswith(']'):
            unit_entry = unit_entry + ']'
        return unit_entry


class CPACSInOut:
    def __init__(self):
        """
        Class summarising the input and output data

        Attributes:
            inputs (list): List of CPACS inputs.
            outputs (list): List of CPACS outputs.

        """

        self.inputs = []
        self.outputs = []
        self.change_listeners = {}

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

            # Logic here should be correct
            # If entry.test_value is not specified
            # and entry.default_value is None, we still get None
            test_value = entry.test_value
            if test_value is None:
                test_value = entry.default_value

            # Every GUI element is identified by a random key
            gui_settings_dict[str(uuid.uuid4())] = (
                entry.gui_name,
                entry.default_value,
                entry.var_type,
                entry.unit,
                entry.xpath,
                entry.descr,
                entry.gui_group,
                test_value,
                entry.expanded,
            )

        return gui_settings_dict

    def set_gui_visibility(self, var_name, visible):
        """Set the visibility of a GUI element"""
        for entry in self.inputs:
            if entry.var_name == var_name:
                entry.gui = visible

    def add_change_listener(self, var_name, listener):
        """Add a change listener for a specific input"""
        if var_name in self.change_listeners:
            self.change_listeners[var_name].append(listener)

    def notify_change_listeners(self, var_name):
        """Notify all change listeners for a specific input"""
        if var_name in self.change_listeners:
            for listener in self.change_listeners[var_name]:
                listener()

    def get_defaultvalue_xpath(self, var_name):
        """Get the value of a specific input"""
        for entry in self.inputs:
            if entry.var_name == var_name:
                return (entry.default_value, entry.xpath)
        raise ValueError(f"Input '{var_name}' not found")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_module_path(module_name: str) -> Path:
    """Get the path to the module directory"""

    if module_name not in get_module_list(only_active=False):
        raise ValueError(f"Module '{module_name}' not found")

    return Path(MODULES_DIR_PATH, module_name)


def check_cpacs_input_requirements(
    tixi, *, module_name=None, submodule_level=1, cpacs_inout=None
):
    """Check if the input CPACS file contains the required nodes

    Note:
        * The __specs__ file will be located based on the calling module
        * In most cases this function should be called simply as

        ==> check_cpacs_input_requirements(cpacs_file)

    Args:
        cpacs_file (Path): Path to the CPACS file to check
        module_name (str): Name of the module_name (if None, determined from caller)
        submodule_level (int): Levels up where the CEASIOMpy submodule is located
        cpacs_inout (obj): CPACSInOut() instance

    Raises:
        CPACSRequirementError: If >=1 paths are required but not available in CPACS file.
    """

    if module_name != "utils":

        if not isinstance(submodule_level, int) and submodule_level < 1:
            ValueError("'submodule_level' must be a positive integer")

        # If 'cpacs_inout' not provided by caller, we try to determine it
        if cpacs_inout is None:
            if module_name is None:
                # Get the path of the caller submodule
                frm = inspect.stack()[1]
                mod = inspect.getmodule(frm[0])
                caller_module_path = Path(mod.__file__).parent

                # Get the CEASIOM_XPATH submodule name
                module_name = caller_module_path.name
                for _ in range(1, submodule_level):
                    module_name = caller_module_path.name

            # Load the submodule specifications
            specs_module = get_specs_for_module(module_name, raise_error=True)
            cpacs_inout = specs_module.cpacs_inout

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


def get_module_list(only_active=True):
    """Return a list of CEASIOMpy modules

    ['SkinFriction', 'PyAVL', ...]

    Returns:
        A list of module names (as strings)
    """

    module_list = []
    for module_dir in MODULES_DIR_PATH.iterdir():
        module_name = module_dir.name

        # Ignore "dunder"-files and dot files
        if module_name.startswith("__") or module_name.startswith("."):
            continue

        init = get_init_for_module(module_name, raise_error=False)
        try:
            module_status = init.module_status
        except AttributeError:
            module_status = False
            if module_name != "utils":
                log.warning(
                    f"Module status of {module_name} is not define in its __init__.py file."
                )

        if only_active:
            if module_status:
                module_list.append(module_name)
        else:
            module_list.append(module_name)

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


def get_specs_for_module(module_name: str, raise_error=False):
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
    except ImportError as e:
        log.error(f"Error loading __specs__ for module {module_name}: {e}")
        if raise_error:
            raise ImportError(f"{MODNAME_SPECS} module not found for {module_name}")
        return None


def get_init_for_module(module_name, raise_error=False):
    """Return the __init__ module for a CEASIOMpy module

    Args:
        module_name (str): name of the module as a string
        raise_error (bool): 'True' if error should be raised
                            if __specs__ does not exist
    """

    if not module_name.startswith("ceasiompy."):
        module_name = ".".join((MODNAME_TOP, module_name))

    try:
        init = importlib.import_module(".".join((module_name, MODNAME_INIT)))
        return init
    except ImportError:
        if raise_error:
            raise ImportError(f"{MODNAME_INIT} module not found for {module_name}")
        return None


def get_all_module_specs():
    """Return a dictionary with module names (keys) and specs files (values)

    Note:
        * If the __specs__ module for a CEASIOMpy cannot
          be located the module will be None

    The dictionary has the form:

    {
        'SkinFriction': skinfriction_specs_module,
        'PyAVL': pyavl_specs_module,
        'SomeModuleWithoutSpecsFile': None,
        ...
    }

    Returns:
        all_specs (dict): Dictionary containing all module specs
    """

    all_specs = {}
    for module_name in get_module_list(only_active=False):
        specs = get_specs_for_module(module_name, raise_error=False)
        all_specs[module_name] = specs
    return all_specs


def create_default_toolspecific():
    """Create a default XML /toolspecific based on all __spec__ xpath and
    default values. Two CPACS file are created and saved in /utils/doc/

    """

    EMPTY_CPACS_PATH = Path(MODULE_DIR, "doc", "empty_cpacs.xml")

    tixi_in = open_tixi(EMPTY_CPACS_PATH)
    tixi_out = open_tixi(EMPTY_CPACS_PATH)

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


def module_to_remove_from_coverage():

    active_modules = get_module_list(only_active=True)

    print(
        "\nYou can copy/paste the following lines in the file /CEASIOMpy/pyproject.toml and "
        "replace the existing section to remove disabled module from the code coverage.\n"
    )

    print("[tool.coverage.run]")
    print("omit = [")
    print('  "*/__init__.py",')
    print('  "*/__specs__.py",')
    for module in get_module_list(only_active=False):
        if module not in active_modules and module != "utils":
            print(f'  "*/{module}/*",')
    print("]")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    # The python script could be run to generate the default toolspecific file
    # create_default_toolspecific()

    # Generate the list of module to remove from the code coverage
    module_to_remove_from_coverage()
