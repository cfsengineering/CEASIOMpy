"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Module interfaces functions to deal with CPACS input and output
"""

# Imports
import inspect
import importlib

from pathlib import Path

from ceasiompy import log
from ceasiompy.utils.commonpaths import MODULES_DIR_PATH


# Constants

MODNAME_TOP = "ceasiompy"
MODNAME_SPECS = "__specs__"
MODNAME_INIT = "__init__"


# Functions
def get_module_path(module_name: str) -> Path:
    """Get the path to the module directory"""

    if module_name not in get_module_list(only_active=False):
        raise ValueError(f"Module '{module_name}' not found")

    return Path(MODULES_DIR_PATH, module_name)


def check_cpacs_input_requirements(tixi, *, module_name=None, submodule_level=1, cpacs_inout=None):
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

            raise ValueError("CPACS xpath(s) required but does not exist!")


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
            MODULE_STATUS = init.MODULE_STATUS
        except AttributeError:
            MODULE_STATUS = False
            if module_name != "utils":
                log.warning(
                    f"Module status of {module_name} is not define in its __init__.py file."
                )

        if only_active:
            if MODULE_STATUS:
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


def get_specs_for_module(module_name: str, reloading=False, raise_error=False):
    """Return the __specs__ module for a CEASIOMpy module

    Args:
        module_name (str): name of the module as a string
        raise_error (bool): 'True' if error should be raised
                            if __specs__ does not exist
    """

    if not module_name.startswith("ceasiompy."):
        module_name = ".".join((MODNAME_TOP, module_name))
    specs = None
    try:
        specs = importlib.import_module(".".join((module_name, MODNAME_SPECS)))
        if reloading:
            importlib.reload(specs)
    except ImportError as e:
        log.error(f"Error loading __specs__ for module {module_name}: {e}")
        if raise_error:
            raise ImportError(f"{MODNAME_SPECS} module not found for {module_name}")
    return specs


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
