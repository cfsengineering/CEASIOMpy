"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/moduleinterfaces.py'

Python version: >=3.7

| Author : Aaron Dettmann
| Creation: 2019-09-09
| Last modifiction: 2019-11-08 (AJ)
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================


import os

import pytest

import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.utils.xpath import RANGE_XPATH

HERE = os.path.abspath(os.path.dirname(__file__))
CPACS_TEST_FILE = os.path.join(HERE, "ToolInput", "cpacs_test_file.xml")


def test_cpacs_inout():
    """
    Test basic functionality of 'CPACSInOut()'
    """

    cpacs_inout = mi.CPACSInOut()

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

    os.chdir(os.path.dirname(__file__))

    cpacs_inout = mi.CPACSInOut()
    cpacs_file = "ToolInput/D150_AGILE_Hangar_v3.xml"

    cpacs_inout.add_input(
        var_name="cruise_alt",
        default_value=12000,
        unit="m",
        descr="Aircraft cruise altitude",
        xpath=RANGE_XPATH + "/cruiseAltitude",
    )

    assert mi.check_cpacs_input_requirements(cpacs_file, cpacs_inout=cpacs_inout) is None

    cpacs_inout.add_input(
        var_name="something",
        default_value=None,
        unit="m",
        descr="Some description",
        xpath="/a/non-existent/path",
    )

    with pytest.raises(mi.CPACSRequirementError):
        mi.check_cpacs_input_requirements(cpacs_file, cpacs_inout=cpacs_inout)


def test_get_submodule_list():
    """
    Test 'get_submodule_list()' function
    """

    submodule_list = mi.get_submodule_list()
    for submod_name in submodule_list:
        assert len(submod_name.split(".")) == 1


def test_get_module_list():
    """
    Test "get_module_list()" function
    """

    module_list = mi.get_module_list()

    assert isinstance(module_list, list)

    # There should be entries, otherwise something went wrong
    assert len(module_list) > 0

    # Modules should have the form 'ceasiompy.SubModule'
    for module_name in module_list:
        assert module_name.startswith("ceasiompy.")
        assert len(module_name.split(".")) == 2


def test_get_toolinput_file_path():
    """
    Test that 'get_toolinput_file_path' works
    """

    module_name = "ModuleTemplate"

    toolinput_path = mi.get_toolinput_file_path(module_name)

    # Test that the end of the path is correct
    assert toolinput_path.endswith(
        os.path.join("CEASIOMpy", "ceasiompy", "ModuleTemplate", "ToolInput", "ToolInput.xml")
    )


def test_get_tooloutput_file_path():
    """
    Test that 'get_tooloutput_file_path' works
    """

    module_name = "ModuleTemplate"

    toolinput_path = mi.get_tooloutput_file_path(module_name)

    # Test that the end of the path is correct
    assert toolinput_path.endswith(
        os.path.join("CEASIOMpy", "ceasiompy", "ModuleTemplate", "ToolOutput", "ToolOutput.xml")
    )


def test_get_specs_for_module():
    """
    Test that 'get_specs_for_module()' works
    """

    # Return None for non-existent modules...
    specs = mi.get_specs_for_module(module_name="SomeModuleThatDoesNotExist")
    assert specs is None

    # ... but raise an error if explicitly told to do so
    with pytest.raises(ImportError):
        mi.get_specs_for_module(module_name="SomeModuleThatDoesNotExist", raise_error=True)


def test_get_all_module_specs():
    """
    Test that 'get_all_module_specs()' runs
    """

    all_specs = mi.get_all_module_specs()
    assert isinstance(all_specs, dict)


def test_find_missing_specs():
    """
    Test that 'find_missing_specs()' runs
    """

    missing = mi.find_missing_specs()
    assert isinstance(missing, list)


def test_create_default_toolspecific():
    """
    Test that 'create_default_toolspecific' works
    """

    pass
    # TODO: how to test that...


def test_check_workflow():
    """
    Check function 'check_workflow'
    """

    workflow = ("NON_EXISTENT_MODULE",)

    with pytest.raises(ValueError):
        workflow = ("PyTornado", "NON_EXISTENT_MODULE")
        mi.check_workflow(CPACS_TEST_FILE, workflow)

    with pytest.raises(ValueError):
        workflow = ("SU2Run", "PyTornado", "WeightUnconventional", "BalanceUnconventional")
        mi.check_workflow(CPACS_TEST_FILE, workflow)
