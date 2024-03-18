"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/ThermoData/func/turbojet_func.py'

Python version: >=3.8


| Author : Francesco Marcucci
| Creation: 2024-02-09

"""
# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import sys

import numpy as np

from ceasiompy.ThermoData.func.turbojet_func import (
    turbojet_analysis,
    write_turbojet_file,
)

sys.path.append("/home/cfse/Stage_Francesco/Thermodata")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_turbojet_func():
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


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
