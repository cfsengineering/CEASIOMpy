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
from ceasiompy.PyAVL.func.avlconfig import get_aeromap_conditions

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH


CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================
def test_directory():
    wkdir = Path.cwd() / "AVLpytest"
    Path(wkdir).mkdir(exist_ok=True)


def test_run_avl():
    wkdir = Path.cwd() / "AVLpytest"
    run_avl(CPACS_IN_PATH, wkdir)


def test_write_command_file():
    wkdir = Path.cwd() / "AVLpytest/Case00_alt1000.0_mach0.3_aoa5.0_aos0.0"
    print("##############", wkdir)
    file_found = Path(wkdir).joinpath("avl_commands.txt").exists()
    assert file_found, "AVL command file not found!"

    if file_found:
        with open(Path(wkdir).joinpath("avl_commands.txt"), "r") as file:
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


def test_results_files(tmp_path):
    wkdir = Path.cwd() / "AVLpytest/Case00_alt1000.0_mach0.3_aoa5.0_aos0.0"
    print("############## Current Working Directory:", Path.cwd())
    print("############## Expected Working Directory:", wkdir)

    if not wkdir.exists():
        print(f"Directory {wkdir} does not exist!")
        assert False, f"Directory {wkdir} does not exist!"

    # List all files in the directory
    print("############## Listing all files in the directory:")
    for path in wkdir.iterdir():
        print(path)

    for file in ["ft", "fs", "fe", "fn", "st"]:
        file_path = wkdir / f"{file}.txt"
        print(f"Checking if {file_path} exists...")
        file_found = file_path.exists()
        assert file_found, f"Result file {file}.txt not found!"


def test_save_fig():
    wkdir = Path.cwd() / "AVLpytest"  # /Case00_alt1000.0_mach0.3_aoa5.0_aos0.0"
    print("##############", wkdir)
    file_found = Path(wkdir).joinpath("plot.ps").exists()
    assert file_found, "AVL ps plot not found!"


def test_get_aeromap_conditions():
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(CPACS_IN_PATH)
    assert alt_list[0] == 1000.0, "Altitude from aeromap not correct, should be 1000.0 meters."
    assert mach_list[0] == 0.3, "Mach number from aeromap not correct, should be 0.3."
    assert aoa_list[0] == 5.0, "Aoa from aeromap not correct, should be 5.0 degrees."
    assert aos_list[0] == 0.0, "Altitude from aeromap not correct, should be 0.0 degrees"


def test_delete_directory():
    shutil.rmtree(Path.cwd() / "AVLpytest")
    shutil.rmtree(Path.cwd() / "Results")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
