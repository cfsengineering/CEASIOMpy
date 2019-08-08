from lib.utils.moduleinterfaces import CPACSInOut


def test_basic():
    """
    Test basic functionality of 'CPACSInOut()'
    """

    cpacs_inout = CPACSInOut()

    cpacs_inout.add_input(
            descr='Test description',
            cpacs_path='/cpacs/testpath',
            default_value=5,
            unit='m/s',
            var_name=None
        )

    cpacs_inout.add_output(
            descr='Test description',
            cpacs_path='/cpacs/testpath',
            default_value=None,
            unit='m/s',
            var_name=None
        )
