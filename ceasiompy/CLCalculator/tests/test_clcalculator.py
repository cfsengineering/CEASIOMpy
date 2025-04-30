"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

| Author : Aidan Jungo
| Creation: 2019-07-24
| Author: Leon Deligny
| Creation: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.CLCalculator.clcalculator import calculate_cl
from pathlib import Path
from pytest import approx

from ceasiompy.utils.decorators import log_test

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.CLCalculator import MODULE_DIR

CPACS_IN_PATH = Path(MODULE_DIR, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_clcalulator_test.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestModuleTemplate(CeasiompyTest):

    @log_test
    def test_calculate_cl(self):
        self.assert_equal_function(
            f=calculate_cl,
            input_args=(122, 12_000, 0.78, 50_000, 1.0, ),
            expected=(approx(0.48429196151547343), ),
        )

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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
