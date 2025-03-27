"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/PyAVL/func/avlconfig.py'

Python version: >=3.8

| Author : Romain Gauthier
| Creation: 2024-06-06
| Modified: Leon Deligny
| Date: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest

from pathlib import Path

from ceasiompy.utils.decorators import log_test

from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_aeromap_conditions, 
)
from ceasiompy.PyAVL.func.config import (
    write_command_file,
    get_option_settings,
)

from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.commonxpath import AVL_AEROMAP_UID_XPATH

from ceasiompy.PyAVL import *

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
    def test_module_template_functions(self) -> None:
        self.assert_equal_function(
            f=get_aeromap_conditions,
            input=(self.cpacs, AVL_AEROMAP_UID_XPATH),
            expected=([1000.0], [0.3], [5.0], [0.0]),
        )

    @log_test
    def test_get_option_settings(self):
        (
            save_plots,
            vortex_distribution,
            Nchordwise,
            Nspanwise,
            integrate_fuselage,
            rotation_rates_float,

        ) = get_option_settings(self.cpacs.tixi)

        assert not save_plots, "Option 'save_plots' should be 'False'."
        assert vortex_distribution == 3.0, "Option 'vortex_distribution' should be '3.0'."
        assert Nchordwise == 5, "Option 'Nchordwise' should be '5'."
        assert Nspanwise == 20, "Option 'Nspanwise' should be '20'."
        assert not integrate_fuselage, "Option 'integrate_fuselage' should be 'False'."
        assert rotation_rates_float == 0.0, "Option 'rotation_rates_float' should be 0.0"

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
            ref_velocity=100.93037463067732,
            ref_density=1.1116596736996904,
            g_acceleration=9.803565306802405,
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
    unittest.main(verbosity=0)
