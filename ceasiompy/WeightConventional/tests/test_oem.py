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

import shutil
from pathlib import Path

from ceasiompy.WeightConventional.func.oem import estimate_oem
from pytest import approx

MODULE_DIR = Path(__file__).parent
TEST_RESULTS_PATH = Path(MODULE_DIR, "ToolOutput")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_estimate_oem():
    """Test function 'estimate_oem'"""

    if TEST_RESULTS_PATH.exists():
        shutil.rmtree(TEST_RESULTS_PATH)
    TEST_RESULTS_PATH.mkdir()

    # estimate_oem(mtom, fuse_length, wing_span, turboprop)
    assert estimate_oem(350_000, 58, 61, False) == approx(171_452, rel=1e-2)
    assert estimate_oem(250_000, 48, 51, False) == approx(125_807, rel=1e-2)
    assert estimate_oem(150_000, 38, 44, False) == approx(78_633, rel=1e-2)
    assert estimate_oem(150_000, 38, 44, True) == approx(76_690, rel=1e-2)
    assert estimate_oem(50_000, 24, 34, False) == approx(26_431, rel=1e-2)
    assert estimate_oem(50_000, 24, 34, True) == approx(28_897, rel=1e-2)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
