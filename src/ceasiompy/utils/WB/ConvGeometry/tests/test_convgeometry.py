"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =============================================================================
#   IMPORTS
# =============================================================================

import sys
import pytest
import numpy as np

from unittest.mock import MagicMock
from ceasiompy.utils.WB.ConvGeometry.geometry import AircraftGeometry

from unittest.mock import patch

# =============================================================================
#   FUNCTIONS
# =============================================================================


@pytest.fixture
def mock_cpacs():
    """Fixture to create a mock cpacs object with tixi and tigl."""
    cpacs = MagicMock()
    cpacs.tixi = MagicMock()
    cpacs.tigl = MagicMock()
    return cpacs


def test_aircraftgeometry_init_defaults():
    ag = AircraftGeometry()
    assert ag.tot_length == 0
    assert ag.fus_nb == 0
    assert ag.fuse_nb == 0
    assert ag.fuse_sym == []
    assert ag.fuse_sec_nb == []
    assert ag.fuse_seg_nb == []
    assert ag.fuse_length == []
    assert ag.w_nb == 0
    assert ag.wing_nb == 0
    assert ag.wing_sym == []
    assert ag.wing_sec_nb == []
    assert ag.wing_seg_nb == []
    assert ag.wing_span == []
    assert ag.wing_plt_area == []
    assert ag.wing_vol == []
    assert ag.is_horiz == []


def test_fuse_geom_eval_basic(mock_cpacs):
    ag = AircraftGeometry()
    # Setup mock tixi and tigl for a single fuselage with 2 sections and 1 segment
    mock_cpacs.tixi.getNamedChildrenCount.return_value = 1
    mock_cpacs.tigl.fuselageGetSymmetry.return_value = 0
    mock_cpacs.tigl.fuselageGetSectionCount.return_value = 2
    mock_cpacs.tigl.fuselageGetSegmentCount.return_value = 1
    mock_cpacs.tigl.fuselageGetVolume.return_value = 10.0
    mock_cpacs.tigl.configurationGetLength.return_value = 30.0
    # Patch fuselage_check_segment_connection and rel_dist
    with patch(
        "ceasiompy.utils.WB.ConvGeometry.Fuselage.fusegeom.fuselage_check_segment_connection"
    ) as mock_conn, patch(
        "ceasiompy.utils.WB.ConvGeometry.Fuselage.fusegeom.rel_dist"
    ) as mock_rel_dist:
        mock_conn.return_value = ([2], [1], np.zeros((1, 1, 3)))
        mock_rel_dist.return_value = (np.array([0.0, 10.0]), np.array([1, 2]))
        mock_cpacs.tigl.fuselageGetCircumference.return_value = 5.0
        mock_cpacs.tigl.fuselageGetPoint.side_effect = lambda i, k, eta, zeta: (
            float(k),
            float(k),
            float(zeta),
        )
        mock_cpacs.tigl.fuselageGetSegmentVolume.return_value = 2.0
        # Patch tigl.fuselageGetCircumference
        # and .fuselageGetPoint and .fuselageGetSegmentVolume
        mock_cpacs.tigl.fuselageGetStartSectionAndElementIndex.return_value = (1, 1)
        mock_cpacs.tigl.fuselageGetEndSectionAndElementIndex.return_value = (2, 1)
        ag.fuse_geom_eval(mock_cpacs)
        assert ag.fus_nb == 1
        assert ag.fuse_nb == 1
        assert ag.fuse_sec_nb == [2]
        assert ag.fuse_seg_nb == [1]
        assert ag.fuse_length[0] == 0.0
        assert ag.tot_length == 30.0
        assert ag.fuse_vol[0] == 10.0


def test_wing_geom_eval_basic(mock_cpacs):
    ag = AircraftGeometry()
    # Setup mock tixi and tigl for a single wing with 2 sections and 1 segment
    mock_cpacs.tixi.getNamedChildrenCount.return_value = 1
    mock_cpacs.tigl.wingGetSymmetry.return_value = 0
    mock_cpacs.tigl.wingGetSectionCount.return_value = 2
    mock_cpacs.tigl.wingGetSegmentCount.return_value = 1
    mock_cpacs.tigl.wingGetVolume.return_value = 5.0
    mock_cpacs.tigl.wingGetReferenceArea.side_effect = lambda i, plane: 20.0
    mock_cpacs.tigl.wingGetUID.return_value = "W1"
    mock_cpacs.tigl.wingGetSpan.return_value = 15.0
    mock_cpacs.tigl.wingGetMAC.return_value = [5.0, 1.0, 2.0, 3.0]
    mock_cpacs.tigl.wingGetChordPoint.side_effect = lambda i, j, eta, xsi: (
        float(j),
        float(j),
        float(xsi),
    )
    mock_cpacs.tigl.wingGetLowerPoint.side_effect = lambda i, j, eta, xsi: (
        float(j),
        float(j),
        float(xsi),
    )
    mock_cpacs.tigl.wingGetUpperPoint.side_effect = lambda i, j, eta, xsi: (
        float(j) + 1,
        float(j) + 1,
        float(xsi) + 1,
    )
    mock_cpacs.tigl.wingGetSegmentVolume.return_value = 1.0
    # Patch wing_check_segment_connection
    with patch.object(AircraftGeometry, "wing_check_segment_connection") as mock_conn:
        mock_conn.return_value = ([2], [1], np.zeros((1, 1, 3)), np.zeros((1, 1)))
        ag.wing_geom_eval(mock_cpacs)
    assert ag.w_nb == 1
    assert ag.wing_nb >= 1
    assert ag.wing_sec_nb[0] == 2
    assert ag.wing_seg_nb[0] == 1
    assert ag.wing_vol[0] == 5.0
    assert ag.wing_span[0] == 15.0
    assert ag.wing_mac[0, 0] == 5.0


def test_get_wing_segment_length():
    ag = AircraftGeometry()
    ag.wing_seg_nb = [2]
    ag.w_nb = 1
    ag.wing_nb = 1
    ag.wing_sym = [0]
    # Create a simple wing_center_section_point array
    wing_center_section_point = np.array(
        [
            [[0.0, 0.0, 0.0]],
            [[1.0, 0.0, 0.0]],
            [[2.0, 0.0, 0.0]],
        ]
    )
    ag.get_wing_segment_length(wing_center_section_point)
    assert ag.wing_seg_length.shape == (2, 1)
    np.testing.assert_allclose(ag.wing_seg_length[:, 0], [1.0, 1.0])


def test_produce_output_txt(tmp_path):
    ag = AircraftGeometry()
    ag.fuse_sec_nb = [2]
    ag.fuse_seg_nb = [1]
    ag.cabin_seg = np.array([[1]])
    ag.fuse_length = [10.0]
    ag.fuse_nose_length = [2.0]
    ag.fuse_cabin_length = [6.0]
    ag.fuse_tail_length = [2.0]
    ag.tot_length = 10.0
    ag.fuse_sec_circ = np.array([[5.0]])
    ag.fuse_sec_rel_dist = np.array([[0.0]])
    ag.fuse_seg_length = np.array([[10.0]])
    ag.fuse_mean_width = 3.0
    ag.fuse_sec_width = np.array([[3.0]])
    ag.fuse_seg_vol = np.array([[20.0]])
    ag.fuse_cabin_vol = [12.0]
    ag.fuse_vol = [20.0]
    ag.wing_nb = 1
    ag.wing_sym = [0]
    ag.wing_sec_nb = [2]
    ag.wing_seg_nb = [1]
    ag.wing_span = [15.0]
    ag.wing_mac = np.array([[5.0], [1.0], [2.0], [3.0]])
    ag.wing_sec_thickness = np.array([[1.0]])
    ag.wing_sec_mean_thick = [1.0]
    ag.wing_seg_length = np.array([[10.0]])
    ag.wing_max_chord = [5.0]
    ag.wing_min_chord = [2.0]
    ag.wing_plt_area = [20.0]
    ag.wing_plt_area_main = 20.0
    ag.wing_vol = [10.0]
    ag.wing_tot_vol = 10.0
    ag.wing_fuel_vol = 8.0
    # Patch get_results_directory to use tmp_path
    with patch(
        "ceasiompy.utils.WB.ConvGeometry.geometry.get_results_directory", return_value=tmp_path
    ):
        ag.produce_output_txt()
        output_file = tmp_path / "Aircraft_Geometry.out"
        assert output_file.exists()
        content = output_file.read_text()
        assert "AIRCRAFT GEOMETRY EVALUATION MODULE" in content
        assert "Number of fuselage sections" in content
        assert "Number of Wings" in content


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
