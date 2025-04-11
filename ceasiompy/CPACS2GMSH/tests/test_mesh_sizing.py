"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/mesh_sizing.py'


| Author : Giacomo Benedetti
| Creation: 2023-11-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from cpacspy.cpacspy import CPACS
from pytest import approx
from ceasiompy.CPACS2GMSH.func.mesh_sizing import fuselage_size, wings_size
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_fuselage_size():
    """
    This test takes the fuselage dimension from simpletest_cpacs.xml,
    on which the mesh size is calculated
    """

    fuselage_maxlen, fuselage_minlen = fuselage_size(CPACS(CPACS_IN_PATH).tixi)

    assert fuselage_maxlen == approx(0.5, abs=1e-2)
    assert fuselage_minlen == approx(0.05, abs=1e-3)


def test_wing_size():
    """
    This test takes the fuselage dimension from simpletest_cpacs.xml,
    on which the mesh size is calculated
    """

    wing_maxlen, wing_minlen = wings_size(CPACS(CPACS_IN_PATH).tixi)

    assert wing_maxlen == approx(0.15, abs=1e-2)
    assert wing_minlen == approx(0.012, abs=1e-4)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
