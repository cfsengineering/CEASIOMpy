"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2019-07-24
| Author: Leon Deligny
| Creation: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pytest import approx
from ceasiompy.CLCalculator.func.calculatecl import calculate_cl

from ceasiompy.utils.decorators import log_test

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

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

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
