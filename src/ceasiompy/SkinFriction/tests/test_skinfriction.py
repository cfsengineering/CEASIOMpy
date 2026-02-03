"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
    current_workflow_dir,
)
from ceasiompy.SkinFriction.skinfriction import (
    main as add_skin_friction,
    estimate_skin_friction_coef,
)
from pytest import approx

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.SkinFriction import MODULE_NAME

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestSkinFriction(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.results_dir = get_results_directory(MODULE_NAME, create=True, wkflow_dir=cls.wkdir)

    def test_estimate_skin_friction_coef(self):
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

    def test_add_skin_friction(self):
        """Test function 'add_skin_friction'"""

        workflow_dir = current_workflow_dir()

        # User the function to add skin frictions
        add_skin_friction(
            self.test_cpacs,
            wkdir=get_results_directory(MODULE_NAME, create=True, wkflow_dir=workflow_dir),
        )

        # Read the aeromap with the skin friction added in the output cpacs file
        apm_sf = self.test_cpacs.get_aeromap_by_uid("test_apm_SkinFriction")

        # Expected values
        cl_list_expected = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        cd_list_expected = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        cs_list_expected = [0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001]

        assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cl"), cl_list_expected)])
        assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cd"), cd_list_expected)])
        assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cs"), cs_list_expected)])


# Main

if __name__ == "__main__":
    main(verbosity=0)
