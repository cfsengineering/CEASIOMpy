"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test the module CPACS2SUMO (lib/CPACS2SUMO/cpacs2sumo.py')

| Author : Aidan Jungo
| Creation: 2018-10-26

TODO:

    * Create tests for this module

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
from ceasiompy.CPACS2SUMO.func.cst2coord import CST_shape

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test CPACS2SUMO module")
    print("To run test use the following command:")
    print(">> pytest -v")
