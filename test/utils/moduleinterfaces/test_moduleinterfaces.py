import os

import pytest

import ceasiompy.utils.moduleinterfaces as m


def test_cpacs_inout():
    """
    Test basic functionality of 'CPACSInOut()'
    """

    cpacs_inout = m.CPACSInOut()

    # Adding input
    cpacs_inout.add_input(
        descr='Test description',
        cpacs_path='/cpacs/testpath',
        default_value=5,
        unit='m/s',
        var_name=None
    )

    # Adding output
    cpacs_inout.add_output(
        descr='Test description',
        cpacs_path='/cpacs/testpath',
        default_value=None,
        unit='m/s',
        var_name=None
    )

    # For the output we do not need to pass 'default_value'
    cpacs_inout.add_output(
        descr='Test description',
        cpacs_path='/cpacs/testpath',
        unit='m/s',
        var_name=None
    )

    with pytest.raises(ValueError):
        cpacs_inout.add_output(
            descr='Test description',
            cpacs_path='/cpacs/testpath',
            default_value='THIS STRING SHOULE CAUSE AN ERROR',
            unit='m/s',
            var_name=None
        )

    # Make sure entries have been added properly
    assert len(cpacs_inout.inputs) == 1
    assert len(cpacs_inout.outputs) == 2


def test_module_name_list():
    """
    Test "get_module_list()" function
    """

    module_list = m.get_module_list()

    assert isinstance(module_list, list)

    # There should be entries, otherwise something went wrong
    assert len(module_list) > 0

    for module_name in module_list:
        assert module_name.startswith('ceasiompy.')
        assert len(module_name.split('.')) == 2


def test_check_cpacs_input_requirements():
    """
    Test "check_cpacs_input_requirements()" function
    """

    os.chdir(os.path.dirname(__file__))

    cpacs_inout = m.CPACSInOut()
    cpacs_file = 'ToolInput/D150_AGILE_Hangar_v3.xml'

    cpacs_inout.add_input(
        var_name='cruise_alt',
        default_value=12000,
        unit='m',
        descr='Aircraft cruise altitude',
        cpacs_path=m.CEASIOM_XPATH + '/ranges/cruiseAltitude',
    )

    assert m.check_cpacs_input_requirements(cpacs_file, cpacs_inout, __file__) is None

    cpacs_inout.add_input(
        var_name='something',
        default_value=None,
        unit='m',
        descr='Some description',
        cpacs_path='/a/non-existent/path',
    )

    with pytest.raises(m.CPACSRequirementError):
        m.check_cpacs_input_requirements(cpacs_file, cpacs_inout, __file__)
