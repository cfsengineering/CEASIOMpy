"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for config.py
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.PyAVL.func.config import write_command_file
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_aeromap_conditions,
)

from pathlib import Path
from unittest import main
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.PyAVL import (
    MODULE_DIR,
    AVL_AEROMAP_UID_XPATH,
)


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestModuleTemplate(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        cpacs_path = Path(CPACS_FILES_PATH, "labARscaled.xml")
        cls.cpacs = CPACS(cpacs_path)
        cls.wkdir = current_workflow_dir()
        cls.command_dir = Path(MODULE_DIR, "tests", "avl_command_template.txt")
        cls.avl_path = Path(MODULE_DIR, "tests", "aircraft.avl")

    @log_test
    def test_get_aeromap_conditions(self) -> None:
        self.assert_equal_function(
            f=get_aeromap_conditions,
            input_args=(self.cpacs, AVL_AEROMAP_UID_XPATH),
            expected=([1000.0], [0.3], [5.0], [0.0]),
        )

    @log_test
    def test_write_command_file(self):

        write_command_file(
            tixi=self.cpacs.tixi,
            avl_path=self.avl_path,
            case_dir_path=self.wkdir,
            alpha=5.0,
            beta=0.0,
            pitch_rate=0.0,
            roll_rate=0.0,
            yaw_rate=0.0,
            mach_number=0.3,
            alt=1000.0,
            aileron=0.0,
            elevator=0.0,
            rudder=0.0,
            save_plots=True,
        )

        file_exists = Path(self.wkdir, "avl_commands.txt").exists()
        assert file_exists, "File 'avl_commands.txt' not found."

        if file_exists:
            self.command_dir = Path(self.wkdir, "avl_commands.txt")
            with open(self.command_dir, "r") as file1, open(self.command_dir, "r") as file2:
                for line1, line2 in zip(file1, file2):
                    if "mass" not in line1:
                        assert line1 == line2, "File 'avl_commands.txt' not correct."

                # Check for any remaining lines in either file
                assert not file1.read() or not file2.read(), "File 'avl_commands.txt' not correct."


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
