"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions of 'ceasiompy/SU2Run/func/su2config.py'

Python version: >=3.8


| Author : Aidan Jungo
| Creation: 2022-04-07

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.SU2Run.func.su2config import add_damping_derivatives
from ceasiompy.utils.configfiles import ConfigFile

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_add_damping_derivatives(tmp_path):
    """Test function 'add_damping_derivatives'"""

    cfg = ConfigFile()
    case_dir_name = "test_damping_der_cfg"

    add_damping_derivatives(cfg, tmp_path, case_dir_name, 5.4)

    case_dp = Path(tmp_path, f"{case_dir_name}_dp")
    case_dq = Path(tmp_path, f"{case_dir_name}_dq")
    case_dr = Path(tmp_path, f"{case_dir_name}_dr")

    assert case_dp.exists()
    assert case_dq.exists()
    assert case_dr.exists()

    assert "5.4 0.0 0.0" in Path(case_dp, "ConfigCFD.cfg").read_text()
    assert "0.0 5.4 0.0" in Path(case_dq, "ConfigCFD.cfg").read_text()
    assert "0.0 0.0 5.4" in Path(case_dr, "ConfigCFD.cfg").read_text()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
