"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for volumesdefinition (unconventional aircraft wings geometry).

| Author: [Your Name]
| Creation: [Today's Date]
"""

# =============================================================================
#   IMPORTS
# =============================================================================

import unittest
import numpy as np
from unittest.mock import MagicMock, patch

from ceasiompy.utils.WB.UncGeometry.NoFuseGeom import volumesdefinition

# =============================================================================
#   MOCK CLASSES
# =============================================================================


class MockAWG:
    def __init__(self):
        self.main_wing_index = 1
        self.w_seg_sec = np.array([[[1, 1, 1], [0, 0, 0]]])
        self.wing_seg_length = np.array([[1.0]])
        self.wing_center_seg_point = np.zeros((1, 1, 3))
        self.wing_sym = [0]
        self.y_max_cabin = 0.0
        self.cabin_area = 0.0
        self.cabin_span = 0.0
        self.fuse_vol = 0.0
        self.cabin_vol = 0.0
        self.fuse_fuel_vol = 0.0
        self.wing_fuel_vol = 0.0
        self.fuel_vol_tot = 0.0
        self.wing_vol = [10.0]


# =============================================================================
#   TESTS
# =============================================================================


class TestVolumesDefinition(unittest.TestCase):

    @patch("ceasiompy.utils.WB.UncGeometry.NoFuseGeom.volumesdefinition.open_tixi")
    @patch("ceasiompy.utils.WB.UncGeometry.NoFuseGeom.volumesdefinition.open_tigl")
    def test_wing_check_thickness(self, mock_open_tigl, mock_open_tixi):
        awg = MockAWG()
        cpacs_in = "dummy.xml"
        TP = False

        # Mock tigl methods to return simple, consistent values
        mock_tigl = MagicMock()
        mock_open_tigl.return_value = mock_tigl
        mock_open_tixi.return_value = MagicMock()

        mock_tigl.wingGetLowerPoint.side_effect = lambda w, i, et, ze: (et + ze, 1.0, ze)
        mock_tigl.wingGetUpperPoint.side_effect = lambda w, i, et, ze: (et + ze, 1.0, ze + 1.0)

        awg, wing_nodes = volumesdefinition.wing_check_thickness(
            h_min=0.5, awg=awg, cpacs_in=cpacs_in, TP=TP, FUEL_ON_CABIN=10
        )

        self.assertTrue(hasattr(awg, "cabin_area"))
        self.assertTrue(hasattr(awg, "fuse_vol"))
        self.assertTrue(hasattr(awg, "cabin_vol"))
        self.assertTrue(hasattr(awg, "wing_fuel_vol"))
        self.assertIsInstance(wing_nodes, np.ndarray)


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=0)
