"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import pandas as pd

from ceasiompy.DynamicStability.func.alphamax import get_alpha_max

from unittest import main
from unittest.mock import MagicMock

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class DummyAlphaMaxClass:
    def __init__(self, software_data, mach_str, aircraft_name):
        self.software_data = software_data
        self.mach_str = mach_str
        self.aircraft_name = aircraft_name


class TestAlphaMax(unittest.TestCase):

    @patch("ceasiompy.DynamicStability.func.alphamax.CeasiompyDb")
    @patch("ceasiompy.DynamicStability.func.alphamax.log")
    def test_get_alpha_max_avl(self, _, mock_db):
        # Setup
        dummy = DummyAlphaMaxClass(
            software_data="AVL", mach_str="0.7,0.8", aircraft_name="TestPlane"
        )
        # Mock DB return: mach, alpha, cms_a
        mock_data = [
            (0.7, -2, -0.5),
            (0.7, 0, -0.1),
            (0.7, 2, 0.2),
            (0.8, -2, -0.3),
            (0.8, 0, -0.2),
            (0.8, 2, -0.05),
        ]
        mock_db.return_value.get_data.return_value = mock_data
        mock_db.return_value.close = MagicMock()

        # Attach the method to the dummy instance if needed
        dummy.get_alpha_max = get_alpha_max.__get__(dummy)

        df = dummy.get_alpha_max()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("mach", df.columns)
        self.assertIn("alpha_max", df.columns)
        # Check correct alpha_max for each mach
        result = dict(zip(df["mach"], df["alpha_max"]))
        self.assertAlmostEqual(result[0.7], 0.0)  # last cms_a < 0 is at alpha=0
        self.assertAlmostEqual(result[0.8], 2.0)  # last cms_a < 0 is at alpha=2

    @patch("ceasiompy.DynamicStability.func.alphamax.CeasiompyDb")
    @patch("ceasiompy.DynamicStability.func.alphamax.log")
    def test_get_alpha_max_non_avl(self, mock_log, mock_db):
        dummy = DummyAlphaMaxClass(
            software_data="OTHER", mach_str="0.7", aircraft_name="TestPlane"
        )
        mock_db.return_value.get_data.return_value = []
        mock_db.return_value.close = MagicMock()

        dummy.get_alpha_max = get_alpha_max.__get__(dummy)

        df = dummy.get_alpha_max()
        mock_log.warning.assert_called()
        self.assertTrue(isinstance(df, pd.DataFrame))


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main()
