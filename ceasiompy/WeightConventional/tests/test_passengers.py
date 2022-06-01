"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/passengers.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import pytest

from ceasiompy.WeightConventional.func.passengers import stringed_seat_row

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_stringed_seat_row():
    """Test function 'stringed_seat_row'"""

    assert stringed_seat_row([1, 0]) == "\nX || "
    assert stringed_seat_row([1, 0, 1]) == "\nX || X "
    assert stringed_seat_row([1, 1, 0, 1, 1]) == "\nX X || X X "
    assert stringed_seat_row([1, 1, 0, 1, 1, 1, 0, 1, 1]) == "\nX X || X X X || X X "

    with pytest.raises(ValueError):
        stringed_seat_row([1, 7, 1])


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
