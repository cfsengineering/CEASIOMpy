"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/PyAVL/func/avlresults.py'

Python version: >=3.8

| Author : Romain Gauthier
| Creation: 2024-06-07

| Modified: Leon Deligny
| Date: 21 March 2025
=======
>>>>>>> origin/main

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.PyAVL.func.avlresults import get_avl_aerocoefs, plot_lift_distribution
import pytest
import unittest

from ceasiompy.utils.decorators import log_test
from ceasiompy.PyAVL.func.results import get_avl_aerocoefs
from ceasiompy.PyAVL.func.plot import plot_lift_distribution
from ceasiompy.utils.ceasiompyutils import current_workflow_dir

from pathlib import Path
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.PyAVL import *


MODULE_DIR = Path(__file__).parent

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")
FT_TEMPLATE = Path(MODULE_DIR, "ft_template.txt")


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestAvlResults(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        cls.force_file_fs = Path(MODULE_DIR, "tests", "fs_template.txt")
        cls.wkdir = current_workflow_dir()
        cls.ft_template = Path(MODULE_DIR, "tests", "st_template.txt")

    @log_test
    def test_template(self) -> None:
        assert self.ft_template.exists(), "Result file 'ft.txt' not found!"

    @log_test
    def test_module_template_functions(self) -> None:
        self.assert_equal_function(
            f=get_avl_aerocoefs,
            input=(self.ft_template,),
            expected=(
                0.00119, 0.00008, 0.18118,
                0.00001, -0.66525, -0.00009,
                -0.156791, -24.343220, 0.410176,
            ),
        )

    @log_test
    def test_plot_lift_distribution(self):
        plot_lift_distribution(
            force_file_fs=self.force_file_fs,
            aoa=5,
            aos=0,
            mach=0.3,
            alt=1000,
            wkdir=self.wkdir,
        )

        assert Path(
            self.wkdir, "lift_distribution.png"
        ).exists(), "Plot 'lift_distribution.png' does not exist."


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_plot_lift_distribution(tmp_path):
    plot_lift_distribution(
        force_file_fs=Path(MODULE_DIR, "fs_template.txt"),
        aoa=5,
        aos=0,
        mach=0.3,
        alt=1000,
        wkdir=tmp_path,
    )

    assert Path(
        tmp_path, "lift_distribution.png"
    ).exists(), "Plot 'lift_distribution.png' does not exist."


def test_get_avl_aerocoefs():
    assert FT_TEMPLATE.exists(), "Result file 'ft.txt' not found!"
    cl, cd, cm = get_avl_aerocoefs(FT_TEMPLATE)
    assert cl == pytest.approx(0.35063, rel=1e-4), "CLtot is not correct!"
    assert cd == pytest.approx(0.00624, rel=1e-4), "CDtot is not correct!"
    assert cm == pytest.approx(-0.01362, rel=1e-4), "Cmtot is not correct!"


# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":
    unittest.main(verbosity=0)

if __name__ == "__main__":
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
