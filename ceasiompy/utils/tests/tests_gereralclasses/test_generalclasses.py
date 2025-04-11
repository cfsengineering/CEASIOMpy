"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/utils/generalclasses.py'



| Author : Aidan Jungo
| Creation: 2021-12-13

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.generalclasses import Point, SimpleNamespace, Transformation
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
CPACS_PATH = Path(MODULE_DIR, "simpletest_cpacs.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_SimpleNamespace():
    """Test the class 'SimpleNamespace'"""

    namespace = SimpleNamespace()

    namespace.test1 = 1
    namespace.test2 = "two"
    namespace.test3 = [1.2, 1.3, 1.4]

    assert namespace.test1 == 1
    assert namespace.test2 == "two"
    assert namespace.test3 == [1.2, 1.3, 1.4]

    namespace2 = SimpleNamespace()
    namespace2.test1 = 1
    namespace3 = SimpleNamespace()
    namespace3.test1 = 1

    assert namespace2 == namespace3


def test_Point():
    """Test the class 'Point'"""

    cpacs = CPACS(CPACS_PATH)
    tixi = cpacs.tixi

    point1 = Point()

    assert point1.x == 0.0
    assert point1.y == 0.0
    assert point1.z == 0.0

    xpath = "/cpacs/vehicles/aircraft/model/fuselages/fuselage/transformation/scaling"
    point1.get_cpacs_points(tixi, xpath)

    assert point1.x == 1.0
    assert point1.y == 0.5
    assert point1.z == 0.5


def test_Transformation():
    """Test the class 'Point'"""

    cpacs = CPACS(CPACS_PATH)
    tixi = cpacs.tixi

    trans1 = Transformation()

    assert trans1.scaling.x == 1.0
    assert trans1.scaling.y == 1.0
    assert trans1.scaling.z == 1.0

    assert trans1.rotation.x == 0.0
    assert trans1.translation.y == 0.0

    xpath = "/cpacs/vehicles/aircraft/model/fuselages/fuselage"
    trans1.get_cpacs_transf(tixi, xpath)

    assert trans1.scaling.x == 1.0
    assert trans1.scaling.y == 0.5
    assert trans1.scaling.z == 0.5
    assert trans1.rotation.x == 0.1
    assert trans1.rotation.y == 0.2
    assert trans1.rotation.z == 0.3
    assert trans1.translation.x == 0.4
    assert trans1.translation.y == 0.5
    assert trans1.translation.z == 0.6

    trans_wing = Transformation()
    xpath = "/cpacs/vehicles/aircraft/model/wings/wing"
    trans_wing.get_cpacs_transf(tixi, xpath)
    trans_wing.get_parent_transformation()

    assert trans_wing.translation.x == 0.4
    assert trans_wing.translation.y == 0.5
    assert trans_wing.translation.z == 0.6


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
