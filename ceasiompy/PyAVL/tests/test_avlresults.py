"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/PyAVL/func/avlresults.py'

Python version: >=3.8

| Author : Romain Gauthier
| Creation: 2024-06-07

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================
import shutil
from pathlib import Path
import pytest
from ceasiompy.PyAVL.avlrun import run_avl
from ceasiompy.PyAVL.func.avlresults import get_avl_aerocoefs

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


def test_get_avl_aerocoefs():
    wkdir = Path.cwd() / "AVLpytest/Case00_alt1000.0_mach0.3_aoa5.0_aos0.0"
    assert (wkdir / "ft.txt").exists(), "Result file ft.txt not found!"
    cl, cd, cm = get_avl_aerocoefs((wkdir / "ft.txt"))
    assert cl == pytest.approx(0.70018, rel=1e-4), "CLtot is not correct!"
    assert cd == pytest.approx(0.02494, rel=1e-4), "CDtot is not correct!"
    assert cm == pytest.approx(-0.02723, rel=1e-4), "Cmtot is not correct!"


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
