"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/ThermoData/func/turbojet_func.py'

Python version: >=3.8


| Author : Francesco Marcucci
| Creation: 2024-02-09

"""
# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path

import pytest
from ceasiompy.SU2Run.func.su2results import save_screenshot
from ceasiompy.utils.commonpaths import TEST_RESULTS_FILES_PATH

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="requires display")
def test_save_screenshot():
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

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
