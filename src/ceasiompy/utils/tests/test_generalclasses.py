"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/utils/generalclasses.py'
"""

# Imports

from unittest import main
from unittest.mock import MagicMock
from ceasiompy.utils.ceasiompytest import CeasiompyTest
from ceasiompy.utils.generalclasses import (
    Point,
    Transformation,
    SimpleNamespace,
)

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestGeneralClasses(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_cpacs_points_all_coords(self):
        """Test get_cpacs_points with all coordinates present."""
        tixi = MagicMock()
        xpath = "/some/xpath"
        tixi.checkElement.return_value = True
        tixi.getDoubleElement.side_effect = (
            lambda x: {"x": 1.1, "y": 2.2, "z": 3.3}[x.split("/")[-1]]
        )
        p = Point()
        p.get_cpacs_points(tixi, xpath)
        self.assertEqual(p.x, 1.1)
        self.assertEqual(p.y, 2.2)
        self.assertEqual(p.z, 3.3)

    def test_get_cpacs_points_missing_coord(self):
        """Test get_cpacs_points with one missing coordinate."""
        tixi = MagicMock()
        xpath = "/some/xpath"
        tixi.checkElement.return_value = True

        def get_double(x):
            if x.endswith("/y"):
                raise Exception("Tixi3Exception")
            return {"x": 1.1, "z": 3.3}[x.split("/")[-1]]

        tixi.getDoubleElement.side_effect = get_double
        p = Point()
        with patch("ceasiompy.utils.generalclasses.Tixi3Exception", Exception):
            p.get_cpacs_points(tixi, xpath)
        self.assertEqual(p.x, 1.1)
        self.assertEqual(p.y, 0.0)  # default
        self.assertEqual(p.z, 3.3)

    def test_get_cpacs_points_xpath_missing(self):
        """Test get_cpacs_points when xpath does not exist."""
        tixi = MagicMock()
        xpath = "/not/exist"
        tixi.checkElement.return_value = False
        p = Point()
        with patch("ceasiompy.utils.generalclasses.log.warning") as mock_warn:
            p.get_cpacs_points(tixi, xpath)
            mock_warn.assert_called_once()
        self.assertEqual(p.x, 0.0)
        self.assertEqual(p.y, 0.0)
        self.assertEqual(p.z, 0.0)

    def test_simplenamespace(self):
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

    def test_point(self):
        """Test the class 'Point'"""

        point1 = Point()

        assert point1.x == 0.0
        assert point1.y == 0.0
        assert point1.z == 0.0

        xpath = "/cpacs/vehicles/aircraft/model/fuselages/fuselage/transformation/scaling"
        point1.get_cpacs_points(self.test_cpacs.tixi, xpath)

        assert point1.x == 1.0
        assert point1.y == 1.0
        assert point1.z == 1.0

    def test_transformation(self):
        """Test the class 'Point'"""

        trans1 = Transformation()

        assert trans1.scaling.x == 1.0
        assert trans1.scaling.y == 1.0
        assert trans1.scaling.z == 1.0

        assert trans1.rotation.x == 0.0
        assert trans1.translation.y == 0.0

        xpath = "/cpacs/vehicles/aircraft/model/fuselages/fuselage"
        trans1.get_cpacs_transf(self.test_cpacs.tixi, xpath)

        assert trans1.scaling.x == 1.0
        assert trans1.scaling.y == 1.0
        assert trans1.scaling.z == 1.0
        assert trans1.rotation.x == 0.0
        assert trans1.rotation.y == 0.0
        assert trans1.rotation.z == 0.0
        assert trans1.translation.x == 0.0
        assert trans1.translation.y == 0.0
        assert trans1.translation.z == -0.723764

        trans_wing = Transformation()
        xpath = "/cpacs/vehicles/aircraft/model/wings/wing[0]"
        trans_wing.get_cpacs_transf(self.test_cpacs.tixi, xpath)
        trans_wing.get_parent_transformation()

        assert trans_wing.translation.x == 0.0
        assert trans_wing.translation.y == 0.0
        assert trans_wing.translation.z == 0.0


# Main
if __name__ == "__main__":
    main(verbosity=0)
