"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for Unconventional Geometry module (No Fuselage).
"""

# =============================================================================
#   IMPORTS
# =============================================================================

import unittest
import numpy as np

from ceasiompy.utils.WB.UncGeometry.NoFuseGeom.bwbwingsanalysis import (
    getwingsegmentlength,
    check_segment_connection,
)

from unittest.mock import MagicMock

# =============================================================================
#   MOCK CLASSES
# =============================================================================


class MockAWG:
    def __init__(self):
        self.w_nb = 1
        self.wing_nb = 1
        self.wing_seg_nb = [1]
        self.wing_sym = [0]
        self.wing_plt_area = [10.0]
        self.wing_vol = []
        self.is_horiz = []
        self.wing_sec_nb = []
        self.wing_seg_nb = [1]
        self.wing_plt_area = [10.0]
        self.wing_tot_vol = 0.0
        self.wing_max_chord = []
        self.wing_min_chord = []
        self.wing_mac = []
        self.wing_sec_thickness = []
        self.wing_sec_mean_thick = []
        self.wing_span = []
        self.main_wing_index = 0
        self.wing_center_seg_point = None
        self.wing_seg_vol = None


# =============================================================================
#   TESTS
# =============================================================================

class TestNoFuseGeom(unittest.TestCase):

    def test_check_segment_connection(self):
        awg = MockAWG()
        wing_plt_area_xz = [5.0]
        wing_plt_area_yz = [2.0]
        tigl = MagicMock()
        tigl.wingGetInnerSectionAndElementIndex.return_value = (1, 1)
        tigl.wingGetOuterSectionAndElementIndex.return_value = (2, 1)
        tigl.wingGetChordPoint.return_value = (0.0, 0.0, 0.0)
        sec_nb, start_index, seg_sec_reordered, sec_index = check_segment_connection(
            wing_plt_area_xz, wing_plt_area_yz, awg, tigl
        )
        self.assertEqual(sec_nb, [2])
        self.assertEqual(start_index, [1])
        self.assertEqual(seg_sec_reordered.shape, (1, 1, 3))
        self.assertEqual(sec_index.shape, (2, 1))

    def test_getwingsegmentlength(self):
        awg = MockAWG()
        awg.wing_seg_nb = [1]
        awg.wing_nb = 1
        wing_center_section_point = np.array([
            [[0.0, 0.0, 0.0]],
            [[1.0, 0.0, 0.0]]
        ])
        awg.wing_sym = [0]
        awg = getwingsegmentlength(awg, wing_center_section_point)
        self.assertTrue(np.allclose(awg.wing_seg_length, np.array([[1.0]])))


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=0)
