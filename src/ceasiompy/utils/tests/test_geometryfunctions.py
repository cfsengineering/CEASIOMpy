"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

import unittest
import numpy as np

from ceasiompy.utils.geometryfunctions import (
    get_aircrafts_list,
    get_profile_coord,
    sum_points,
    prod_points,
    check_if_rotated,
)

from unittest.mock import MagicMock

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestGeometryFunctions(unittest.TestCase):

    @patch("ceasiompy.utils.geometryfunctions.CEASIOMPY_DB_PATH")
    def test_get_aircrafts_list_db_missing(self, MockPath):
        MockPath.exists.return_value = False
        result = get_aircrafts_list()
        self.assertEqual(result, ["Can't use ceasiompy.db"])

    def test_sum_points(self):
        Point = type("Point", (), {})
        p1 = Point()
        p1.x, p1.y, p1.z = 1, 2, 3
        p2 = Point()
        p2.x, p2.y, p2.z = 4, 5, 6
        self.assertEqual(sum_points(p1, p2), (5, 7, 9))

    def test_prod_points(self):
        Point = type("Point", (), {})
        p1 = Point()
        p1.x, p1.y, p1.z = 2, 3, 4
        p2 = Point()
        p2.x, p2.y, p2.z = 5, 6, 7
        self.assertEqual(prod_points(p1, p2), (10, 18, 28))

    def test_check_if_rotated_warns(self):
        Point = type("Point", (), {})
        rot = Point()
        rot.x, rot.y, rot.z = 1, 0, 0
        with patch("ceasiompy.utils.geometryfunctions.log.warning") as mock_warn:
            check_if_rotated(rot, "elem1")
            mock_warn.assert_called_once()

    def test_check_if_rotated_no_warn(self):
        Point = type("Point", (), {})
        rot = Point()
        rot.x, rot.y, rot.z = 0, 0, 0
        with patch("ceasiompy.utils.geometryfunctions.log.warning") as mock_warn:
            check_if_rotated(rot, "elem1")
            mock_warn.assert_not_called()

    def test_get_profile_coord(self):
        # Mock tixi and get_float_vector
        tixi = MagicMock()
        tixi.getTextElement.return_value = "profile1"
        tixi.uIDGetXPath.return_value = "/xpath/profile1"
        tixi.checkElement.return_value = True
        with patch("ceasiompy.utils.geometryfunctions.get_float_vector") as mock_gfv:
            mock_gfv.side_effect = [
                [1.0, 2.0, 3.0],  # x
                [4.0, 5.0, 6.0],  # y
                [7.0, 8.0, 9.0],  # z
            ]
            prof_uid, x, y, z = get_profile_coord(tixi, "/some/uid/xpath")
            self.assertEqual(prof_uid, "profile1")
            np.testing.assert_array_equal(x, np.array([1.0, 2.0, 3.0]))
            np.testing.assert_array_equal(y, np.array([4.0, 5.0, 6.0]))
            np.testing.assert_array_equal(z, np.array([7.0, 8.0, 9.0]))

    def test_get_profile_coord_not_found(self):
        tixi = MagicMock()
        tixi.getTextElement.return_value = "profile1"
        tixi.uIDGetXPath.return_value = "/xpath/profile1"
        tixi.checkElement.return_value = False
        with self.assertRaises(ValueError):
            get_profile_coord(tixi, "/some/uid/xpath")


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main()
