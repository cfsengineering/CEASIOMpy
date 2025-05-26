"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'

| Author : Aidan Jungo
| Creation: 2019-07-17

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.ceasiompyutils import get_results_directory, current_workflow_dir
from ceasiompy.SkinFriction.skinfriction import (
    main as add_skin_friction,
    estimate_skin_friction_coef,
)
from cpacspy.cpacspy import CPACS
from pytest import approx

from ceasiompy.utils.commonpaths import LOGFILE

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "D150_simple_SkinFriction_test.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_skinfriction_test_output.xml")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_estimate_skin_friction_coef():
    """Test function 'estimate_skin_friction_coef'"""

    # Normal case
    # {cd0:[wetted_area,wing_area,wing_span,mach,alt]}
    test_dict = {
        0.005308238904488722: [1, 1, 1, 1, 1],
        0.021046702729598663: [701.813, 100, 20, 0.78, 12000],
        0.00655: [1, 1, 1, 0, 0],
    }

    for cd0, inputs in test_dict.items():
        assert cd0 == approx(estimate_skin_friction_coef(*inputs))

    with open(LOGFILE, "r") as log_file:
        estimate_skin_friction_coef(400.0, 50, 20, 0.22, 12000)
        assert "Reynolds number is out of range." in log_file.read()

    with open(LOGFILE, "r") as log_file:
        estimate_skin_friction_coef(3401.0, 100, 20, 0.78, 12000)
        assert "Wetted area is not in the correct range." in log_file.read()

    with open(LOGFILE, "r") as log_file:
        estimate_skin_friction_coef(701.813, 19, 20, 0.78, 12000)
        assert "Wing area is not in the correct range." in log_file.read()

    with open(LOGFILE, "r") as log_file:
        estimate_skin_friction_coef(701.813, 100, 75, 0.78, 12000)
        assert "Wing span is not in the correct range." in log_file.read()


def test_add_skin_friction():
    """Test function 'add_skin_friction'"""

    cpacs = CPACS(CPACS_IN_PATH)
    workflow_dir = current_workflow_dir()
    # User the function to add skin frictions
    add_skin_friction(
        cpacs,
        wkdir=get_results_directory("SkinFriction", create=True, wkflow_dir=workflow_dir),
    )

    # Read the aeromap with the skin friction added in the output cpacs file
    apm_sf = cpacs.get_aeromap_by_uid("test_apm_SkinFriction")

    # Expected values
    cl_list_expected = [0.1, 0.102944, 0.1, 0.102944]
    cd_list_expected = [0.0269518, 0.0266942, 0.0266942, 0.0264406]
    cs_list_expected = [0.001, 0.001, 0.00394364, 0.00394364]

    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cl"), cl_list_expected)])
    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cd"), cd_list_expected)])
    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cs"), cs_list_expected)])

    # Remove the output cpacs file if exist
    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()
