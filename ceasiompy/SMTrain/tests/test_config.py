"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.SMTrain.func.createdata import retrieve_aeromap_data

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.SMTrain import SMTRAIN_AVL_DATABASE_XPATH

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestConfig(CeasiompyTest):

    @log_test
    def test_retrieve_aeromap_data(self) -> None:
        # Load the default test
        cpacs = self.test_cpacs

        # Specify to not add data from ceasiompy.db
        cpacs.tixi.updateBooleanElement(SMTRAIN_AVL_DATABASE_XPATH, False)
        output = retrieve_aeromap_data(
            cpacs=cpacs,
            aeromap_uid="aeromap_empty",
            objective="cl",
        )
        print(output)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
