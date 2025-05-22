"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/SU2Run/func/meshutils.py'


| Author : Aidan Jungo
| Creation: 2021-12-23

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from ceasiompy import log

import pytest
from ceasiompy.SU2Run.func.utils import (
    get_efficiency_and_aoa,
    get_mesh_markers,
    get_su2_aerocoefs,
    get_wetted_area,
)
from pytest import approx

MODULE_DIR = Path(__file__).parent
FORCES_BREAKDOWN = Path(MODULE_DIR, "forces_breakdown.dat")
FORCES_BREAKDOWN_NO_VALUE = Path(MODULE_DIR, "forces_breakdown_no_value.dat")
SU2_LOGFILE = Path(MODULE_DIR, "logfile_SU2_CFD.log")
SU2_LOGFILE_NO_WETTED_AREA = Path(MODULE_DIR, "logfile_SU2_CFD_no_wetted_area.log")


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
    log.info("Nothing to execute!")
