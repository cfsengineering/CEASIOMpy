import unittest
import ceasiompy.utils.WB.UncGeometry.uncgeomanalysis as uncgeometry

from ceasiompy.utils.WB.UncGeometry.uncgeomanalysis import (
    get_number_of_parts,
    no_fuse_geom_analysis,
    with_fuse_geom_analysis,
)


class MockTixi:
    def __init__(self, fus_nb=1, wing_nb=2):
        self._fus_nb = fus_nb
        self._wing_nb = wing_nb
        self.saved = False

    def checkElement(self, xpath):
        if "fuselages" in xpath:
            return self._fus_nb > 0
        if "wings" in xpath:
            return self._wing_nb > 0
        return False

    def getNamedChildrenCount(self, xpath, name):
        if "fuselages" in xpath:
            return self._fus_nb
        if "wings" in xpath:
            return self._wing_nb
        return 0

    def save(self, cpacs_in):
        self.saved = True


def mock_open_tixi(cpacs_in):
    return MockTixi(fus_nb=2, wing_nb=3)


class TestUncGeometry(unittest.TestCase):

    def setUp(self):
        # Patch open_tixi in the module under test
        self.orig_open_tixi = uncgeometry.open_tixi
        uncgeometry.open_tixi = mock_open_tixi

    def tearDown(self):
        uncgeometry.open_tixi = self.orig_open_tixi

    def test_get_number_of_parts(self):
        fus_nb, wing_nb = get_number_of_parts("dummy.xml")
        self.assertEqual(fus_nb, 2)
        self.assertEqual(wing_nb, 3)

    # The following are smoke tests for the analysis functions
    def test_no_fuse_geom_analysis(self):
        # Patch dependencies for a smoke test
        uncgeometry.geom_eval = lambda wing_nb, awg, cpacs_in: awg
        uncgeometry.wing_check_thickness = (
            lambda h_min, awg, cpacs_in, TP, FUEL_ON_CABIN: (awg, [[0, 0, 0]])
        )
        uncgeometry.produce_wing_output_txt = lambda awg, NAME: None
        result = no_fuse_geom_analysis("dummy.xml", 1, 2, 1.0, 0.5, "Test", False)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_with_fuse_geom_analysis(self):
        # Patch dependencies for a smoke test
        class DummyAdUI:
            VRT_THICK = 0.1
        uncgeometry.wing_geom_eval = lambda wing_nb, TP, awg, cpacs_in: awg
        uncgeometry.fuse_geom_eval = lambda fus_nb, h_min, VRT_THICK, F_FUEL, afg, cpacs_in: afg
        uncgeometry.produce_geom_output_txt = lambda afg, awg, NAME: None
        result = with_fuse_geom_analysis(
            "dummy.xml", 1, 2, 1.0, DummyAdUI(), False, [False], "Test"
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
