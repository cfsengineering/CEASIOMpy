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

import pytest

import numpy as np

from ceasiompy.ThermoData.func.turbofan_func import (
    turbofan_analysis,
    write_hbtf_file,
)

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


"""
        T_tot_out,
        V_stat_out,
        MN_out,
        P_tot_out,
        massflow_stat_out,
        T_stat_out,
        P_stat_out,




def test_write_turbojet_file():
    ll = 2


def test_turbofan():
    alt = 4000  # [ft]
    MN = 0.6
    # Fn = 11800  # [lbf]
    new_sol_tf = turbofan_analysis(alt, MN)
    correct_sol_tf = np.array(
        [
            8.11328662e01,
            3.44500820e02,
            1.00000000e00,
            4.19439630e02,
            5.64233274e01,
            1.08865912e-01,
        ]
    ).reshape((6, 1))
    np.testing.assert_almost_equal(new_sol_tf, correct_sol_tf, 5)


def test_write_hbtf_file():
    ll = 1

"""
# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
