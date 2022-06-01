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

from ceasiompy.WeightConventional.func.weightconvclasses import NewWeightOutputs

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestWeightConv:

    weight_conv = NewWeightOutputs()

    def test_mass_properties(self):

        assert self.weight_conv.cabin_crew_nb == 0
        assert self.weight_conv.crew_nb == 2
        assert self.weight_conv.crew_mass == 204.0
        assert self.weight_conv.passenger_mass == 0.0
        assert self.weight_conv.people_mass == 204.0
        assert self.weight_conv.toilet_nb == 0
        assert self.weight_conv.total_toilet_length == 0.0

        self.weight_conv.abreast_nb = 6
        self.weight_conv.row_nb = 25

        assert self.weight_conv.cabin_crew_nb == 4
        assert self.weight_conv.crew_nb == 6
        assert self.weight_conv.crew_mass == 476.0
        assert self.weight_conv.passenger_mass == 15_750.0
        assert self.weight_conv.people_mass == 16_226.0
        assert self.weight_conv.toilet_nb == 3
        assert self.weight_conv.total_toilet_length == 3.8


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test WeightConventional")
    print("To run test use the following command:")
    print(">> pytest -v")
