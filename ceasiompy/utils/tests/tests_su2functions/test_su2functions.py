"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'

Python version: >=3.7


| Author : Aidan Jungo
| Creation: 2021-12-23

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import pytest

from ceasiompy.utils.su2functions import get_mesh_marker

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_get_mesh_marker():
    """Test the class 'get_mesh_marker'"""

    NOT_SU2_MESH = os.path.join(MODULE_DIR, "not_su2_mesh.txt")
    SU2_MESH_0 = os.path.join(MODULE_DIR, "test_mesh0.su2")
    SU2_MESH_1 = os.path.join(MODULE_DIR, "test_mesh1.su2")

    with pytest.raises(FileNotFoundError):
        get_mesh_marker("This_file_do_not_exist.su2")

    with pytest.raises(ValueError):
        get_mesh_marker(NOT_SU2_MESH)

    # Check if ValueError is raised when no MARKER_TAG in the SU2 mesh
    with pytest.raises(ValueError):
        get_mesh_marker(SU2_MESH_0)

    wall_marker_list, eng_bc_marker_list = get_mesh_marker(SU2_MESH_1)
    assert wall_marker_list == ["D150_VAMP_SL1", "D150_VAMP_FL1", "D150_VAMP_HL1", "D150_VAMP_W1"]
    assert eng_bc_marker_list == ["D150_ENGINE1_Intake", "D150_ENGINE1_Exhaust"]


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
