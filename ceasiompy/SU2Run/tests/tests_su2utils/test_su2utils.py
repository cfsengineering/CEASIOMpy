"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SU2Run/func/meshutils.py'

Python version: >=3.8


| Author : Aidan Jungo
| Creation: 2021-12-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from ceasiompy.SU2Run.func.su2utils import (
    get_efficiency_and_aoa,
    get_mesh_markers,
    get_su2_aerocoefs,
    get_su2_config_template,
    get_su2_version,
    get_wetted_area,
)
from ceasiompy.utils.moduleinterfaces import get_module_path
from pytest import approx

MODULE_DIR = Path(__file__).parent
FORCES_BREAKDOWN = Path(MODULE_DIR, "forces_breakdown.dat")
FORCES_BREAKDOWN_NO_VALUE = Path(MODULE_DIR, "forces_breakdown_no_value.dat")
SU2_LOGFILE = Path(MODULE_DIR, "logfile_SU2_CFD.log")
SU2_LOGFILE_NO_WETTED_AREA = Path(MODULE_DIR, "logfile_SU2_CFD_no_wetted_area.log")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_get_mesh_marker():
    """Test the class 'get_mesh_markers'"""

    NOT_SU2_MESH = Path(MODULE_DIR, "not_su2_mesh.txt")
    SU2_MESH_NO_MARKER = Path(MODULE_DIR, "test_mesh0.su2")
    SU2_MESH_1 = Path(MODULE_DIR, "test_mesh1.su2")

    with pytest.raises(FileNotFoundError):
        get_mesh_markers(Path("This_file_do_not_exist.su2"))

    with pytest.raises(ValueError):
        get_mesh_markers(NOT_SU2_MESH)

    with pytest.raises(ValueError):
        get_mesh_markers(SU2_MESH_NO_MARKER)

    mesh_markers = get_mesh_markers(SU2_MESH_1)
    assert mesh_markers["wall"] == [
        "D150_VAMP_SL1",
        "D150_VAMP_FL1",
        "D150_VAMP_HL1",
        "D150_VAMP_W1",
    ]
    assert mesh_markers["engine_intake"] == ["D150_ENGINE1_In"]
    assert mesh_markers["engine_exhaust"] == ["D150_ENGINE1_Ex"]
    assert mesh_markers["actuator_disk_inlet"] == ["D150_PROPELLER1_AD_Inlet"]
    assert mesh_markers["actuator_disk_outlet"] == ["D150_PROPELLER1_AD_Outlet"]
    assert mesh_markers["farfield"] == ["Farfield"]
    assert mesh_markers["symmetry"] == ["None"]


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
    config_template_path = Path(su2_dir, "files", "config_template_euler.cfg")

    # Remove the config template file if it exists (from a previous test)
    if config_template_path.exists():
        assert get_su2_config_template() == config_template_path

    # # Test with an inexistent config template version
    # with patch("ceasiompy.SU2Run.func.su2utils.get_su2_version", return_value="9.9.99"):
    #     with pytest.raises(FileNotFoundError):
    #         assert get_su2_config_template() == config_template_path


def test_get_su2_aerocoefs():
    """Test function 'get_su2_aerocoefs'"""

    with pytest.raises(FileNotFoundError):
        get_su2_aerocoefs(Path(MODULE_DIR, "This_file_do_not_exist.dat"))

    results = get_su2_aerocoefs(FORCES_BREAKDOWN)
    correct_results = [0.132688, 0.199127, 0.010327, None, -0.392577, 0.076315, 102.089]
    for r, res in enumerate(results):
        assert res == approx(correct_results[r], rel=1e-4)

    results_no_value = get_su2_aerocoefs(FORCES_BREAKDOWN_NO_VALUE)
    for res in results_no_value:
        assert res is None


def test_get_efficiency_and_aoa():
    """Test function 'get_efficiency_and_aoa'"""

    with pytest.raises(FileNotFoundError):
        get_efficiency_and_aoa(Path(MODULE_DIR, "This_file_do_not_exist.dat"))

    cl_cd, aoa = get_efficiency_and_aoa(FORCES_BREAKDOWN)
    assert cl_cd == approx(0.666351, rel=1e-4)
    assert aoa == approx(0.5, rel=1e-4)

    with pytest.raises(ValueError):
        get_efficiency_and_aoa(FORCES_BREAKDOWN_NO_VALUE)


def test_get_wetted_area():
    """Test function 'get_wetted_area'"""

    with pytest.raises(FileNotFoundError):
        get_wetted_area(Path(MODULE_DIR, "This_file_do_not_exist.log"))

    assert get_wetted_area(SU2_LOGFILE) == approx(702.04, rel=1e-4)

    assert get_wetted_area(SU2_LOGFILE_NO_WETTED_AREA) == 0


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Nothing to execute!")
