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

    # TODO
    pass
