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

# import math
from pathlib import Path

import numpy as np
import pytest
from ambiance import Atmosphere
from ceasiompy.SU2Run.func.su2actuatordiskfile import (
    axial_interference_function,
    calculate_radial_thrust_coefs,
    get_advanced_ratio,
    get_prandtl_correction_values,
    get_radial_stations,
    save_plots,
    thrust_calculator,
    check_values,
    write_actuator_disk_data,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory

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
        get_advanced_ratio(100, 0, 2)

    Atm = Atmosphere(1000)
    free_stream_velocity = 0.3 * Atm.speed_of_sound[0]
    assert get_advanced_ratio(free_stream_velocity, 100, 2) == pytest.approx(0.2523, 1e-3)

    Atm = Atmosphere(10000)
    free_stream_velocity = 0.48 * Atm.speed_of_sound[0]
    assert get_advanced_ratio(free_stream_velocity, 100, 1.5) == pytest.approx(0.47925, 1e-3)


def test_axial_interference():

    lagrangian_mult = np.array([0.3, 0.12, 0.05])
    adimensional_radius = np.array([0.25, 0.5, 0.75])
    axial_interference_factor = axial_interference_function(lagrangian_mult, adimensional_radius)

    np.testing.assert_array_almost_equal(
        axial_interference_factor, np.array([0.010699, 0.019942, 0.016892])
    )


def test_get_prandtl_correction_values():
    """Test function 'get_prandtl_correction_values'"""

    radial_stations = np.arange(0.1, 1, 0.18)
    correction_values = get_prandtl_correction_values(radial_stations, True, 2, 30, 0.8, 120)
    output_values = np.array([0.73844572, 0.68137418, 0.6087976, 0.51282436, 0.37404968])
    np.testing.assert_array_almost_equal(correction_values, output_values)

    correction_values = get_prandtl_correction_values(radial_stations, False, 2, 30, 0.8, 120)
    output_values = np.ones(len(radial_stations))
    np.testing.assert_array_almost_equal(correction_values, output_values)


def test_get_error():

    radial_stations = np.arange(0.1, 1, 0.20)
    dCt = calculate_radial_thrust_coefs(
        radial_stations,
        advanced_ratio=1.0,
        opt_axial_interf_factor=np.array([1.0, 1.0, 1.0, 1.0, 1.0]),
    )
    radial_stations_spacing = radial_stations[1] - radial_stations[0]

    error = np.sum(radial_stations_spacing * dCt) - 0.3

    assert error == pytest.approx(2.841, rel=1e-3)


def test_get_corrected_axial_factor():

    radial_stations = np.arange(0.1, 1, 0.20)
    prandtl_correction_values = get_prandtl_correction_values(
        radial_stations, False, 2, 30, 0.8, 120
    )
    lagrange_multiplier = 0.2
    non_dimensional_radius = 0.75
    axial_interference_function(lagrange_multiplier, non_dimensional_radius)
    vectorized_axial_interf_f = np.vectorize(axial_interference_function)

    corrected_axial_factor = vectorized_axial_interf_f(
        lagrange_multiplier * prandtl_correction_values,
        non_dimensional_radius,
    )

    np.testing.assert_array_almost_equal(
        corrected_axial_factor,
        np.array([0.05617978, 0.05617978, 0.05617978, 0.05617978, 0.05617978]),
    )


def test_calculate_radial_thrust_coefs():
    """Test function 'calculate_radial_thrust_coefs'"""

    radial_thrust_coefs = calculate_radial_thrust_coefs(
        radial_stations=get_radial_stations(1, 0.2, number_of_stations=4),
        advanced_ratio=1.0,
        opt_axial_interf_factor=np.array([1.0, 1.0, 1.0, 1.0]),
    )

    assert radial_thrust_coefs[0] == np.pi / 2
    assert radial_thrust_coefs[1] == np.pi
    assert radial_thrust_coefs[2] == 3 * np.pi / 2
    assert radial_thrust_coefs[3] == 2 * np.pi


def test_save_plots(tmp_path):
    """Test function 'save_plots'"""

    fake_value = np.array([1.0, 2.0, 3.0, 4.0])

    save_plots(
        radial_stations=fake_value / 4,
        radial_thrust_coefs=fake_value,
        radial_power_coefs=fake_value,
        non_dimensional_radius=fake_value,
        optimal_axial_interference_factor=fake_value,
        optimal_rotational_interference_factor=fake_value,
        prandtl_correction_values=fake_value,
        case_dir_path=tmp_path,
        propeller_uid="propeller_test",
    )

    assert Path(tmp_path, "propeller_test", "interference.png").exists()
    assert Path(tmp_path, "propeller_test", "radial_thrust_and_power_coefficient.png").exists()
    assert Path(tmp_path, "propeller_test", "prandtl_correction.png").exists()


def test_check_values():
    radial_stations = get_radial_stations(1, 0.2, number_of_stations=5)
    radial_stations_spacing = radial_stations[1] - radial_stations[0]

    input_values = {
        "test1": [
            [
                radial_stations_spacing,
                np.array([0.1, 0.2, 0.3, 0.4, 0.2]),
                np.array([0.07, 0.17, 0.25, 0.32, 0.22]),
                100,
                0.9,
                radial_stations,
                2,
                20,
            ],
            [0.24, 0.20600, 40691.358, 0.3973, 0.7725],
        ],
    }

    for test_name, values in input_values.items():
        (
            total_power_coefficient,
            optimal_total_thrust_coefficient,
            thrust_density_ratio,
            computed_total_thrust_coefficient,
            eta,
        ) = check_values(*values[0])

        assert total_power_coefficient == pytest.approx(values[1][0], rel=1e-3)
        assert optimal_total_thrust_coefficient == pytest.approx(values[1][1], rel=1e-3)
        assert thrust_density_ratio == pytest.approx(values[1][2], rel=1e-3)
        assert computed_total_thrust_coefficient == pytest.approx(values[1][3], rel=1e-3)
        assert eta == pytest.approx(values[1][4], rel=1e-3)


def test_thrust_calculator():
    """Test function which made different test on thrust_coefficient function, the test function
    receive a vector with input parameter [total_thrust_coefficient, radius, hub radius,
    free_stream_velocity, prandtl, blades_number, rotational_velocity]
    the function will give an output file to compare with given result vector
    [renard_thrust_coeff, power_coeff, thrust_over_density, efficiency]
    TODO
    """

    input_values = {
        "test1": [
            [get_radial_stations(1.5, 0.2), 0.5, 1.5, 150, True, 2, 33],
            [0.5, 0.965, 44104.5, 0.7847],
        ],
        "test2": [
            [get_radial_stations(1.5, 0.15), 0.8, 1.5, 0.1, True, 3, 33],
            [0, 0.00744, 0, 0],
        ],
        "test3": [
            [get_radial_stations(1.2, 0.1), 1, 1.2, 180, False, 3, 33],
            [1, 3.010, 36130.40, 0.7549],
        ],
        "test4": [
            [get_radial_stations(1.4, 0.1), 1.2, 1.4, 140, True, 2, 33],
            [1.2, 3.299, 80323.24, 0.55097],
        ],
        "test5": [
            [get_radial_stations(2, 0.2), 1.5, 2, 190, True, 8, 33],
            [1.5, 4.6177, 418175.999, 0.4675],
        ],
        "test6": [
            [get_radial_stations(1.4, 0.1), 0.2, 1.4, 130, True, 2, 33],
            [0.2, 0.3138, 13387.20, 0.8966],
        ],
        "test7": [
            [get_radial_stations(1.4, 0.1), 0.15, 1.4, 130, True, 2, 33],
            [0.15, 0.2292, 10040.4057, 0.92068],
        ],
        "test8": [
            [get_radial_stations(1.7, 0.5107), 1.2, 1.7, 160, False, 6, 22],
            [1.199, 3.7025, 77614.39, 0.6932],
        ],
    }

    for values in input_values.values():

        renard_thrust_coeff, power_coeff, _, _, _, _ = thrust_calculator(*values[0])

        assert np.sum((1 / 40.0) * renard_thrust_coeff) == pytest.approx(values[1][0], rel=1e-3)
        assert np.sum((1 / 40.0) * power_coeff) == pytest.approx(values[1][1], rel=1e-3)

    results_dir = get_results_directory("SU2Run")
    markdown_file_path = Path(results_dir, "su2actuatordisk.md")

    if markdown_file_path.exists():
        markdown_file_path.unlink()

    thrust_calculator(get_radial_stations(1.5, 0.2), 0.5, 1.5, 150, True, 2, 33)

    assert markdown_file_path.exists()


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
