"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from copy import deepcopy
from ceasiompy.utils.decorators import log_test
from ceasiompy.SMTrain.func.createdata import retrieve_aeromap_data
from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)

from unittest import main
from pandas import DataFrame
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.SMTrain import SMTRAIN_AVL_DATABASE_XPATH

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestConfig(CeasiompyTest):

    @log_test
    def test_retrieve_aeromap_data(self) -> None:
        # Load the default test
        cpacs = deepcopy(self.test_cpacs)
        tixi = cpacs.tixi

        # Specify to not add data from ceasiompy.db
        create_branch(tixi, SMTRAIN_AVL_DATABASE_XPATH)
        add_value(tixi, SMTRAIN_AVL_DATABASE_XPATH, False)
        full_df = retrieve_aeromap_data(
            cpacs=cpacs,
            aeromap_uid="aeromap_empty",
            objective="cl",
        )
        self.assertTrue(
            full_df.equals(
                DataFrame({
                    "altitude": [0.0],
                    "machNumber": [0.3],
                    "angleOfAttack": [0.0],
                    "angleOfSideslip": [0.0],
                    "cl": [float("nan")],
                })
            )
        )

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
