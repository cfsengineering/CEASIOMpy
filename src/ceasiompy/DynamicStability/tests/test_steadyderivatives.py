"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.DynamicStability.func.steadyderivatives import (
    format_aero_data,
    format_ctrl_data,
)

from pandas import DataFrame
from unittest import (
    main,
    TestCase,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestSteadyDerivatives(TestCase):

    def test_format_aero_data(self):
        df = DataFrame({
            "mach": [0.7, 0.7, 0.7, 0.8, 0.8],
            "alpha": [0, 1, 2, 0, 1],
            "beta": [0, 1, 0, 0, 0],
            "pb_2V": [0, 0, 0, 0, 0],
            "qc_2V": [0, 0, 0, 0, 0],
            "rb_2V": [0, 0, 0, 0, 0],
            "cl": [1, 2, 3, 4, 5],
            "cd": [0.1, 0.2, 0.3, 0.4, 0.5],
            "cms": [0, 0, 0, 0, 0],
            "cs": [0, 0, 0, 0, 0],
            "cmd": [0, 0, 0, 0, 0],
            "cml": [0, 0, 0, 0, 0],
        })
        result = format_aero_data(
            df,
            chosen_beta=[0, 1],
            chosen_p=[0],
            chosen_q=[0],
            chosen_r=[0],
        )
        self.assertIsInstance(result, DataFrame)
        self.assertIn("mach", result.columns)
        self.assertEqual(len(result), 5)

    def test_format_ctrl_data(self):
        df = DataFrame({
            "mach": [0.7, 0.7, 0.8, 0.8],
            "alpha": [0, 1, 0, 1],
            "elevator": [0, 1, 0, 0],
            "rudder": [0, 0, 1, 0],
            "aileron": [0, 0, 0, 1],
            "cl": [1, 2, 3, 4],
            "cd": [0.1, 0.2, 0.3, 0.4],
            "cms": [0, 0, 0, 0],
            "cs": [0, 0, 0, 0],
            "cmd": [0, 0, 0, 0],
            "cml": [0, 0, 0, 0],
        })
        result = format_ctrl_data(
            df,
            chosen_elevator=[0, 1],
            chosen_aileron=[0, 1],
            chosen_rudder=[0, 1],
        )
        self.assertIsInstance(result, DataFrame)
        self.assertIn("mach", result.columns)
        self.assertEqual(len(result), 6)


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main()
