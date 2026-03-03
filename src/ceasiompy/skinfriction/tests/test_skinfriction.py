"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
from ceasiompy.utils.guiobjects import add_value
from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
    current_workflow_dir,
)
from ceasiompy.skinfriction.skinfriction import (
    main as add_skin_friction,
    estimate_skin_friction_coef,
)
from pytest import approx

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.skinfriction import MODULE_NAME
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH

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
            0.021046702729598663: [12000, 0.78, 100, 20, 701.813],
            0.00655: [0, 0, 1, 1, 1],
        }

        for cd0, inputs in test_dict.items():
            assert cd0 == approx(estimate_skin_friction_coef(*inputs))

    def test_add_skin_friction(self):
        """Test function 'add_skin_friction'"""

        workflow_dir = current_workflow_dir()
        add_value(
            tixi=self.test_cpacs.tixi,
            xpath=SELECTED_AEROMAP_XPATH,
            value="test_apm",
        )
        # User the function to add skin frictions
        add_skin_friction(
            cpacs=self.test_cpacs,
            results_dir=get_results_directory(MODULE_NAME, create=True, wkflow_dir=workflow_dir),
        )


# Main

if __name__ == "__main__":
    main(verbosity=0)
