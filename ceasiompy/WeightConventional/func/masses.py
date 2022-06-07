"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script store all the aircraft masses ...

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math
from pathlib import Path

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.oem import estimate_oem

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import (
    FUEL_DENSITY_XPATH,
    MASS_CARGO_XPATH,
    WB_ABREAST_NB_XPATH,
    WB_AISLE_WIDTH_XPATH,
    WB_CAB_CREW_NB_XPATH,
    WB_CREW_MASS_XPATH,
    WB_CREW_NB_XPATH,
    WB_MAX_PAYLOAD_XPATH,
    WB_PASSENGER_MASS_XPATH,
    WB_PASSENGER_NB_XPATH,
    WB_PEOPLE_MASS_XPATH,
    WB_ROW_NB_XPATH,
    WB_SEAT_LENGTH_XPATH,
    WB_SEAT_WIDTH_XPATH,
    WB_TOILET_NB_XPATH,
)
from ceasiompy.WeightConventional.func.weightutils import UNUSABLE_FUEL_RATIO

from cpacspy.cpacsfunctions import add_value, get_value_or_default

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


class AircfaftMasses:
    """
    Class to store and calculate aircraft masses.

    Attributes:
        ...

    """

    def __init__(self, cpacs):

        self.cpacs = cpacs

        # User input
        # Maximum payload allowed, set 0 if equal to max passenger mass.
        self.max_payload = get_value_or_default(cpacs.tixi, WB_MAX_PAYLOAD_XPATH, 0)
        self.mass_cargo = get_value_or_default(cpacs.tixi, MASS_CARGO_XPATH, 0.0)
        self.fuel_density = 800  # TODO: deal with multiple fuel store in cpacs
        # self.fuel_density = get_value_or_default(cpacs.tixi, FUEL_DENSITY_XPATH, 800)
        # add_uid(cpacs.tixi, FUEL_DENSITY_XPATH, "kerosene")

        # self.mass_fuel_maxpass = 0
        self.mass_fuel_max = 0
        self.mass_payload = 0
        self.max_payload = 0
        # self.mass_people = 0
        # self.mass_cargo = 0
        # self.zero_fuel_mass = 0
        # self.mass_crew = 0

    def get_mtom(self, fuselage_length, fuselage_width, wing_area, wing_span, results_dir):

        self.mtom = estimate_mtom(
            fuselage_length, fuselage_width, wing_area, wing_span, results_dir
        )

    def get_oem(self, fuselage_length, wing_span, turboprop):
        # Operating Empty Mass evaluation

        self.oem = estimate_oem(self.mtom, fuselage_length, wing_span, turboprop)

    def get_mass_fuel_max(self, wing_area, fuse_length, max_fuel_vol, turboprop):
        # Fuel Mass evaluation
        # Maximum fuel that can be stored with maximum number of passengers.

        if not max_fuel_vol:  # TODO while retesting, redo fitting
            if turboprop:
                if wing_area > 55.00:
                    coef = 4.6
                else:
                    coef = 3.6
            elif wing_area < 90.00:
                if fuse_length[0] < 60.00:
                    coef = 4.3
                else:
                    coef = 4.0
            elif wing_area < 300.00:
                if fuse_length[0] < 35.00:
                    coef = 3.6
                else:
                    coef = 3.8
            elif wing_area < 400.00:
                coef = 2.2
            elif wing_area < 600.00:
                coef = 2.35
            else:
                coef = 2.8

            self.mass_fuel_max = self.mtom / coef
        else:
            self.mass_fuel_max = max_fuel_vol * self.fuel_density

    @property
    def mass_fuel_maxpass(self):
        return self.mtom - self.oem - self.mass_payload

    def check_max_payload(self):
        # maxp = False
        if self.max_payload > 0 and self.mass_payload > self.max_payload:
            self.mass_payload = self.max_payload
            # maxp = True
            # new_passenger_nb = self.max_payload / (PASSENGER_MASS)
            # log.info(f"With the fixed payload, passenger nb reduced to: {new_passenger_nb}")

    @property
    def zfm(self):
        # Zero Fuel Mass evaluation
        return self.mtom - self.mass_fuel_maxpass + UNUSABLE_FUEL_RATIO * self.mass_fuel_max

    def get_wing_loading(self, wings_area):
        self.wing_loading = self.mtom / wings_area


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
