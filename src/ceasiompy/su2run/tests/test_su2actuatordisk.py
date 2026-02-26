"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/SU2Run/func/su2actuatordisk.py'

| Author : Aidan Jungo and Giacomo Benedetti
| Creation: 2022-12-05

"""

# Imports

import pytest
import numpy as np

from ceasiompy.su2run.func.actuatordiskfile import (
    axial_interference_function,
    calculate_radial_thrust_coefs,
    check_input_output_values,
    get_advanced_ratio,
    get_prandtl_correction_values,
    get_radial_stations,
    thrust_calculator,
    write_actuator_disk_data,
)
from ceasiompy.su2run.func.plot import save_plots

from pathlib import Path
from ambiance import Atmosphere


# Functions

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

    atmosphere = Atmosphere(1000)
    free_stream_velocity = 0.3 * atmosphere.speed_of_sound[0]
    assert get_advanced_ratio(free_stream_velocity, 100, 2) == pytest.approx(0.2523, 1e-3)

    atmosphere = Atmosphere(10000)
    free_stream_velocity = 0.48 * atmosphere.speed_of_sound[0]
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
    thrust_coef_distribution = calculate_radial_thrust_coefs(
        radial_stations,
        advanced_ratio=1.0,
        opt_axial_interf_factor=np.array([1.0, 1.0, 1.0, 1.0, 1.0]),
    )
    radial_stations_spacing = radial_stations[1] - radial_stations[0]

    error = np.sum(radial_stations_spacing * thrust_coef_distribution)

    assert error == pytest.approx(3.141, rel=1e-3)


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


def test_check_input_output_values():
    radial_stations = get_radial_stations(1, 0.2, number_of_stations=5)
    radial_stations_spacing = radial_stations[1] - radial_stations[0]
    radial_power_coefs = np.array([0.1, 0.2, 0.3, 0.4, 0.2])
    radial_thrust_coefs = np.array([0.07, 0.17, 0.25, 0.32, 0.22])
    free_stream_velocity = 100
    advanced_ratio = 0.9
    radius = 2
    rotational_velocity = 20

    output_values = np.array([0.24, 0.20600, 40691.358, 0.3973, 0.7725])

    (
        total_power_coefficient,
        optimal_total_thrust_coefficient,
        thrust_density_ratio,
        computed_total_thrust_coefficient,
        eta,
    ) = check_input_output_values(
        radial_stations_spacing,
        radial_power_coefs,
        radial_thrust_coefs,
        free_stream_velocity,
        advanced_ratio,
        radial_stations,
        radius,
        rotational_velocity,
    )

    assert total_power_coefficient == pytest.approx(output_values[0], rel=1e-3)
    assert optimal_total_thrust_coefficient == pytest.approx(output_values[1], rel=1e-3)
    assert thrust_density_ratio == pytest.approx(output_values[2], rel=1e-3)
    assert computed_total_thrust_coefficient == pytest.approx(output_values[3], rel=1e-3)
    assert eta == pytest.approx(output_values[4], rel=1e-3)


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
    output = thrust_calculator(get_radial_stations(1.5, 0.2), 0.5, 1.5, 150, True, 2, 33)
    expected_output = (
        np.array(
            [
                0.02078195,
                0.03256252,
                0.04786722,
                0.06698531,
                0.09012885,
                0.11742818,
                0.14892926,
                0.18459271,
                0.22429463,
                0.2678288,
                0.31491016,
                0.36517897,
                0.41820553,
                0.47349492,
                0.53049132,
                0.58858183,
                0.64709911,
                0.70532275,
                0.76247894,
                0.81773804,
                0.87020954,
                0.91893373,
                0.96286896,
                1.00087305,
                1.031676,
                1.05384008,
                1.06569946,
                1.06526611,
                1.05007506,
                1.01691255,
                0.9612927,
                0.87631138,
                0.74958649,
                0.55155389,
                0.0,
            ]
        ),
        np.array(
            [
                0.04414487,
                0.06905163,
                0.10132347,
                0.1415201,
                0.19002749,
                0.24704882,
                0.3125994,
                0.38650567,
                0.46840797,
                0.55776666,
                0.65387087,
                0.75584924,
                0.86268168,
                0.97321154,
                1.08615734,
                1.20012332,
                1.3136083,
                1.42501223,
                1.53263983,
                1.6347008,
                1.72930577,
                1.81445713,
                1.88803302,
                1.94776248,
                1.99118768,
                2.01560727,
                2.01798957,
                1.99483563,
                1.94195218,
                1.85405013,
                1.72396697,
                1.54095551,
                1.28609572,
                0.91467686,
                0.0,
            ]
        ),
        np.array(
            [
                0.31101767,
                0.36285395,
                0.41469023,
                0.46652651,
                0.51836279,
                0.57019907,
                0.62203535,
                0.67387162,
                0.7257079,
                0.77754418,
                0.82938046,
                0.88121674,
                0.93305302,
                0.9848893,
                1.03672558,
                1.08856185,
                1.14039813,
                1.19223441,
                1.24407069,
                1.29590697,
                1.34774325,
                1.39957953,
                1.45141581,
                1.50325208,
                1.55508836,
                1.60692464,
                1.65876092,
                1.7105972,
                1.76243348,
                1.81426976,
                1.86610604,
                1.91794232,
                1.96977859,
                2.02161487,
                2.07345115,
            ]
        ),
        np.array(
            [
                0.01885475,
                0.02516654,
                0.03215161,
                0.03970322,
                0.04771119,
                0.05606441,
                0.064653,
                0.07337019,
                0.08211375,
                0.09078708,
                0.09929983,
                0.1075683,
                0.11551535,
                0.12307017,
                0.13016774,
                0.1367481,
                0.14275548,
                0.14813724,
                0.15284265,
                0.15682157,
                0.16002283,
                0.16239239,
                0.16387106,
                0.1643917,
                0.16387534,
                0.16222599,
                0.15932295,
                0.15500896,
                0.14907081,
                0.14120494,
                0.1309506,
                0.11754146,
                0.09950375,
                0.07309429,
                0.0,
            ]
        ),
        np.array(
            [
                0.2732678,
                0.2675221,
                0.26119863,
                0.25436391,
                0.24708657,
                0.23943554,
                0.23147848,
                0.22328039,
                0.21490254,
                0.20640161,
                0.1978291,
                0.18923096,
                0.18064743,
                0.17211307,
                0.16365683,
                0.15530236,
                0.14706821,
                0.13896824,
                0.13101187,
                0.12320438,
                0.11554722,
                0.1080381,
                0.10067112,
                0.09343664,
                0.08632096,
                0.07930573,
                0.07236671,
                0.06547179,
                0.05857729,
                0.05162119,
                0.04450944,
                0.03708477,
                0.02904023,
                0.01957538,
                0.0,
            ]
        ),
        np.array(
            [
                0.90972805,
                0.90434105,
                0.89862739,
                0.89256626,
                0.88613532,
                0.87931058,
                0.87206619,
                0.86437428,
                0.85620469,
                0.84752477,
                0.838299,
                0.82848865,
                0.81805138,
                0.80694062,
                0.79510505,
                0.7824877,
                0.76902508,
                0.75464592,
                0.73926965,
                0.72280447,
                0.70514474,
                0.68616768,
                0.66572875,
                0.64365536,
                0.619738,
                0.5937172,
                0.56526388,
                0.53394827,
                0.49918808,
                0.46015586,
                0.41559731,
                0.36342601,
                0.29962042,
                0.21391652,
                0.0,
            ]
        ),
    )

    for output_arr, expected_arr in zip(output, expected_output):
        np.testing.assert_allclose(output_arr, expected_arr, rtol=1e-6, atol=1e-8)


def test_write_actuator_disk_data(tmp_path):
    """Test function 'write_actuator_disk_data'"""

    correct_actuatordisk_file_content = [
        "# Total thurst coefficient= 0.05200",
        "MARKER_ACTDISK= Inlet Outlet",
        "CENTER= 0 5 0",
        "AXIS= 1 0 0",
        "RADIUS= 2.5",
        "ADV_RATIO= 1.50000",
        "NROW= 5",
        "# rs=r/R    dCT/drs     dCP/drs     dCR/drs",
        "0.20000     0.02000      00.10000     0.0",
        "0.40000     0.04000      00.20000     0.0",
        "0.60000     0.06000      00.30000     0.0",
        "0.80000     0.08000      00.40000     0.0",
        "1.00000     0.06000      00.30000     0.0",
        "",
        "",
    ]

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

    assert test_actuatordisk_path.read_text().split("\n") == correct_actuatordisk_file_content


# Main
if __name__ == "__main__":
    test_thrust_calculator()
    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
