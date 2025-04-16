"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test for get_su2_results function.


| Author : Aidan Jungo
| Creation: 2022-04-07
| Modified: Leon Deligny
| Date: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pytest
import unittest

from ceasiompy.SU2Run.func.results import save_screenshot

from pathlib import Path
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.commonpaths import TEST_RESULTS_FILES_PATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


class TestSU2Results(CeasiompyTest):

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="requires display")
    def test_save_screenshot(self):
        """Test the function 'save_screenshot'"""

        surface_flow_file = Path(TEST_RESULTS_FILES_PATH, "surface_flow.vtu")
        screenshot_file = save_screenshot(surface_flow_file, "Mach")
        assert screenshot_file.exists()

        if screenshot_file.exists():
            screenshot_file.unlink()

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    unittest.main(verbosity=0)
