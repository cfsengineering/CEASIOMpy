"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/mtom.py'

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

    # Tests to be sure that a 10% change of one of the input modify by less than 10% the output
    mtom_1 = estimate_mtom(65, 6, 362, 60, TEST_RESULTS_PATH)
    mtom_2 = estimate_mtom(71.5, 6, 362, 60, TEST_RESULTS_PATH)
    assert abs(mtom_2 - mtom_1) / mtom_1 < 0.1

    mtom_2 = estimate_mtom(65, 6.6, 362, 60, TEST_RESULTS_PATH)
    assert abs(mtom_2 - mtom_1) / mtom_1 < 0.1

    mtom_2 = estimate_mtom(65, 6, 398, 60, TEST_RESULTS_PATH)
    assert abs(mtom_2 - mtom_1) / mtom_1 < 0.1

    mtom_2 = estimate_mtom(65, 6, 362, 66, TEST_RESULTS_PATH)
    assert abs(mtom_2 - mtom_1) / mtom_1 < 0.1

    # Test A320 like
    assert estimate_mtom(37.5, 4, 122, 36, TEST_RESULTS_PATH) == approx(79000, rel=0.05)

    # Test A350 like
    assert estimate_mtom(70.8, 6, 443, 65, TEST_RESULTS_PATH) == approx(294000, rel=0.05)

    # Test figure creation
    assert Path(TEST_RESULTS_PATH, MTOM_FIGURE_NAME).exists()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
