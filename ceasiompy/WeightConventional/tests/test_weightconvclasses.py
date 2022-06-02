"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/weightconvclasses.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import pytest

from cpacspy.cpacspy import CPACS

from ceasiompy.WeightConventional.func.weightconvclasses import (
    Cabin,
    check_aisle_nb,
    check_toilet_length,
    stringed_seat_row,
)
from ceasiompy.WeightConventional.func.weightutils import TOILET_LENGTH
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent
TEST_CPACS_IN = Path(CPACS_FILES_PATH, "D150_simple.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestWeightConv:

    cpacs = CPACS(TEST_CPACS_IN)

    weight_conv = Cabin(cpacs, cabin_length=22.5, cabin_width=4.0)

    def test_mass_properties(self):

        assert self.weight_conv.abreast_nb == 6
        assert self.weight_conv.row_nb == 25
        assert self.weight_conv.passenger_nb == 150

        assert self.weight_conv.cabin_crew_nb == 4
        assert self.weight_conv.crew_nb == 6
        assert self.weight_conv.crew_mass == 476.0
        assert self.weight_conv.passenger_mass == 15_750.0
        assert self.weight_conv.people_mass == 16_226.0
        assert self.weight_conv.toilet_nb == 3

        self.weight_conv.write_seat_config()


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
