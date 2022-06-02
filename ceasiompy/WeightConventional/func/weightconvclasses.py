import math
from pathlib import Path

from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.WeightConventional.func.weightutils import (
    CABIN_CREW_MASS,
    PASSENGER_MASS,
    PASSENGER_PER_TOILET,
    PILOT_MASS,
    TOILET_LENGTH,
)
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import (
    WB_AISLE_WIDTH_XPATH,
    WB_SEAT_LENGTH_XPATH,
    WB_SEAT_WIDTH_XPATH,
)

log = get_logger()


# @property
# def fuselage_thickness_ratio(self):
#     return get_value_or_default(self.cpacs.tixi, WB_FUSELAGE_THICK_XPATH, 6.63)

# @property
# def cabin_width(self):

#     return self.fuselage_width * (1 - self.fuselage_thickness_ratio / 100)


def check_aisle_nb(abreast_nb):
    """It is a static method and not property to avoid circular dependency."""

    if abreast_nb > 10:
        log.warning(
            "Aisle number is greater than 10. It is outside the range of value define for"
            "the WeightConventional module, try to use the WeightUnconventional module."
        )

    if abreast_nb < 1:
        log.warning(
            "Aisle number is less than 1. It is outside the range of value define for"
            "the WeightConventional module, try to use the WeightUnconventional module."
        )

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


class Cabin:
    """
    The class contains all the aircraft mass and weight value relative to the
    weight analysis.

    Attributes:
    mass_fuel_maxpass (float): Max fuel mass with max payload [kg]
    mass_fuel_mass (float): Max fuel mass allowed (evaluated) [kg]
    maximum_take_off_mass (float): Maximum take off mass [kg]
    operating_empty_mass (float): Operating empty mass [kg]
    mass_payload (float): Payload mass [kg]
    MAX_FUEL_MASS (float): Maximum fuel mass allowed (chosen) [kg]
    max_payload (float): Maximum payload mass allowed [kg]
    people_mass (float): Mass of people inside the aircraft [kg]
    mass_cargo (float): Extra possible payload [kg]
    zero_fuel_mass (float): Zero fuel mass [kg]
    crew_mass (float): Crew members total mass [kg]
    abreast_nb (int): Number of abreast.
    row_nb (int): Number of rows.
    passenger_nb (int): Number of passengers.
    toilet_nb (int): Number of toilets.
    crew_nb (int): Number of total crew members.
    cabin_crew_nb (int): Number of cabin crew members.
    wing_loading (float): Wing loading [kg/m^2].
    passenger_mass ...

    """

    def __init__(self, cpacs, cabin_length, cabin_width):

        self.cpacs = cpacs
        self.cabin_length = cabin_length
        self.cabin_width = cabin_width

        self.wing_loading = 0

        self.mass_fuel_maxpass = 0
        self.mass_fuel_max = 0
        self.maximum_take_off_mass = 0
        self.operating_empty_mass = 0
        self.mass_payload = 0
        self.MAX_FUEL_MASS = 0
        self.max_payload = 0
        self.mass_cargo = 0
        self.zero_fuel_mass = 0

        # People
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

    def write_seat_config(self):
        """Write the seat configuration in a file in the result directory."""

        result_dir = get_results_directory("WeightConventional")
        output_file = Path(result_dir, "Seats_disposition.out")

        lines = open(output_file, "w")
        lines.write("\n---------------------------------------")
        lines.write(f"\nAbreast nb.: {self.abreast_nb}")
        lines.write(f"\nRow nb.: {self.row_nb}")
        lines.write(f"\nSeats_nb : {self.passenger_nb}")
        lines.write("-----------------------------------------")
        lines.write("\nPossible seat configuration")
        lines.write("\nSeat = X and Aisle = || ")
        lines.write("\n---------------------------------------\n")

        for _ in range(self.row_nb):
            lines.write(stringed_seat_row(self.abreast_nb))

        lines.close()
