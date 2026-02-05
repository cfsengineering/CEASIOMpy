"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'
"""

# Imports

import streamlit as st

from pytest import approx
from ceasiompy.utils.decorators import log_test
from ceasiompy.clcalculator.func.calculatecl import calculate_cl
from ceasiompy.clcalculator.clcalculator import main as cl_calculator
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    update_cpacs_from_specs,
)

from unittest import main
from unittest.mock import MagicMock
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.clcalculator import MODULE_NAME

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestClCalculator(CeasiompyTest):

    @log_test
    def test_calculate_cl(self):
        self.assert_equal_function(
            f=calculate_cl,
            input_args=(
                122,
                12_000,
                0.78,
                50_000,
                1.0,
            ),
            expected=(approx(0.48429196151547343),),
        )

    @log_test
    def test_main(self):
        st.session_state = MagicMock()
        update_cpacs_from_specs(self.test_cpacs, module_name=MODULE_NAME, test=True)
        cl_calculator(self.test_cpacs, wkdir=current_workflow_dir())


# Main

if __name__ == "__main__":
    main(verbosity=0)
