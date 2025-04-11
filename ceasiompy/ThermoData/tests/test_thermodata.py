"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/ThermoData/func/turbojet_func.py'



| Author : Francesco Marcucci
| Creation: 2024-02-09

"""
# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from pathlib import Path

from ceasiompy.ThermoData.func.turbojet import (
    turbojet_analysis,
    write_turbojet_file,
)

from ceasiompy.ThermoData.func.turbofan import (
    turbofan_analysis,
    write_hbtf_file,
)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_turbojet_func():
    """Test function 'turbojet_analysis'"""
    alt = 1000
    MN = 0.3
    Fn = 2000
    new_sol = turbojet_analysis(alt, MN, Fn)
    correct_sol = np.array(
        [
            1006.6296749,
            798.79704119,
            1.50478324,
            326886.19429314,
            2.89168807,
            727.76800186,
            89874.50518856,
        ]
    ).reshape((7, 1))
    np.testing.assert_almost_equal(new_sol, correct_sol, 3)


def test_write_turbojet_file(tmp_path):
    """Test function 'write_turbojet_file'"""
    T_tot_out = 300
    V_stat_out = 200
    MN_out = 0.5
    P_tot_out = 100000
    massflow_stat_out = 50
    T_stat_out = 400
    P_stat_out = 200000

    test_thermodata_path = Path(tmp_path, "EngineBC.dat")

    with open(test_thermodata_path, "w") as file:
        write_turbojet_file(
            file,
            T_tot_out,
            V_stat_out,
            MN_out,
            P_tot_out,
            massflow_stat_out,
            T_stat_out,
            P_stat_out,
        )

    with open(test_thermodata_path, "r") as file:
        content = [line.strip() for line in file.readlines()]
    content.append("")

    # print("content=", content)
    # expected_content = test_thermodata_path.read_text().split("\n")
    # print("expected_content=", expected_content)

    assert test_thermodata_path.read_text().split("\n") == content


def test_turbofan_func():
    """Test function 'turbofan_analysis'"""
    alt = 1000
    MN = 0.3
    Fn = 2000
    new_sol_tuple = turbofan_analysis(alt, MN, Fn)
    new_sol = np.concatenate(new_sol_tuple)
    correct_sol = np.array(
        [
            65.04136793,
            323.23292298,
            0.95295201,
            161198.12289882,
            1.78761453,
            13.08931717,
            1270.61685498,
            724.51083329,
            1.0,
            964349.32127573,
            1.42155524,
            1139.22870449,
        ]
    )
    np.testing.assert_almost_equal(new_sol, correct_sol, 3)


def test_write_hbtf_file(tmp_path):
    """Test function 'write_hbtf_file'"""
    T_tot_out_core = 300
    V_stat_out_core = 200
    MN_out_core = 0.5
    P_tot_out_core = 100000
    massflow_out_core = 50
    T_stat_out_core = 400
    T_tot_out_byp = 200000
    V_stat_out_byp = 300
    MN_out_byp = 1.2
    P_tot_out_byp = 100000
    massflow_stat_out_byp = 1.6
    T_stat_out_byp = 13

    test_thermodata_path = Path(tmp_path, "EngineBC.dat")

    with open(test_thermodata_path, "w") as file:
        write_hbtf_file(
            file,
            T_tot_out_core,
            V_stat_out_core,
            MN_out_core,
            P_tot_out_core,
            massflow_out_core,
            T_stat_out_core,
            T_tot_out_byp,
            V_stat_out_byp,
            MN_out_byp,
            P_tot_out_byp,
            massflow_stat_out_byp,
            T_stat_out_byp,
        )

    with open(test_thermodata_path, "r") as file:
        content = [line.strip() for line in file.readlines()]
    content.append("")

    assert test_thermodata_path.read_text().split("\n") == content


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test ThermoData")
    print("To run test use the following command:")
    print(">> pytest -v")
