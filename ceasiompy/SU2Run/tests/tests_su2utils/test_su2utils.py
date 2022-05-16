"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SU2Run/func/meshutils.py'  

Python version: >=3.7


| Author : Aidan Jungo
| Creation: 2021-12-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import pytest
from unittest.mock import mock_open, patch

from ceasiompy.SU2Run.func.su2utils import (
    get_mesh_marker,
    get_su2_config_template,
    get_su2_version,
)
from ceasiompy.utils.moduleinterfaces import get_module_path

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_mesh_marker():
    """Test the class 'get_mesh_marker'"""

    NOT_SU2_MESH = Path(MODULE_DIR, "not_su2_mesh.txt")
    SU2_MESH_0 = Path(MODULE_DIR, "test_mesh0.su2")
    SU2_MESH_1 = Path(MODULE_DIR, "test_mesh1.su2")

    with pytest.raises(FileNotFoundError):
        get_mesh_marker(Path("This_file_do_not_exist.su2"))

    with pytest.raises(ValueError):
        get_mesh_marker(NOT_SU2_MESH)

    # Check if ValueError is raised when no MARKER_TAG in the SU2 mesh
    with pytest.raises(ValueError):
        get_mesh_marker(SU2_MESH_0)

    wall_marker_list, eng_bc_marker_list = get_mesh_marker(SU2_MESH_1)
    assert wall_marker_list == ["D150_VAMP_SL1", "D150_VAMP_FL1", "D150_VAMP_HL1", "D150_VAMP_W1"]
    assert eng_bc_marker_list == ["D150_ENGINE1_Intake", "D150_ENGINE1_Exhaust"]


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

    # TODO: When Python 3.10 will be used, with could use one "with" with parentheses
    with patch(
        "ceasiompy.SU2Run.func.su2utils.get_install_path",
        return_value=Path("/mockpath/bin/SU2_CFD"),
    ):
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_data):
                assert get_su2_version() == "9.9.9"

    mock_text_no_version = (
        r"## \file SU2_CFD.py\n"
        r"#  \brief Python script to launch SU2_CFD through the Python Wrapper.\n"
    )

    mock_data_no_version = mock_open(read_data=mock_text_no_version)

    # TODO: When Python 3.10 will be used, with could use one "with" with parentheses
    with patch(
        "ceasiompy.SU2Run.func.su2utils.get_install_path",
        return_value=Path("/mockpath/bin/SU2_CFD"),
    ):
        with patch.object(Path, "exists", return_value=True):
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

    with patch("ceasiompy.SU2Run.func.su2utils.get_su2_version", return_value=su2_version):
        assert get_su2_config_template() == config_template_path

    # Test with an inexistent config template version
    with patch("ceasiompy.SU2Run.func.su2utils.get_su2_version", return_value="9.9.99"):
        with pytest.raises(FileNotFoundError):
            assert get_su2_config_template() == config_template_path


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
