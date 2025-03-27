"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SaveAeroCoefficients/saveaerocoef.py'

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-09-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path

from ceasiompy.SaveAeroCoefficients.saveaerocoef import main as save_aero_coef
from ceasiompy.utils.ceasiompyutils import change_working_dir
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_saveaerocoef_test.xml")
FIG_PATH = Path(MODULE_DIR, "Results", "AeroCoefficients", "D150-Alt0.0-Mach0.3-AoS0.0.png")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_save_aero_coef():
    """
    Test if the function 'save_aero_coef' will produce a figure
    """

    with change_working_dir(MODULE_DIR):
        save_aero_coef(CPACS_IN_PATH, CPACS_OUT_PATH)
        assert FIG_PATH.exists()

    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()

    if FIG_PATH.exists():
        FIG_PATH.unlink()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test SaveAeroCoefficients")
    print("To run test use the following command:")
    print(">> pytest -v")
