"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

| Author : Aidan Jungo
| Creation: 2019-07-24
| Author: Leon Deligny
| Creation: 25 March 2025

"""

# Imports

from ceasiompy.utils.decorators import log_test
from ceasiompy.CLCalculator.func.utils import (
    retrieve_gui,
    save_for_su2,
    deal_with_mass,
)

from unittest import main
from unittest.mock import MagicMock
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from unittest.mock import patch
from ceasiompy.SU2Run import (
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestClCalculatorUtils(CeasiompyTest):

    @patch("ceasiompy.CLCalculator.func.utils.create_branch")
    @patch("ceasiompy.CLCalculator.func.utils.log")
    @log_test
    def test_save_for_su2(self, mock_log, mock_create_branch):
        tixi = MagicMock()
        save_for_su2(tixi, 0.7)
        mock_create_branch.assert_any_call(tixi, SU2_TARGET_CL_XPATH.rsplit("/", 1)[0])
        tixi.updateDoubleElement.assert_called_with(SU2_TARGET_CL_XPATH, 0.7, "%g")
        tixi.updateTextElement.assert_called_with(SU2_FIXED_CL_XPATH, "YES")
        mock_log.info.assert_called()

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_retrieve_gui(self, mock_get_value):
        tixi = MagicMock()
        # Setup mock return values
        mock_get_value.side_effect = [123.4, "MTOM", 11000.0, 0.78, 2.5]
        result = retrieve_gui(tixi)
        self.assertEqual(result, (123.4, "MTOM", 11000.0, 0.78, 2.5))
        self.assertEqual(mock_get_value.call_count, 5)

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_deal_with_mass_custom(self, mock_get_value):
        md = MagicMock()
        tixi = MagicMock()
        mock_get_value.return_value = 50000.0
        mass = deal_with_mass(md, tixi, "Custom")
        self.assertEqual(mass, 50000.0)
        md.p.assert_any_call("The mass used for the calculation is Custom")

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_deal_with_mass_percent_fuel(self, mock_get_value):
        md = MagicMock()
        tixi = MagicMock()
        # percent_fuel_mass, mtom, mzfm
        mock_get_value.side_effect = [10.0, 60000.0, 50000.0]
        mass = deal_with_mass(md, tixi, "% fuel mass")
        expected_mass = (60000.0 - 50000.0) * 10.0 / 100 + 50000.0
        self.assertEqual(mass, expected_mass)
        md.p.assert_any_call("The mass used for the calculation is % fuel mass")

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_deal_with_mass_other(self, mock_get_value):
        md = MagicMock()
        tixi = MagicMock()
        mock_get_value.return_value = 70000.0
        mass = deal_with_mass(md, tixi, "operatingMass")
        self.assertEqual(mass, 70000.0)
        md.p.assert_any_call("The mass used for the calculation is operatingMass")

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_deal_with_mass_mzfm_gt_mtom(self, mock_get_value):
        md = MagicMock()
        tixi = MagicMock()
        # percent_fuel_mass, mtom, mzfm
        mock_get_value.side_effect = [10.0, 50000.0, 60000.0]
        with self.assertRaises(ValueError):
            deal_with_mass(md, tixi, "% fuel mass")

    @patch("ceasiompy.CLCalculator.func.utils.get_value")
    @log_test
    def test_deal_with_mass_not_found(self, mock_get_value):
        md = MagicMock()
        tixi = MagicMock()
        mock_get_value.return_value = None
        with self.assertRaises(ValueError):
            deal_with_mass(md, tixi, "Custom")


# Main

if __name__ == "__main__":
    main(verbosity=0)
