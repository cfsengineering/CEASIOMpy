"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/SU2Run/func/su2actuatordisk.py'

Python version: >=3.8


| Author : Aidan Jungo and Giacomo Benedetti
| Creation: 2022-12-05

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import numpy as np
import pytest


from ceasiompy.SU2Run.func.su2actuatordiskfile import (
    get_advanced_ratio,
    get_radial_stations,
    write_actuator_disk_data,
)

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_radial_stations():
    """Test function 'get_radial_stations'"""

    with pytest.raises(ValueError):
        get_radial_stations(1, 1.1)

    np.testing.assert_almost_equal(get_radial_stations(1, 0.1), (np.arange(0.1, 1.02, 0.025)))
    np.testing.assert_almost_equal(get_radial_stations(1, 0.5), (np.arange(0.5, 1.02, 0.025)))
    np.testing.assert_almost_equal(get_radial_stations(1, 0.2), (np.arange(0.2, 1.02, 0.025)))
    np.testing.assert_almost_equal(get_radial_stations(1, 0.0), (np.arange(0.0, 1.02, 0.025))[1:])


def test_get_advanced_ratio():
    """Test function 'get_advanced_ratio'"""

    with pytest.raises(ValueError):
        get_advanced_ratio(1000, 0.3, 0, 2)

    assert get_advanced_ratio(1000, 0.3, 100, 2) == pytest.approx(0.2523, 1e-3)
    assert get_advanced_ratio(10000, 0.48, 100, 1.5) == pytest.approx(0.47925, 1e-3)


def test_write_actuator_disk_data(tmp_path):
    """Test function 'write_actuator_disk_data'"""

    correct_actuatordisck_path = Path(MODULE_DIR, "correct_ActuatorDisk.dat")
    test_actuatordisk_path = Path(tmp_path, "ActuatorDisk.dat")

    with open(test_actuatordisk_path, "w") as f:

        write_actuator_disk_data(
            file=f,
            inlet_marker="Inlet",
            outlet_marker="Outlet",
            center=(0, 5, 0),
            axis=(1, 0, 0),
            radius=2.5,
            advanced_ratio=1.5,
            radial_stations=np.array([0.2, 0.4, 0.6, 0.8, 1.0]),
            radial_thrust_coefs=np.array([0.02, 0.04, 0.06, 0.08, 0.06]),
            radial_power_coefs=np.array([0.1, 0.2, 0.3, 0.4, 0.3]),
        )

    assert test_actuatordisk_path.read_text() == correct_actuatordisck_path.read_text()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
