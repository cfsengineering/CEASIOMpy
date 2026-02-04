"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for config.py
"""

# Imports

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.decorators import log_test
from ceasiompy.PyAVL.func.config import (
    write_command_file,
    retrieve_gui_values,
    get_physics_conditions,
)
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_selected_aeromap_values,
)

from pathlib import Path
from unittest import main
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH
from ceasiompy.PyAVL import (
    MODULE_DIR,
    AVL_DISTR_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_ROTRATES_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_EXPAND_VALUES_XPATH,
    AVL_FREESTREAM_MACH_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestPyAVLConfig(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        cpacs_path = Path(CPACS_FILES_PATH, "lab_ar_scaled.xml")
        cls.cpacs = CPACS(cpacs_path)
        cls.wkdir = current_workflow_dir()
        cls.command_dir = Path(MODULE_DIR, "tests", "avl_command_template.txt")
        cls.avl_path = Path(MODULE_DIR, "tests", "aircraft.avl")

        # Ensure there is a selected aeromap
        create_branch(cls.cpacs.tixi, xpath=SELECTED_AEROMAP_XPATH)
        cls.cpacs.tixi.updateTextElement(SELECTED_AEROMAP_XPATH, "aeromap_empty")

    @log_test
    def test_retrieve_gui_values(self):
        tixi = self.cpacs.tixi

        create_branch(tixi, xpath=AVL_FUSELAGE_XPATH)
        tixi.updateBooleanElement(AVL_FUSELAGE_XPATH, False)

        create_branch(tixi, xpath=AVL_EXPAND_VALUES_XPATH)
        tixi.updateBooleanElement(AVL_EXPAND_VALUES_XPATH, False)

        create_branch(tixi, xpath=AVL_NCHORDWISE_XPATH)
        tixi.updateIntegerElement(AVL_NCHORDWISE_XPATH, 1, "%d")

        create_branch(tixi, xpath=AVL_NSPANWISE_XPATH)
        tixi.updateIntegerElement(AVL_NSPANWISE_XPATH, 1, "%d")

        create_branch(tixi, xpath=AVL_DISTR_XPATH)
        tixi.updateTextElement(AVL_DISTR_XPATH, "cosine")

        create_branch(tixi, xpath=AVL_ROTRATES_XPATH)
        tixi.updateDoubleElement(AVL_ROTRATES_XPATH, 0.0, "%g")

        create_branch(tixi, xpath=AVL_FREESTREAM_MACH_XPATH)
        tixi.updateDoubleElement(AVL_FREESTREAM_MACH_XPATH, 0.6, "%g")

        create_branch(tixi, xpath=AVL_CTRLSURF_ANGLES_XPATH)
        tixi.updateDoubleElement(AVL_CTRLSURF_ANGLES_XPATH, 0.0, "%g")

        result = retrieve_gui_values(self.cpacs, self.wkdir)

        assert result[0] == [1000.0]
        assert result[1] == [0.3]
        assert result[2] == [5.0]
        assert result[3] == [0.0]
        assert result[4] == [0.0]
        assert result[5] == [0.0]
        assert result[6] == Path(str(self.wkdir) + "/" + self.cpacs.ac_name + ".avl")

    @log_test
    def test_get_selected_aeromap_values(self) -> None:
        self.assert_equal_function(
            f=get_selected_aeromap_values,
            input_args=(self.cpacs, ),
            expected=([1000.0], [0.3], [5.0], [0.0]),
        )

    @log_test
    def test_write_command_file(self):
        mach = 0.3
        (
            roll_rate_star, pitch_rate_star, yaw_rate_star,
            ref_density, g_acceleration, ref_velocity,
        ) = get_physics_conditions(
            self.cpacs.tixi,
            alt=1000.0,
            mach=mach,
            roll_rate=0.0,
            pitch_rate=0.0,
            yaw_rate=0.0,
        )

        write_command_file(
            avl_path=self.avl_path,
            case_dir_path=self.wkdir,
            ref_density=ref_density,
            g_acceleration=g_acceleration,
            ref_velocity=ref_velocity,
            alpha=5.0,
            beta=0.0,
            pitch_rate_star=pitch_rate_star,
            roll_rate_star=roll_rate_star,
            yaw_rate_star=yaw_rate_star,
            mach_number=mach,
            aileron=0.0,
            elevator=0.0,
            rudder=0.0,
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


# Main

if __name__ == "__main__":
    main(verbosity=0)
