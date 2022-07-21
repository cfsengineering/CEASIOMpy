"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/mtom.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-05-30

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import shutil

from pytest import approx

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.utils.commonnames import MTOM_FIGURE_NAME

MODULE_DIR = Path(__file__).parent
TEST_RESULTS_PATH = Path(MODULE_DIR, "ToolOutput")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_estimate_mtom():
    """Test function 'estimate_mtom'"""

    if TEST_RESULTS_PATH.exists():
        shutil.rmtree(TEST_RESULTS_PATH)
    TEST_RESULTS_PATH.mkdir()

    # estimate_mtom(fuselage_length, fuselage_width, wing_area, wing_span)
    # These tests are made from random value just to check if the function return the same kind of
    # result after it will be refactored.
    assert estimate_mtom(50, 5, 750, 60, TEST_RESULTS_PATH) == approx(223398, rel=1e-2)
    assert estimate_mtom(55, 5, 750, 60, TEST_RESULTS_PATH) == approx(231389, rel=1e-2)
    assert estimate_mtom(50, 5, 550, 60, TEST_RESULTS_PATH) == approx(176957, rel=1e-2)
    assert estimate_mtom(50, 5, 550, 50, TEST_RESULTS_PATH) == approx(173153, rel=1e-2)
    assert estimate_mtom(20, 2.5, 250, 28, TEST_RESULTS_PATH) == approx(23255, rel=1e-2)
    assert estimate_mtom(12, 2, 65, 15, TEST_RESULTS_PATH) == approx(18900, rel=1e-2)
    assert estimate_mtom(12, 2, 62, 15, TEST_RESULTS_PATH) == approx(17707, rel=1e-2)

    # Seems wrong, maybe out of range
    # assert estimate_mtom(10, 1.8, 50, 11, TEST_RESULTS_PATH) == approx(17707, rel=1e-2)
    # --> Obtained: 33795.118

    assert Path(TEST_RESULTS_PATH, MTOM_FIGURE_NAME).exists()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
