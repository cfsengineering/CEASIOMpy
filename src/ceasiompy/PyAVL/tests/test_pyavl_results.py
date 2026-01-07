"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for results.py
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.PyAVL.func.results import get_avl_aerocoefs
from ceasiompy.utils.ceasiompyutils import current_workflow_dir

from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.PyAVL import MODULE_DIR

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
    def test_get_avl_aerocoefs(self) -> None:
        self.assert_equal_function(
            f=get_avl_aerocoefs,
            input_args=(self.ft_template,),
            expected=(
                0.00119,
                0.00008,
                0.18118,
                0.00001,
                -0.66525,
                -0.00009,
                -0.0027365191874944295,
                -0.424869339537334,
                0.007158921712660261,
            ),
        )


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
