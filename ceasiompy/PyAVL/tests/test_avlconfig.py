"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/PyAVL/func/avlconfig.py'

Python version: >=3.8

| Author : Romain Gauthier
| Creation: 2024-06-06

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================
import shutil
from pathlib import Path
import pytest
from ambiance import Atmosphere
from ceasiompy.PyAVL.avlrun import run_avl
from ceasiompy.PyAVL.func.avlconfig import (
    get_aeromap_conditions,
    get_option_settings
)
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH


CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")

MODULE_DIR = Path(__file__).parent
CASE_DIR = Path(MODULE_DIR, "AVLpytest")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_run_avl():
    Path(MODULE_DIR, "AVLpytest").mkdir(parents=True, exist_ok=True)
    run_avl(CPACS_IN_PATH, CASE_DIR)


def test_write_command_file():
    file_found = (
        Path(CASE_DIR, "Case00_alt1000.0_mach0.3_aoa5.0_aos0.0")
        .joinpath("avl_commands.txt")
        .exists()
    )
    assert file_found, "AVL command file not found!"

    if file_found:
        with open(
            Path(CASE_DIR, "Case00_alt1000.0_mach0.3_aoa5.0_aos0.0").joinpath("avl_commands.txt"),
            "r",
        ) as file:
            for line in file:
                if "a a" in line:
                    assert float(line.split()[2]) == 5.0, "AoA should be 5"
                elif "b b" in line:
                    assert float(line.split()[2]) == 0.0, "AoS should be 0"
                elif "mn" in line:
                    assert float(line.split()[1]) == 0.3, "Mach number should be 0.3"
                elif "g " in line:
                    g_acc = Atmosphere(1000).grav_accel[0]
                    assert float(line.split()[1]) == pytest.approx(
                        g_acc, rel=1e-4
                    ), "Gravitational acceleration is not correct."
                elif "d " in line and "load" not in line:
                    density = Atmosphere(1000).density[0]
                    assert float(line.split()[1]) == pytest.approx(
                        density, rel=1e-4
                    ), "Density is not correct."
                elif "v " in line:
                    velocity = Atmosphere(1000).speed_of_sound[0] * 0.3
                    assert float(line.split()[1]) == pytest.approx(
                        velocity, rel=1e-4
                    ), "Velocity is not correct."


def test_get_aeromap_conditions():
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(CPACS_IN_PATH)
    assert alt_list[0] == 1000.0, "Altitude from aeromap not correct, should be 1000.0 meters."
    assert mach_list[0] == 0.3, "Mach number from aeromap not correct, should be 0.3."
    assert aoa_list[0] == 5.0, "Aoa from aeromap not correct, should be 5.0 degrees."
    assert aos_list[0] == 0.0, "Altitude from aeromap not correct, should be 0.0 degrees"


def test_delete_directory():
    directories_to_delete = ["AVLpytest", "Results"]

    for dir_name in directories_to_delete:
        dir_path = Path.cwd() / dir_name

        try:
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                print(f"Directory {dir_path} deleted successfully.")
            else:
                print(f"Directory {dir_path} does not exist.")

            assert not dir_path.exists(), f"Directory {dir_path} was not deleted."

        except Exception as e:
            print(f"An error occurred while deleting {dir_path}: {e}")
            raise


def test_get_option_settings():
    save_plots, vortex_distribution, Nchordwise, Nspanwise, integrate_fuselage = get_option_settings(
        CPACS_IN_PATH)
    assert save_plots, "Option 'save_plots' should be 'True'."
    assert vortex_distribution == 3.0, "Option 'vortex_distribution' should be '3.0'."
    assert Nchordwise == 5, "Option 'Nchordwise' should be '5'."
    assert Nspanwise == 20, "Option 'Nspanwise' should be '20'."
    assert not integrate_fuselage, "Option 'integrate_fuselage' should be 'False'."

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
