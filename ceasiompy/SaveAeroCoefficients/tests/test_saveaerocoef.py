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

from ceasiompy.SaveAeroCoefficients.saveaerocoef import main as save_aero_coef
from ceasiompy.utils.ceasiompyutils import change_working_dir, get_results_directory

from pathlib import Path
from cpacspy.cpacspy import CPACS


from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.SaveAeroCoefficients import MODULE_NAME, MODULE_DIR

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_saveaerocoef_test.xml")
FIG_PATH = Path(MODULE_DIR, "Results", "ExportCSV", "D150-Alt0.0-Mach0.3-AoS0.0.png")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_save_aero_coef():
    """
    Test if the function 'save_aero_coef' will produce a figure
    """

    with change_working_dir(MODULE_DIR):
        cpacs = CPACS(CPACS_IN_PATH)
        save_aero_coef(cpacs, get_results_directory(MODULE_NAME))
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
