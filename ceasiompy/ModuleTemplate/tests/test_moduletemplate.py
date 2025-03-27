"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland


Test functions ModuleTemplate module.
=======
Test functions for 'lib/ModuleTemplate/moduletemplate.py'
>>>>>>> origin/main

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2019-08-14

| Modified: Leon Deligny
| Date: 18-Mar-2025
=======
>>>>>>> origin/main

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pytest import approx
from ceasiompy.ModuleTemplate.moduletemplate import MyClass, get_fuselage_scaling, sum_funcion
from ceasiompy.ModuleTemplate.func.subfunc import my_subfunc
import pytest
from pathlib import Path
from ceasiompy.utils.decorators import log_test
from ceasiompy.ModuleTemplate.moduletemplate import get_fuselage_scaling

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest
from ceasiompy.ModuleTemplate.func.subfunc import MyClass


MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "ToolOutput", "ToolOutput.xml")


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestModuleTemplate(CeasiompyTest):

    @log_test
    def test_module_template_functions(self) -> None:
        self.assert_equal_function(
            f=get_fuselage_scaling,
            input=self.test_cpacs,
            expected=(1.0, 1.0, 1.0),
        )

    @log_test
    def test_my_class(self):
        TestClass = MyClass()

        self.assertEqual(TestClass.var_a, 1.1)
        self.assertEqual(TestClass.var_b, 2.2)
        self.assertEqual(TestClass.var_c, 0.0)

        TestClass.add_my_var()
        self.assertAlmostEqual(TestClass.var_c, 3.3)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_MyClass():
    """Test Class 'MyClass'"""

    TestClass = MyClass()

    assert TestClass.var_a == 1.1
    assert TestClass.var_b == 2.2
    assert TestClass.var_c == 0.0

    TestClass.add_my_var()
    assert TestClass.var_c == approx(3.3)


def test_sum_funcion():
    """Test function 'sum_funcion'"""

    # Test Raise ValueError
    with pytest.raises(ValueError):
        sum_funcion(5.5, 4.4)

    # Test 'sum_funcion' normal use
    assert sum_funcion(5, 4.4) == approx(9.4)


def test_get_fuselage_scaling():
    """Test function 'get_fuselage_scaling'"""

    x, y, z = get_fuselage_scaling(CPACS_IN_PATH, CPACS_OUT_PATH)

    assert x == approx(1)
    assert y == approx(0.5)
    assert z == approx(0.5)


def test_subfunc():
    """Test subfunction 'my_subfunc'"""

    a = "a"
    b = "b"

    res = my_subfunc(a, b)

    assert res == "a and b"


# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":
    main(verbosity=0)

if __name__ == "__main__":

    print("Test ModuleTemplate")
    print("To run test use the following command:")
    print(">> pytest -v")
