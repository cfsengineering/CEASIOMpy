"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/WeightConventional/func/crewmembers.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-05-30

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.WeightConventional.func.crewmembers import estimate_crew

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_estimate_crew():
    """Test function 'estimate_crew'"""

    assert estimate_crew(pass_nb=500, payload=220_000, pilot_nb=3) == (14, 11, 1054)
    assert estimate_crew(pass_nb=300, payload=120_000, pilot_nb=2) == (9, 7, 680)
    assert estimate_crew(pass_nb=52, payload=40_000, pilot_nb=2) == (4, 2, 340)
    assert estimate_crew(pass_nb=50, payload=32_000, pilot_nb=2) == (3, 1, 272)
    assert estimate_crew(pass_nb=20, payload=5_000, pilot_nb=2) == (3, 1, 272)
    assert estimate_crew(pass_nb=18, payload=5_000, pilot_nb=2) == (3, 1, 272)
    assert estimate_crew(pass_nb=12, payload=3_000, pilot_nb=2) == (2, 0, 204)
    assert estimate_crew(pass_nb=12, payload=3_000, pilot_nb=2) == (2, 0, 204)
    assert estimate_crew(pass_nb=7, payload=3_000, pilot_nb=2) == (2, 0, 204)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
