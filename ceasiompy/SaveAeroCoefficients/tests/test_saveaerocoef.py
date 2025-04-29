"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

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

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_save_aero_coef():
    """
    Test if the function 'save_aero_coef' will produce a figure
    """

    with change_working_dir(MODULE_DIR):
        cpacs = CPACS(CPACS_IN_PATH)
        results_dir = get_results_directory(MODULE_NAME)
        save_aero_coef(cpacs, results_dir)

        # Assert a .png file exists in the directory
        png_files = list(results_dir.glob("*.png"))
        assert png_files, f"No .png file found in {results_dir}"

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    print("Test SaveAeroCoefficients")
    print("To run test use the following command:")
    print(">> pytest -v")
