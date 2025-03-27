"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2019-07-24

| Author: Leon Deligny
| Creation: 25 March 2025
=======
>>>>>>> origin/main

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from cpacspy.cpacsfunctions import open_tixi
from ceasiompy.utils.commonxpath import SU2_TARGET_CL_XPATH
from ceasiompy.CLCalculator.clcalculator import calculate_cl
from pathlib import Path
from pytest import approx

from ceasiompy.utils.decorators import log_test

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest


MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_clcalulator_test.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


class TestModuleTemplate(CeasiompyTest):

    @log_test
    def test_calculate_cl(self):
        self.assert_equal_function(
            f=calculate_cl,
            input=(122, 12_000, 0.78, 50_000, 1.0, ),
            expected=(approx(0.48429196151547343), ),
        )


def test_calculate_cl():
    """Test function 'calculate_cl'"""

    ref_area = 122
    alt = 12000
    mach = 0.78
    mass = 50000
    load_fact = 1.0

    cl = calculate_cl(ref_area, alt, mach, mass, load_fact)

    assert cl == approx(0.48429196151547343)

# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":

    main(verbosity=0)


print("Running Test CL Calulator")
print("To run test use the following command:")
print(">> pytest -v")
