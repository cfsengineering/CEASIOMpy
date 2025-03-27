"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/moduleinterfaces.py'

Python version: >=3.8

| Author : Aaron Dettmann
| Creation: 2019-09-09

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path

import pytest
from ceasiompy.utils.moduleinterfaces import (
    CPACSInOut,
    CPACSRequirementError,
    check_cpacs_input_requirements,
    get_all_module_specs,
    get_module_path,
    get_specs_for_module,
    get_module_list,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.commonpaths import MODULES_DIR_PATH
from ceasiompy.utils.commonxpath import RANGE_XPATH

MODULE_DIR = Path(__file__).parent
CPACS_TEST_FILE = Path(MODULE_DIR, "ToolInput", "cpacs_test_file.xml")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_module_path():
    """Test function 'get_module_path'."""

    assert get_module_path("ModuleTemplate") == Path(MODULES_DIR_PATH, "ModuleTemplate")

    with pytest.raises(ValueError):
        get_module_path("NotExistingModule")


def test_cpacs_inout():
    """
    Test basic functionality of 'CPACSInOut()'
    """

    cpacs_inout = CPACSInOut()

    # Adding input
    cpacs_inout.add_input(
        descr="Test description",
        xpath="/cpacs/testpath",
        default_value=5,
        unit="m/s",
        var_name=None,
    )

    # Adding output
    cpacs_inout.add_output(
        descr="Test description",
        xpath="/cpacs/testpath",
        default_value=None,
        unit="m/s",
        var_name=None,
    )

    # For the output we do not need to pass 'default_value'
    cpacs_inout.add_output(
        descr="Test description", xpath="/cpacs/testpath", unit="m/s", var_name=None
    )

    with pytest.raises(ValueError):
        cpacs_inout.add_output(
            descr="Test description",
            xpath="/cpacs/testpath",
            default_value="THIS STRING SHOULE CAUSE AN ERROR",
            unit="m/s",
            var_name=None,
        )

    # Make sure entries have been added properly
    assert len(cpacs_inout.inputs) == 1
    assert len(cpacs_inout.outputs) == 2


def test_check_cpacs_input_requirements():
    """
    Test "check_cpacs_input_requirements()" function
    """

    cpacs_inout = CPACSInOut()
    cpacs_file = Path(MODULE_DIR, "ToolInput", "D150_AGILE_Hangar_v3.xml")

    cpacs_inout.add_input(
        var_name="cruise_alt",
        default_value=12000,
        unit="m",
        descr="Aircraft cruise altitude",
        xpath=RANGE_CRUISE_ALT_XPATH,
    )

    assert check_cpacs_input_requirements(cpacs_file, cpacs_inout=cpacs_inout) is None

    cpacs_inout.add_input(
        var_name="something",
        default_value=None,
        unit="m",
        descr="Some description",
        xpath="/a/non-existent/path",
    )

    with pytest.raises(CPACSRequirementError):
        check_cpacs_input_requirements(cpacs_file, cpacs_inout=cpacs_inout)


def test_get_module_list():
    """
    Test 'get_module_list' function
    """

    module_list = get_module_list(only_active=False)
    for module_name in module_list:
        assert len(module_name.split(".")) == 1

    assert "SU2Run" in module_list
    assert "utils" in module_list
    assert "NotExistingModule" not in module_list

    module_list_active = get_module_list(only_active=True)
    assert "SU2Run" in module_list_active
    assert "utils" not in module_list_active
    assert "NotExistingModule" not in module_list_active

    assert len(module_list_active) < len(module_list)


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


def test_get_all_module_specs():
    """
    Test that 'get_all_module_specs()' runs
    """

    all_specs = get_all_module_specs()
    assert isinstance(all_specs, dict)


def test_create_default_toolspecific():
    """
    Test that 'create_default_toolspecific' works
    """

    pass
    # TODO: how to test that...


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test moduleinterfaces.py")
    print("To run test use the following command:")
    print(">> pytest -v")
