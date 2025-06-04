"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SaveAeroCoefficients/saveaerocoef.py'

| Author : Aidan Jungo
| Creation: 2022-09-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

<<<<<<< HEAD
from ceasiompy.SaveAeroCoefficients.saveaerocoef import main as save_aero_coef
from ceasiompy.utils.ceasiompyutils import change_working_dir, get_results_directory

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.SaveAeroCoefficients import MODULE_NAME, MODULE_DIR

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_saveaerocoef_test.xml")
=======
import pandas as pd

from ceasiompy.SaveAeroCoefficients.func.utils import (
    write_legend,
    deal_with_feature,
)
from ceasiompy.SaveAeroCoefficients.saveaerocoef import main as save_aero_coef
from ceasiompy.SaveAeroCoefficients.func.responsesurface import plot_response_surface
from ceasiompy.utils.ceasiompyutils import (
    create_branch,
    change_working_dir,
    current_workflow_dir,
    get_results_directory,
    update_cpacs_from_specs,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.commonpaths import MODULES_DIR_PATH
from ceasiompy.utils.commonxpaths import (
    SM_XPATH,
)
from ceasiompy.SaveAeroCoefficients import (
    NONE_LIST,
    MODULE_DIR,
    MODULE_NAME,
)
>>>>>>> general_updates

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


<<<<<<< HEAD
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
=======
class TestSaveAeroCoef(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.results_dir = get_results_directory(
            module_name=MODULE_NAME,
            wkflow_dir=current_workflow_dir()
        )
        cls.df = pd.DataFrame({
            "alpha": [2, 4],
            "angleOfSideslip": [0.0, 0.0],
        })
        cls.criterion = (cls.df["alpha"] > 0)
        cls.groupby_list = ["alpha", "angleOfSideslip"]

    def test_save_aero_coef(self):
        """
        Test if the function 'save_aero_coef' will produce a figure
        """

        with change_working_dir(MODULE_DIR):
            save_aero_coef(self.test_cpacs, self.results_dir)

            # Assert a .png file exists in the directory
            png_files = list(self.results_dir.glob("*.png"))
            assert png_files, f"No .png file found in {self.results_dir}"

    def test_plot_response_surface(self):
        model_path = str(
            MODULES_DIR_PATH / "SaveAeroCoefficients" / "tests" / "surrogateModel_cl.pkl"
        )
        create_branch(self.test_cpacs.tixi, SM_XPATH)
        self.test_cpacs.tixi.updateTextElement(SM_XPATH, model_path)

        update_cpacs_from_specs(
            self.test_cpacs,
            module_name=MODULE_NAME,
            test=True,
        )

        plot_response_surface(self.test_cpacs, self.results_dir)

    def test_single_groupby_str_value(self):
        legend = write_legend(["angleOfAttack"], 5)
        assert legend == "AoA=5"

    def test_single_groupby_uid(self):
        legend = write_legend(["uid"], "aero1")
        assert legend == "aero1"

    def test_multiple_groupby_tuple_value(self):
        legend = write_legend(["angleOfAttack", "machNumber"], (3, 0.8))
        assert legend == "AoA=3\nMach=0.8"

    def test_groupby_with_unknown_feature(self):
        legend = write_legend(["unknown", "machNumber"], (1, 0.7))
        assert legend == "unknown=1\nMach=0.7"

    def test_multiple_groupby_uid_and_other(self):
        legend = write_legend(["uid", "altitude"], ("aero2", 12000))
        assert legend == "aero2\nalt=12000"

    def test_single_unique_value(self):
        df = pd.DataFrame({"angleOfAttack": [1, 1]})
        title = "Test"
        groupby_list = ["angleOfAttack"]
        # Should append the unique value to the title
        deal_with_feature(title, None, df, groupby_list, "angleOfAttack", "any")
        # No assertion needed, just check no error

    def test_crit_not_in_none_list(self):
        title = "Test"
        groupby_list = ["angleOfAttack", "angleOfSideslip"]
        crit = "0.0"
        # Should enter the elif branch
        deal_with_feature(title, self.criterion, self.df, groupby_list, "angleOfSideslip", crit)
        # No assertion needed, just check no error

    def test_crit_in_none_list(self):
        title = "Test"
        groupby_list = ["angleOfAttack", "angleOfSideslip"]
        crit = NONE_LIST[0]  # e.g. ""
        # Should NOT enter the elif branch
        deal_with_feature(title, self.criterion, self.df, groupby_list, "angleOfSideslip", crit)
        # No assertion needed, just check no error

>>>>>>> general_updates

# =================================================================================================
#    MAIN
# =================================================================================================

<<<<<<< HEAD

if __name__ == "__main__":
    print("Test SaveAeroCoefficients")
    print("To run test use the following command:")
    print(">> pytest -v")
=======
if __name__ == "__main__":
    main(verbosity=0)
>>>>>>> general_updates
