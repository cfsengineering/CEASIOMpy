"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script estimates all the cabin related parameters (Crew, passenger, equipment, etc.)

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    WB_ABREAST_NB_XPATH,
    WB_AISLE_WIDTH_XPATH,
    WB_CAB_CREW_NB_XPATH,
    WB_CREW_MASS_XPATH,
    WB_CREW_NB_XPATH,
    WB_PASSENGER_MASS_XPATH,
    WB_PASSENGER_NB_XPATH,
    WB_PEOPLE_MASS_XPATH,
    WB_ROW_NB_XPATH,
    WB_SEAT_LENGTH_XPATH,
    WB_SEAT_WIDTH_XPATH,
    WB_TOILET_NB_XPATH,
)
from ceasiompy.WeightConventional.func.weightutils import (
    CABIN_CREW_MASS,
    PASSENGER_MASS,
    PASSENGER_PER_TOILET,
    PILOT_MASS,
    TOILET_LENGTH,
)
from cpacspy.cpacsfunctions import add_value, get_value_or_default

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


class Cabin:
    """
    Class to store and calculate the equipments/people mass and count related to the cabin.

    Attributes:
        cpacs (Cpacs): The Cpacs object.
        cabin_length (float): Length of the cabin.
        cabin_width (float): Width of the cabin.
        mass_payload (float): Mass of the payload.

    """

    def __init__(self, cpacs, cabin_length, cabin_width, payload_mass=0):

        self.cpacs = cpacs
        self.cabin_length = cabin_length
        self.cabin_width = cabin_width
        self.mass_payload = payload_mass

        self.pilot_nb = 2

    @property
    def abreast_nb(self):

        seat_width = get_value_or_default(self.cpacs.tixi, WB_SEAT_WIDTH_XPATH, 0.525)
        aisle_width = get_value_or_default(self.cpacs.tixi, WB_AISLE_WIDTH_XPATH, 0.42)

        for i in range(10, 0, -1):
            if (seat_width * i + aisle_width * check_aisle_nb(i)) <= self.cabin_width:
                return i

        log.warning("The cabin width is too narrow to fit one abreast and one aisle")
        return 0

    @property
    def row_nb(self):

        seat_length = get_value_or_default(self.cpacs.tixi, WB_SEAT_LENGTH_XPATH, 0.74)

        for i in range(100, 0, -1):
            passenger_nb_tmp = self.abreast_nb * i
            if (seat_length * i + check_toilet_length(passenger_nb_tmp)) <= self.cabin_length:
                return i

        log.warning("The cabin length is too short to fit one row!")
        return 0

    @property
    def passenger_nb(self):
        return self.abreast_nb * self.row_nb

    @property
    def cabin_crew_nb(self):
        """Function to evaluate the number of crew members on board.

        Source : https://www.gpo.gov/fdsys/pkg/CFR-2011-title14-vol3/xml/CFR-2011
                -title14-vol3-sec121-391.xml
        """

        if self.passenger_nb >= 101:
            return int(self.passenger_nb / 50) + 1
        elif self.passenger_nb >= 51:
            return 2
        elif self.passenger_nb >= 19 and self.mass_payload <= 3400.0:
            return 1
        elif self.passenger_nb >= 9 and self.mass_payload > 3400.0:
            return 1
        else:
            return 0

    @property
    def crew_nb(self):
        # TODO: write in cpacs (same for the other properties)
        return self.pilot_nb + self.cabin_crew_nb

    @property
    def crew_mass(self):
        return self.pilot_nb * PILOT_MASS + self.cabin_crew_nb * CABIN_CREW_MASS

    @property
    def passenger_mass(self):
        return self.passenger_nb * PASSENGER_MASS

    @property
    def people_mass(self):
        return self.crew_mass + self.passenger_mass

    @property
    def toilet_nb(self):
        return math.ceil(self.passenger_nb / PASSENGER_PER_TOILET)

    def save_to_cpacs(self):
        """Save calculated value in the CPACS object."""

        attr_to_xpath = {
            "abreast_nb": WB_ABREAST_NB_XPATH,
            "row_nb": WB_ROW_NB_XPATH,
            "passenger_nb": WB_PASSENGER_NB_XPATH,
            "passenger_mass": WB_PASSENGER_MASS_XPATH,
            "cabin_crew_nb": WB_CAB_CREW_NB_XPATH,
            "crew_nb": WB_CREW_NB_XPATH,
            "crew_mass": WB_CREW_MASS_XPATH,
            "people_mass": WB_PEOPLE_MASS_XPATH,
            "toilet_nb": WB_TOILET_NB_XPATH,
        }

        for attr, xpath in attr_to_xpath.items():
            add_value(self.cpacs.tixi, xpath, getattr(self, attr))

    def write_seat_config(self, cabin_output_file):
        """Write the seat configuration in a file in the result directory."""

        lines = open(cabin_output_file, "w")

        lines.write("\n### CABIN")

        lines.write("\n#### Crew")
        lines.write(f"\n- Pilot nb: {self.pilot_nb}")
        lines.write(f"\n- Cabin crew nb: {self.cabin_crew_nb}")
        lines.write(f"\n- Crew mass: {self.crew_mass} [kg]")
        lines.write("\n")
        lines.write("\n#### Passengers ")
        lines.write(f"\n- Passengers nb: {self.passenger_nb}")
        lines.write(f"\n- Passengers mass: {self.passenger_mass} [kg]")
        lines.write("\n")
        lines.write("\n#### Seats")
        lines.write(f"\n- Abreast nb.: {self.abreast_nb}")
        lines.write(f"\n- Row nb.: {self.row_nb}")
        lines.write(f"\n- Seats_nb : {self.passenger_nb}")
        lines.write(f"\n- Number of lavatory: {int(self.toilet_nb)}")
        lines.write("\n")
        lines.write("\n#### Possible seat configuration")
        lines.write("\nSeat = X and Aisle = || ")
        lines.write("\n")
        lines.write("\n```")
        for _ in range(self.row_nb):
            lines.write(stringed_seat_row(self.abreast_nb))
        lines.write("\n```")
        lines.close()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_aisle_nb(abreast_nb):
    """It is a static method and not property to avoid circular dependency."""

    if abreast_nb < 1:
        return 0
    elif abreast_nb <= 6:
        return 1
    else:
        return 2


def check_toilet_length(passenger_nb):
    """It is a static method and not property to avoid circular dependency."""

    toilet_nb = math.ceil(passenger_nb / PASSENGER_PER_TOILET)

    return math.ceil(toilet_nb / 2) * TOILET_LENGTH


def stringed_seat_row(abreast_nb):
    """Return a string which represent the seat row disposition."""

    if abreast_nb == 1:
        return "X ||" + "\n"
    elif abreast_nb <= 6:
        return "X " * (abreast_nb // 2) + "|| " + "X " * (abreast_nb - abreast_nb // 2) + "\n"
    elif abreast_nb == 7:
        return "X " * 2 + "|| " + "X " * 3 + "|| " + "X " * 2 + "\n"
    elif abreast_nb == 8:
        return "X " * 2 + "|| " + "X " * 4 + "|| " + "X " * 2 + "\n"
    elif abreast_nb == 9:
        return "X " * 3 + "|| " + "X " * 3 + "|| " + "X " * 3 + "\n"
    elif abreast_nb == 10:
        return "X " * 3 + "|| " + "X " * 4 + "|| " + "X " * 3 + "\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
