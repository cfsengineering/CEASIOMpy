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
from ceasiompy.SMTrain.func.createdata import retrieve_aeromap_data

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestConfig(CeasiompyTest):

    @log_test
    def test_retrieve_aeromap_data(self) -> None:
        output = retrieve_aeromap_data(
            cpacs=self.test_cpacs,
            aeromap_uid="aeromap_empty",
            objective="cl",
        )
        print(output)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
