"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pandas import read_csv
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.utils.decorators import log_test
from ceasiompy.SMTrain.func.sampling import (
    lh_sampling,
    # split_data
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================

class TestCreateData(CeasiompyTest):

    @log_test
    def test_lh_sampling(self) -> None:
        MAX_ALT = 1000.0
        MAX_MACH = 0.3
        MAX_AOA = MAX_AOS = 15.0
        lh_sampling_path = lh_sampling(
            n_samples=1,  # Run AVL at least once
            ranges={
                "altitude": [0, MAX_ALT],
                "machNumber": [0.1, MAX_MACH],
                "angleOfAttack": [0, MAX_AOA],
                "angleOfSideslip": [0, MAX_AOS],
            },
            results_dir=current_workflow_dir(),  # Where to store AVL results
            random_state=42,
        )

        self.assertTrue(lh_sampling_path.is_file(), "Sampling CSV file was not created.")
        # Read the csv at lh_sampling_path and check if values are specific ones
        # Read the csv at lh_sampling_path and check if values are within the specified ranges
        df = read_csv(lh_sampling_path)
        self.assertIn("altitude", df.columns)
        self.assertIn("machNumber", df.columns)
        self.assertIn("angleOfAttack", df.columns)
        self.assertIn("angleOfSideslip", df.columns)

        # Check the ranges
        self.assertGreaterEqual(df["altitude"].iloc[0], 0)
        self.assertLessEqual(df["altitude"].iloc[0], MAX_ALT)
        self.assertGreaterEqual(df["machNumber"].iloc[0], 0.1)
        self.assertLessEqual(df["machNumber"].iloc[0], MAX_MACH)
        self.assertGreaterEqual(df["angleOfAttack"].iloc[0], 0)
        self.assertLessEqual(df["angleOfAttack"].iloc[0], MAX_AOA)
        self.assertGreaterEqual(df["angleOfSideslip"].iloc[0], 0)
        self.assertLessEqual(df["angleOfSideslip"].iloc[0], MAX_AOS)

        print(df)


    # @log_test
    # def test_split_data(self) -> None:
    #     splitted_data = split_data(
    #         fidelity_level=LEVEL_ONE,
    #         fidelity_datasets=,
    #     )

    #     splitted_data = split_data(
    #         fidelity_level=LEVEL_TWO,
    #         fidelity_datasets=,
    #     )


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
