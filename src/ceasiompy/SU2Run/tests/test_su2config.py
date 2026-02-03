"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/SU2Run/func/su2config.py'

| Author : Aidan Jungo
| Creation: 2022-04-07

"""

# Imports

from pathlib import Path

import pytest
from ceasiompy.SU2Run.func.config import add_damping_derivatives
from ceasiompy.utils.configfiles import ConfigFile

MODULE_DIR = Path(__file__).parent

# Functions

def test_add_damping_derivatives(tmp_path):
    """Test function 'add_damping_derivatives'"""

    cfg = ConfigFile()
    case_dir_name = "test_damping_der_cfg"

    rotation_rate = 5.4
    add_damping_derivatives(cfg, tmp_path, case_dir_name, rotation_rate)

    case_dp = Path(tmp_path, f"{case_dir_name}_p_{rotation_rate}")
    case_dq = Path(tmp_path, f"{case_dir_name}_q_{rotation_rate}")
    case_dr = Path(tmp_path, f"{case_dir_name}_r_{rotation_rate}")

    assert case_dp.exists()
    assert case_dq.exists()
    assert case_dr.exists()

    assert "5.4 0.0 0.0" in Path(case_dp, "ConfigCFD.cfg").read_text()
    assert "0.0 5.4 0.0" in Path(case_dq, "ConfigCFD.cfg").read_text()
    assert "0.0 0.0 5.4" in Path(case_dr, "ConfigCFD.cfg").read_text()


@pytest.mark.skip(reason="Not implemented yet")
def test_add_actuator_disk():
    """Test function 'add_actuator_disk'"""
    ...
