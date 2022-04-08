"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'SU2Run/func/su2config.py'

Python version: >=3.7


| Author : Aidan Jungo
| Creation: 2022-04-07

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from ceasiompy.SU2Run.func.su2config import get_su2_version, get_su2_config_template
from ceasiompy.utils.moduleinterfaces import get_module_path

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_su2_version():
    """Test function 'get_su2_version'"""

    mock_text = (
        r"## \file SU2_CFD.py\n"
        r"#  \brief Python script to launch SU2_CFD through the Python Wrapper.\n"
        r"#  \author David Thomas\n"
        r'#  \version 9.9.9 "Blackbird"\n'
        r"#"
        r"# SU2 Project Website: https://su2code.github.io\n"
    )

    mock_data = mock_open(read_data=mock_text)

    # TODO: When Python 3.10 will be used, with could be use with parentheses
    with patch("builtins.open", mock_data), patch(
        "ceasiompy.utils.ceasiompyutils.get_install_path", return_value=None
    ), patch.object(Path, "exists", return_value=True):
        assert get_su2_version() == "9.9.9"

    mock_text_no_version = (
        r"## \file SU2_CFD.py\n"
        r"#  \brief Python script to launch SU2_CFD through the Python Wrapper.\n"
    )

    mock_data_no_version = mock_open(read_data=mock_text_no_version)
    with patch("builtins.open", mock_data_no_version):
        assert get_su2_version() is None


def test_get_su2_config_template():
    """Test function 'get_su2_config_template'"""

    su2_dir = get_module_path("SU2Run")

    # Test with an old version of the config template
    su2_version = "3.0.0"
    config_template_path = Path(su2_dir, "files", f"config_template_v{su2_version}.cfg")

    # Remove the config template file if it exists (from a previous test)
    if config_template_path.exists():
        config_template_path.unlink()

    with patch("ceasiompy.SU2Run.func.su2config.get_su2_version", return_value=su2_version):
        assert get_su2_config_template() == config_template_path

    # Test with an inexistent config template version
    with patch("ceasiompy.SU2Run.func.su2config.get_su2_version", return_value="9.9.99"):
        with pytest.raises(FileNotFoundError):
            assert get_su2_config_template() == config_template_path


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
