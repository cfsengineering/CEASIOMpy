"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

<<<<<<< HEAD
Test the module CPACS2SUMO (lib/CPACS2SUMO/cpacs2sumo.py')

| Author : Aidan Jungo
| Creation: 2018-10-26

TODO:

    * Create tests for this module

=======
Test the module CPACS2SUMO
>>>>>>> general_updates
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
<<<<<<< HEAD
=======
import unittest

from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord
from ceasiompy.CPACS2SUMO.func.sumofunctions import (
    add_wing_cap,
    sumo_str_format,
    sumo_add_engine_bc,
    sumo_add_nacelle_lip,
)

from unittest.mock import MagicMock
from ceasiompy.utils.ceasiompytest import CeasiompyTest
>>>>>>> general_updates
from ceasiompy.CPACS2SUMO.func.cst2coord import CST_shape

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


<<<<<<< HEAD
def test_cst2coord():

    # Simple 4 points profile with default values
    airfoil_CST = CST_shape(N=4)
    airfoil_CST.airfoil_coor()

    assert airfoil_CST.x_list == pytest.approx([1.0, 0.5, 0.0, 0.5], rel=1e-5)
    assert airfoil_CST.y_list == pytest.approx([0.0, -0.35355, 0.0, 0.35355], rel=1e-3)

    # More complex profile

    wu = [0.2, 0.45, -0.12, 1.0, -0.473528, 0.95, 0.14, 0.38, 0.11, 0.38]
    wl = [-0.13, 0.044, -0.38, 0.43, -0.74, 0.54, -0.51, 0.10, -0.076, 0.062]
    dz = 0.00
    N = 10

    airfoil_CST = CST_shape(wl, wu, dz, N)
    airfoil_CST.airfoil_coor()

    x_true_values = [1.0, 0.9045, 0.6545, 0.3454, 0.0954, 0.0, 0.0954, 0.3454, 0.6545, 0.9045]
    y_true_values = [
        0.0,
        -0.0004864,
        -0.0216,
        -0.03189,
        -0.02366,
        0.0,
        0.07616,
        0.12024,
        0.09293,
        0.02447,
    ]

    assert airfoil_CST.x_list == pytest.approx(x_true_values, rel=1e-3)
    assert airfoil_CST.y_list == pytest.approx(y_true_values, rel=1e-3)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test CPACS2SUMO module")
    print("To run test use the following command:")
    print(">> pytest -v")
=======
class TestCPACS2SUMO(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tixi = cls.test_cpacs.tixi

    def test_cst2coord(self):

        # Simple 4 points profile with default values
        airfoil_CST = CST_shape(N=4)
        airfoil_CST.airfoil_coor()

        assert airfoil_CST.x_list == pytest.approx([1.0, 0.5, 0.0, 0.5], rel=1e-5)
        assert airfoil_CST.y_list == pytest.approx([0.0, -0.35355, 0.0, 0.35355], rel=1e-3)

        # More complex profile

        wu = [0.2, 0.45, -0.12, 1.0, -0.473528, 0.95, 0.14, 0.38, 0.11, 0.38]
        wl = [-0.13, 0.044, -0.38, 0.43, -0.74, 0.54, -0.51, 0.10, -0.076, 0.062]
        dz = 0.00
        N = 10

        airfoil_CST = CST_shape(wl, wu, dz, N)
        airfoil_CST.airfoil_coor()

        x_true_values = [
            1.0,
            0.9045,
            0.6545,
            0.3454,
            0.0954,
            0.0,
            0.0954,
            0.3454,
            0.6545,
            0.9045,
        ]
        y_true_values = [
            0.0,
            -0.0004864,
            -0.0216,
            -0.03189,
            -0.02366,
            0.0,
            0.07616,
            0.12024,
            0.09293,
            0.02447,
        ]

        assert airfoil_CST.x_list == pytest.approx(x_true_values, rel=1e-3)
        assert airfoil_CST.y_list == pytest.approx(y_true_values, rel=1e-3)

    def test_pointlist_profile(self):
        x, y, z = get_profile_coord(self.tixi, "D150_VAMP_W_SupCritProf1")
        # Check that the lists are not empty and have the same length
        self.assertTrue(len(x) > 3)
        self.assertEqual(len(x), len(y))
        self.assertEqual(len(x), len(z))
        # Check that all are floats
        self.assertTrue(all(isinstance(val, float) for val in x))
        self.assertTrue(all(isinstance(val, float) for val in y))
        self.assertTrue(all(isinstance(val, float) for val in z))
        # Check that x is monotonic decreasing or increasing (airfoil property)
        self.assertTrue(all(x[i] >= x[i + 1] or x[i] <= x[i + 1] for i in range(len(x) - 1)))

    def test_cst2d_profile(self):
        # Only check length and type, as CST_shape is tested elsewhere
        x, _, z = get_profile_coord(self.tixi, "D150_VAMP_W_SupCritProf1")
        self.assertTrue(len(x) > 10)
        self.assertEqual(len(x), len(z))
        self.assertTrue(all(isinstance(val, float) for val in x))
        self.assertTrue(all(isinstance(val, float) for val in z))

    def test_no_profile(self):
        with self.assertRaises(ValueError):
            get_profile_coord(self.tixi, "testProf")

    def test_sumo_str_format(self):
        self.assertEqual(sumo_str_format(1, 2, 3), "1 2 3")
        self.assertEqual(sumo_str_format(1.5, -2.2, 0.0), "1.5 -2.2 0.0")
        self.assertIsInstance(sumo_str_format(0, 0, 0), str)

    def test_sumo_add_nacelle_lip(self):
        sumo = MagicMock()
        xpath = "/Assembly/Engine"
        sumo_add_nacelle_lip(sumo, xpath, ax_offset=1.1, rad_offset=0.2, shape_coef=0.5)
        sumo.createElementAtIndex.assert_called_with(xpath, "NacelleInletLip", 1)
        sumo.addTextAttribute.assert_any_call(xpath + "/NacelleInletLip", "axialOffset", "1.1")
        sumo.addTextAttribute.assert_any_call(xpath + "/NacelleInletLip", "radialOffset", "0.2")
        sumo.addTextAttribute.assert_any_call(xpath + "/NacelleInletLip", "shapeCoef", "0.5")

    def test_sumo_add_engine_bc(self):
        sumo = MagicMock()
        sumo_add_engine_bc(sumo, "TestEngine", "FanPart")
        sumo.createElementAtIndex.assert_called_with("/Assembly", "JetEngineSpec", 1)
        sumo.addTextAttribute.assert_any_call("/Assembly/JetEngineSpec[1]", "name", "TestEngine")
        sumo.addTextAttribute.assert_any_call(
            "/Assembly/JetEngineSpec[1]/Turbofan", "bypass_ratio", "3.5")
        sumo.addTextAttribute.assert_any_call(
            "/Assembly/JetEngineSpec[1]/NozzleRegions/JeRegion", "surface", "FanPart")

    def test_add_wing_cap(self):
        sumo = MagicMock()
        wg_sk_xpath = "/Assembly/WingSkeleton[1]"
        add_wing_cap(sumo, wg_sk_xpath)
        sumo.createElementAtIndex.assert_any_call(wg_sk_xpath, "Cap", 1)
        sumo.addTextAttribute.assert_any_call(wg_sk_xpath + "/Cap[1]", "side", "south")
        sumo.createElementAtIndex.assert_any_call(wg_sk_xpath, "Cap", 2)
        sumo.addTextAttribute.assert_any_call(wg_sk_xpath + "/Cap[2]", "side", "north")


# =================================================================================================
#   MAIN
# =================================================================================================


if __name__ == "__main__":
    unittest.main()
>>>>>>> general_updates
