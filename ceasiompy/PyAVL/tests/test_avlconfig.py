"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/PyAVL/func/avlconfig.py'

Python version: >=3.8

| Author : Romain Gauthier
| Creation: 2024-06-06
<<<<<<< HEAD
| Modified: Leon Deligny
| Date: 21 March 2025
=======
>>>>>>> origin/main

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

<<<<<<< HEAD
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
=======
from pathlib import Path

from ceasiompy.PyAVL.func.avlconfig import (
    get_aeromap_conditions,
    get_option_settings,
    write_command_file,
)
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")

MODULE_DIR = Path(__file__).parent
CASE_DIR = Path(MODULE_DIR, "AVLpytest")
COMMAND_TEM_DIR = Path(MODULE_DIR, "avl_command_template.txt")
>>>>>>> origin/main

# =================================================================================================
#   CLASSES
# =================================================================================================


<<<<<<< HEAD
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
=======
# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_write_command_file(tmp_path):
    test_path = Path("/path", "to", "avl", "input", "file", "aircraft.avl")

    write_command_file(
        avl_path=test_path,
        case_dir_path=tmp_path,
        alpha=5.0,
        beta=0.0,
        mach_number=0.3,
        ref_velocity=100.93037463067732,
        ref_density=1.1116596736996904,
        g_acceleration=9.803565306802405,
        save_plots=True,
    )

    file_exists = Path(tmp_path, "avl_commands.txt").exists()
    assert file_exists, "File 'avl_commands.txt' not found."

    if file_exists:
        COMMAND_DIR = Path(tmp_path, "avl_commands.txt")
        with open(COMMAND_TEM_DIR, "r") as file1, open(COMMAND_DIR, "r") as file2:
            for line1, line2 in zip(file1, file2):
                if "mass" not in line1:
                    assert line1 == line2, "File 'avl_commands.txt' not correct."

            # Check for any remaining lines in either file
            assert not file1.read() or not file2.read(), "File 'avl_commands.txt' not correct."


def test_get_aeromap_conditions():
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(CPACS_IN_PATH)
    assert alt_list[0] == 1000.0, "Altitude from aeromap not correct, should be 1000.0 meters."
    assert mach_list[0] == 0.3, "Mach number from aeromap not correct, should be 0.3."
    assert aoa_list[0] == 5.0, "Aoa from aeromap not correct, should be 5.0 degrees."
    assert aos_list[0] == 0.0, "Altitude from aeromap not correct, should be 0.0 degrees"


def test_get_option_settings():
    (
        save_plots,
        vortex_distribution,
        Nchordwise,
        Nspanwise,
        integrate_fuselage,
    ) = get_option_settings(CPACS_IN_PATH)

    assert not save_plots, "Option 'save_plots' should be 'False'."
    assert vortex_distribution == 3.0, "Option 'vortex_distribution' should be '3.0'."
    assert Nchordwise == 5, "Option 'Nchordwise' should be '5'."
    assert Nspanwise == 20, "Option 'Nspanwise' should be '20'."
    assert not integrate_fuselage, "Option 'integrate_fuselage' should be 'False'."
>>>>>>> origin/main


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
<<<<<<< HEAD
    unittest.main(verbosity=0)
=======
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
>>>>>>> origin/main
