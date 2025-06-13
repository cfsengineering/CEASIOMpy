import unittest

from ceasiompy.utils.WB.UncGeometry.WithFuseGeom.Wings.wingsgeom import (
    check_segment_connection,
)


class MockAWG:
    def __init__(self):
        self.w_nb = 1
        self.wing_nb = 1
        self.wing_seg_nb = [2]
        self.wing_plt_area = [10.0]
        self.wing_sym = [0]


class MockTigl:
    def __init__(self):
        # Simulate a wing with 2 segments and 3 sections
        self.inner_sections = {(1, 1): (1, 0), (1, 2): (2, 0)}
        self.outer_sections = {(1, 1): (2, 0), (1, 2): (3, 0)}
        self.chord_points = {
            (1, 1, 0.0, 0.0): (0.0, 0.0, 0.0),
            (1, 2, 0.0, 0.0): (1.0, 0.0, 0.0),
            (1, 1, 1.0, 0.0): (0.5, 1.0, 0.0),
            (1, 2, 1.0, 0.0): (1.5, 2.0, 0.0),
        }

    def wingGetInnerSectionAndElementIndex(self, i, j):
        return self.inner_sections[(i, j)]

    def wingGetOuterSectionAndElementIndex(self, i, j):
        return self.outer_sections[(i, j)]

    def wingGetChordPoint(self, i, j, eta, zeta):
        return self.chord_points.get((i, j, eta, zeta), (float(j), eta, zeta))


class TestWingsGeom(unittest.TestCase):

    def test_check_segment_connection(self):
        awg = MockAWG()
        tigl = MockTigl()
        wing_plt_area_xz = [5.0]
        wing_plt_area_yz = [2.0]
        sec_nb, start_index, seg_sec_reordered, sec_index = check_segment_connection(
            wing_plt_area_xz, wing_plt_area_yz, awg, tigl
        )
        self.assertEqual(sec_nb[0], 3)
        self.assertEqual(start_index[0], 1)
        self.assertEqual(seg_sec_reordered.shape, (2, 1, 3))
        self.assertEqual(sec_index.shape, (3, 1))


if __name__ == "__main__":
    unittest.main()
