"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the weight analysis.

| Works with Python 3.6
| Author : Stefano Piccini
| Date of creation: 2018-09-27

TODO:

    * Maybe gather all parameter in one class (or one class with subclasses)

"""


# =============================================================================
#   IMPORTS
# =============================================================================


from cpacspy.cpacsfunctions import add_uid, get_value_or_default, open_tixi
from ceasiompy.utils.xpath import (
    CAB_CREW_XPATH,
    F_XPATH,
    FUEL_XPATH,
    GEOM_XPATH,
    MASSBREAKDOWN_XPATH,
    ML_XPATH,
    PASS_XPATH,
    PILOTS_XPATH,
    PROP_XPATH,
)

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =============================================================================
#   CLASSES
# =============================================================================


class UserInputs:
    """
    The class contains all the default values for the inputs required for
    the weight analysis.

    Source:
    https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf

    Attributes:
    IS_DOUBLE_FLOOR (int):  0 = no 2nd floor.
                            1 = full 2nd floor (A380),
                            2 = half 2nd floor (B747)
    pilot_nb (int):         Number of pilots[-].
    MASS_PILOT (int):       Pilot mass [kg] .
    MASS_CABIN_CREW (int):  Cabin crew mass[kg].
    MASS_PASS (int):        Passenger mass_cabin_crew [kg].
    MAX_PAYLOAD (int):      Maximum payload allowed, set 0 if equal to max passenger mass.
    MAX_FUEL_VOL (int):     Maximum fuel volume allowed [l].
    PASS_PER_TOILET (int):  Min 1 toilette per 50 passenger.
    FUEL_DENSITY (float) :  Fuel density [kg/m^3].
    RES_FUEL_PERC (float):  % of the total fuel, unusable fuel_consumption.
    TURBOPROP (bool):       Set True if the engine is a turboprop.

    """

    def __init__(self):
        self.IS_DOUBLE_FLOOR = 0
        self.PILOT_NB = 2
        self.MASS_PILOT = 102
        self.MASS_CABIN_CREW = 68
        self.MASS_PASS = 105
        self.MASS_CARGO = 0.0
        self.MAX_PAYLOAD = 0
        self.MAX_FUEL_VOL = 0
        self.PASS_PER_TOILET = 50
        self.FUEL_DENSITY = 800
        self.RES_FUEL_PERC = 0.06
        self.TURBOPROP = False

    def get_user_inputs(self, cpacs_path):
        """Get user input from the CPACS file

        The function 'get_user_inputs' extracts from the CPACS file the required
        input data, the code will use the default value when they are missing.

        Args:
            cpacs_path (str): Path to CPACS file

        """

        tixi = open_tixi(cpacs_path)

        description = "User geometry input"
        get_value_or_default(tixi, GEOM_XPATH + "/description", description)

        self.IS_DOUBLE_FLOOR = get_value_or_default(tixi, GEOM_XPATH + "/isDoubleFloor", 0)
        self.PILOT_NB = get_value_or_default(tixi, PILOTS_XPATH + "/pilotNb", 2)
        self.MASS_PILOT = get_value_or_default(tixi, PILOTS_XPATH + "/pilotMass", 102)
        self.MASS_CABIN_CREW = get_value_or_default(
            tixi, CAB_CREW_XPATH + "/cabinCrewMemberMass", 68
        )
        self.MASS_PASS = get_value_or_default(tixi, PASS_XPATH + "/passMass", 105)
        self.PASS_PER_TOILET = get_value_or_default(tixi, PASS_XPATH + "/passPerToilet", 50)

        description = "Desired max fuel volume [m^3] and payload mass [kg]"
        get_value_or_default(tixi, ML_XPATH + "/description", description)

        self.MAX_PAYLOAD = get_value_or_default(tixi, ML_XPATH + "/maxPayload", 0)
        self.MAX_FUEL_VOL = get_value_or_default(tixi, ML_XPATH + "/maxFuelVol", 0)
        self.MASS_CARGO = get_value_or_default(
            tixi, MASSBREAKDOWN_XPATH + "/payload/mCargo/massDescription/mass", 0.0
        )
        self.FUEL_DENSITY = get_value_or_default(tixi, F_XPATH + "/density", 800)
        add_uid(tixi, F_XPATH, "kerosene")

        self.TURBOPROP = get_value_or_default(tixi, PROP_XPATH + "/turboprop", False)
        self.RES_FUEL_PERC = get_value_or_default(tixi, FUEL_XPATH + "/resFuelPerc", 0.06)

        tixi.save(cpacs_path)


class InsideDimensions:
    """
    The class contains all the dimensions of the inside structure
    of the aircraft.

    Attributes:
    seat_length (float): Seats length [m]
    seat_width (float): Seats width [m]
    aisle_width (float): Aisles width [m]
    nose_length (float): Nose length [m]
    tail_length (float): Tail length [m]
    fuse_thick (float): Fuselage thickness, % of fuselage width [-]
    toilet_length (float): Common space length [m]
    nose_length (float): Length of the aircraft nose [m]
    tail_length (float): Length of the aircraft tail [m]
    cabin_length (float): Length of the aircraft cabin [m]
    cabin_width (float): Width of the aircraft cabin [m]
    cabin_area (float): Area of the aircraft cabin [m^2]

    """

    def __init__(self, fuse_length, fuse_width):

        if fuse_length < 15.00:
            self.seat_length = 1.4
        else:
            self.seat_length = 0.74

        self.seat_width = 0.525
        self.aisle_width = 0.42
        self.fuse_thick = 6.63

        self.nose_length = 0
        self.tail_length = 0

        # [m] Adding common space in relation with airplane dimensions.
        if fuse_length >= 70:
            self.toilet_length = 4.2
        elif fuse_length >= 65:
            self.toilet_length = 2.7
        else:
            self.toilet_length = 1.9
        # [m] Common space dimension
        # in longitudinal direction.
        # --- Value to be evaluated ---
        self.cabin_width = 0
        self.cabin_area = 0

    def get_inside_dim(self, cpacs_path):
        """Get user input from the CPACS file

        The function 'get_inside_dim' extracts from the CPACS file the required
        aircraft inside dimension, the code will use the default value when they are
        missing.

        Args:
            cpacs_path (str): Path to CPACS file

        """

        tixi = open_tixi(cpacs_path)

        # Get inside dimension from the CPACS file if exit
        self.seat_width = get_value_or_default(tixi, GEOM_XPATH + "/seatWidth", 0.525)
        self.seat_length = get_value_or_default(tixi, GEOM_XPATH + "/seatLength", self.seat_length)
        self.aisle_width = get_value_or_default(tixi, GEOM_XPATH + "/aisleWidth", 0.42)
        self.fuse_thick = get_value_or_default(tixi, GEOM_XPATH + "/fuseThick", 6.63)
        self.toilet_length = get_value_or_default(
            tixi, GEOM_XPATH + "/toiletLength", self.toilet_length
        )

        tixi.save(cpacs_path)


class MassesWeights:
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
    MAX_PAYLOAD (float): Maximum payload mass allowed [kg]
    mass_people (float): Mass of people inside the aircraft [kg]
    mass_cargo (float): Extra possible payload [kg]
    zero_fuel_mass (float): Zero fuel mass [kg]
    mass_crew (float): Crew members total mass [kg]

    """

    def __init__(self):
        self.mass_fuel_maxpass = 0
        self.mass_fuel_max = 0
        self.maximum_take_off_mass = 0
        self.operating_empty_mass = 0
        self.mass_payload = 0
        self.MAX_FUEL_MASS = 0
        self.MAX_PAYLOAD = 0
        self.mass_people = 0
        self.mass_cargo = 0
        self.zero_fuel_mass = 0
        self.mass_crew = 0


class WeightOutput:
    """
    The class contains some of the output value of the weight analysis.

    Attributes:
    abreast_nb (int): Number of abreasts.
    row_nb (int): Number of rows.
    pass_nb (int): Number of passengers.
    toilet_nb (int): Numbre of toilets.
    crew_nb (int): Number of total crew members.
    cabin_crew_nb (int): Number of cabin crew members.
    PILOT_NB (int): Number of pilots.
    wing_loading (float): Wing loading [kg/m^2].

    """

    def __init__(self):
        self.abreast_nb = 0
        self.row_nb = 0
        self.pass_nb = 0
        self.toilet_nb = 0
        self.crew_nb = 0
        self.cabin_crew_nb = 0
        self.PILOT_NB = 0
        self.wing_loading = 0


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":
    log.warning("#########################################################")
    log.warning("### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ###")
    log.warning("#####################1###################################")
