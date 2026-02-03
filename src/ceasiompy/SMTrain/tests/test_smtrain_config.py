"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# Imports

from ceasiompy.utils.decorators import log_test
from ceasiompy.SMTrain.func.createdata import retrieve_aeromap_data

from unittest import main
from pandas import DataFrame
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestConfig(CeasiompyTest):

    @log_test
    def test_retrieve_aeromap_data(self) -> None:
        full_df = retrieve_aeromap_data(
            cpacs=self.test_cpacs,
            aeromap_uid="test_apm",
            objective="cl",
        )
        self.assertTrue(
            full_df.equals(
                DataFrame(
                    {
                        "altitude": [0.0, 0.0, 0.0, 0.0, 1000.0, 1000.0, 1000.0, 1000],
                        "machNumber": [0.3, 0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.5],
                        "angleOfAttack": [0.0, 10.0, 0.0, 10.0, 0.0, 10.0, 0.0, 10],
                        "angleOfSideslip": [0.0, 0.0, 10.0, 10.0, 0.0, 0.0, 10.0, 10],
                        "cl": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
                    }
                )
            )
        )


# Main
if __name__ == "__main__":
    main(verbosity=0)
