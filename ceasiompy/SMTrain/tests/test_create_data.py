"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.SMTrain.func.sampling import lh_sampling
from ceasiompy.SMTrain.func.createdata import launch_avl

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================

class TestCreateData(CeasiompyTest):

    @log_test
    def test_launch_avl(self) -> None:
        MAX_ALT = 1000.0
        MAX_MACH = 0.3
        MAX_AOA = MAX_AOS = 15.0
        launch_avl(
            cpacs=self.test_cpacs,
            lh_sampling_path=lh_sampling(
                n_samples=2,  # Run AVL at least once
                ranges={
                    "altitude": [0, MAX_ALT],
                    "machNumber": [0.1, MAX_MACH],
                    "angleOfAttack": [0, MAX_AOA],
                    "angleOfSideslip": [0, MAX_AOS],
                },
                results_dir=current_workflow_dir(),  # Where to store AVL results
                random_state=42,
            ),
            objective="cl",
        )


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
