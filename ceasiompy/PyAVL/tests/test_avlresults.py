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
from pathlib import Path
import pytest
from ceasiompy.PyAVL.func.avlresults import get_avl_aerocoefs, plot_lift_distribution

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "labARscaled.xml")
FT_TEMPLATE = Path(MODULE_DIR, "ft_template.txt")

# =================================================================================================
#   CLASSES
# =================================================================================================


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
    print("Test avlconfig.py")
    print("To run test use the following command:")
    print(">> pytest -v")
