"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/cabin.py'

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
from pathlib import Path

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.commonxpath import WB_ABREAST_NB_XPATH, WB_PEOPLE_MASS_XPATH
from ceasiompy.WeightConventional.func.cabin import (
    Cabin,
    check_aisle_nb,
    check_toilet_length,
    stringed_seat_row,
)
from ceasiompy.WeightConventional.func.weightutils import TOILET_LENGTH
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
TEST_CPACS_IN = Path(CPACS_FILES_PATH, "D150_simple.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestCabin:

    cpacs = CPACS(TEST_CPACS_IN)

    cabins = []
    cabins.append(Cabin(cpacs, cabin_length=22.5, cabin_width=4.0, payload_mass=10_000.0))
    cabins.append(Cabin(cpacs, cabin_length=12.5, cabin_width=2.0, payload_mass=5_000.0))
    cabins.append(Cabin(cpacs, cabin_length=37.5, cabin_width=5.6, payload_mass=100_000.0))
    cabins.append(Cabin(cpacs, cabin_length=5.5, cabin_width=0.50, payload_mass=1_000.0))

    results_attributes = {
        "abreast_nb": [6, 3, 9, 0],
        "row_nb": [25, 14, 40, 7],
        "passenger_nb": [150, 42, 360, 0],
        "cabin_crew_nb": [4, 1, 8, 0],
        "crew_nb": [6, 3, 10, 2],
        "crew_mass": [476.0, 272.0, 748.0, 204.0],
        "passenger_mass": [15_750.0, 4_410.0, 37_800.0, 0.0],
        "people_mass": [16_226.0, 4_682.0, 38_548.0, 204.0],
        "toilet_nb": [3, 1, 8, 0],
    }

    def test_mass_properties(self):

        for c, cabin in enumerate(self.cabins):
            for attribute, results in self.results_attributes.items():
                assert getattr(cabin, attribute) == results[c]

    def test_cabin_crew_nb_attribute(self):

        assert self.cabins[0].cabin_crew_nb == 4
        assert self.cabins[1].cabin_crew_nb == 1
        assert self.cabins[2].cabin_crew_nb == 8
        assert self.cabins[3].cabin_crew_nb == 0

    def test_save_to_cpacs(self):

        self.cabins[0].save_to_cpacs()

        assert self.cpacs.tixi.getTextElement(WB_ABREAST_NB_XPATH) == str(
            self.results_attributes["abreast_nb"][0]
        )
        assert self.cpacs.tixi.getTextElement(WB_PEOPLE_MASS_XPATH) == str(
            self.results_attributes["people_mass"][0]
        )

    def test_write_seat_config(self):

        if TEST_OUT_PATH.exists():
            shutil.rmtree(TEST_OUT_PATH)
        TEST_OUT_PATH.mkdir()

        cabin_config_file = Path(TEST_OUT_PATH, "Cabin.md")

        self.cabins[0].write_seat_config(cabin_config_file)

        assert cabin_config_file.exists()

        with open(cabin_config_file, "r") as f:
            lines = f.readlines()

        assert any("- Number of abreast: 6" in line for line in lines)
        assert any("- Number of row: 25" in line for line in lines)
        assert any("- Number of seats : 150" in line for line in lines)
        assert any("X X X || X X X " in line for line in lines)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_check_aisle_nb():

    assert check_aisle_nb(0) == 0
    assert check_aisle_nb(1) == 1
    assert check_aisle_nb(6) == 1
    assert check_aisle_nb(7) == 2
    assert check_aisle_nb(10) == 2


def test_check_toilet_length():

    assert check_toilet_length(0) == 0
    assert check_toilet_length(1) == TOILET_LENGTH
    assert check_toilet_length(100) == TOILET_LENGTH
    assert check_toilet_length(101) == 2 * TOILET_LENGTH
    assert check_toilet_length(201) == 3 * TOILET_LENGTH


def test_stringed_seat_row():
    """Test function 'stringed_seat_row'"""

    assert stringed_seat_row(1) == "X ||\n"
    assert stringed_seat_row(2) == "X || X \n"
    assert stringed_seat_row(3) == "X || X X \n"
    assert stringed_seat_row(4) == "X X || X X \n"
    assert stringed_seat_row(5) == "X X || X X X \n"
    assert stringed_seat_row(7) == "X X || X X X || X X \n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
