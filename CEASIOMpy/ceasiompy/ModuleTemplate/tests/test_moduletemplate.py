"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions ModuleTemplate module.

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2019-08-14
| Modified: Leon Deligny
| Date: 18-Mar-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.ModuleTemplate.moduletemplate import get_fuselage_scaling

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest
from ceasiompy.ModuleTemplate.func.subfunc import MyClass


# =================================================================================================
#   CLASSES
# =================================================================================================

class TestModuleTemplate(CeasiompyTest):

    @log_test
    def test_module_template_functions(self) -> None:
        self.assert_equal_function(
            f=get_fuselage_scaling,
            input_args=(self.test_cpacs, ),
            expected=(1.0, 1.0, 1.0, ),
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
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
