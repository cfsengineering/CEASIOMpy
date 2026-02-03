"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/moduleinterfaces.py'
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest

from ceasiompy.utils.moduleinterfaces import (
    get_module_path,
    get_specs_for_module,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)

from pathlib import Path

from ceasiompy.utils.commonpaths import MODULES_DIR_PATH

MODULE_DIR = Path(__file__).parent
CPACS_TEST_FILE = Path(MODULE_DIR, "ToolInput", "cpacs_test_file.xml")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_module_path():
    """Test function 'get_module_path'."""

    assert get_module_path("utils") == Path(MODULES_DIR_PATH, "utils")

    with pytest.raises(ValueError):
        get_module_path("NotExistingModule")


def test_get_toolinput_file_path():
    """
    Test that 'get_toolinput_file_path' works
    """

    module_name = "ModuleTemplate"

    toolinput_path = get_toolinput_file_path(module_name)

    # Test that the end of the path is correct
    assert toolinput_path == Path(MODULES_DIR_PATH, "ModuleTemplate", "ToolInput", "ToolInput.xml")


def test_get_tooloutput_file_path():
    """
    Test that 'get_tooloutput_file_path' works
    """

    module_name = "ModuleTemplate"

    toolinput_path = get_tooloutput_file_path(module_name)

    # Test that the end of the path is correct
    assert toolinput_path == Path(
        MODULES_DIR_PATH, "ModuleTemplate", "ToolOutput", "ToolOutput.xml"
    )


def test_get_specs_for_module():
    """
    Test that 'get_specs_for_module()' works
    """

    # Return None for non-existent modules...
    specs = get_specs_for_module(module_name="SomeModuleThatDoesNotExist")
    assert specs is None

    # ... but raise an error if explicitly told to do so
    with pytest.raises(ImportError):
        get_specs_for_module(module_name="SomeModuleThatDoesNotExist", raise_error=True)
