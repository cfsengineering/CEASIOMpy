import math
from ceasiompy.WeightConventional.func.weightutils import (
    CABIN_CREW_MASS,
    PASSENGER_MASS,
    PASSENGER_PER_TOILET,
    PILOT_MASS,
    TOILET_LENGTH,
)


class NewWeightOutputs:
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
    abreast_nb (int): Number of abreasts.
    row_nb (int): Number of rows.
    pass_nb (int): Number of passengers.
    toilet_nb (int): Number of toilets.
    crew_nb (int): Number of total crew members.
    cabin_crew_nb (int): Number of cabin crew members.
    wing_loading (float): Wing loading [kg/m^2].
    passenger_mass ...

    """

    def __init__(self):

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

        # Equipements (TODO: calculate from cabin length and width)
        self.abreast_nb = 0
        self.row_nb = 0

        # People
        self.pilot_nb = 2

    @property
    def pass_nb(self):
        return self.abreast_nb * self.row_nb

    @property
    def toilet_nb(self):
        return math.ceil(self.pass_nb / PASSENGER_PER_TOILET)

    @property
    def total_toilet_length(self):
        return math.ceil(self.toilet_nb / 2) * TOILET_LENGTH

    @property
    def cabin_crew_nb(self):
        """Function to evaluate the number of crew members on board.

        Source : https://www.gpo.gov/fdsys/pkg/CFR-2011-title14-vol3/xml/CFR-2011
                -title14-vol3-sec121-391.xml
        """

        if self.pass_nb >= 101:
            return int(self.pass_nb / 50) + 1
        elif self.pass_nb >= 51:
            return 2
        elif self.pass_nb >= 19 and self.mass_payload <= 3400.0:
            return 1
        elif self.pass_nb >= 9 and self.mass_payload > 3400.0:
            return 1
        else:
            return 0

    @property
    def crew_nb(self):
        return self.pilot_nb + self.cabin_crew_nb

    @property
    def crew_mass(self):
        return self.pilot_nb * PILOT_MASS + self.cabin_crew_nb * CABIN_CREW_MASS

    @property
    def passenger_mass(self):
        return self.pass_nb * PASSENGER_MASS

    @property
    def people_mass(self):
        return self.crew_mass + self.passenger_mass
