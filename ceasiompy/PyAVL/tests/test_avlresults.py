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

MODULE_DIR = Path(__file__).parent
AVL_TEST_DIR = Path(MODULE_DIR, "AVLpytest")

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_directory():
    Path(AVL_TEST_DIR).mkdir(exist_ok=True)


def test_run_avl():
    run_avl(CPACS_IN_PATH, AVL_TEST_DIR)


def test_get_avl_aerocoefs():
    FT_TEMPLATE = Path(MODULE_DIR, "ft_template.txt")

    assert FT_TEMPLATE.exists(), "Result file ft.txt not found!"
    cl, cd, cm = get_avl_aerocoefs(FT_TEMPLATE)
    assert cl == pytest.approx(0.35063, rel=1e-4), "CLtot is not correct!"
    assert cd == pytest.approx(0.00624, rel=1e-4), "CDtot is not correct!"
    assert cm == pytest.approx(-0.01362, rel=1e-4), "Cmtot is not correct!"


def test_delete_directory():
    shutil.rmtree(AVL_TEST_DIR)
    shutil.rmtree(Path(MODULE_DIR, "Results"))


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
