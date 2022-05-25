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
import numpy as np
from ceasiompy.utils.commonxpath import (
    F_XPATH,
    GEOM_XPATH,
    MASSBREAKDOWN_XPATH,
    ML_XPATH,
    PROP_XPATH,
    WB_AISLE_WIDTH_XPATH,
    WB_FUSELAGE_THICK_XPATH,
    WB_SEAT_LENGTH_XPATH,
    WB_SEAT_WIDTH_XPATH,
    WB_TOILET_LENGTH_XPATH,
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
    MAX_PAYLOAD (int):      Maximum payload allowed, set 0 if equal to max passenger mass.
    MAX_FUEL_VOL (int):     Maximum fuel volume allowed [l].
    FUEL_DENSITY (float) :  Fuel density [kg/m^3].
    TURBOPROP (bool):       Set True if the engine is a turboprop.

    """

    def __init__(self):
        self.IS_DOUBLE_FLOOR = 0
        self.MASS_CARGO = 0.0
        self.MAX_PAYLOAD = 0
        self.MAX_FUEL_VOL = 0
        self.FUEL_DENSITY = 800
        self.TURBOPROP = False

    def get_user_inputs(self, cpacs):
        """Get user input from the CPACS file

        The function 'get_user_inputs' extracts from the CPACS file the required
        input data, the code will use the default value when they are missing.

        Args:
            cpacs_path (str): Path to CPACS file

        """

        tixi = cpacs.tixi

        description = "User geometry input"
        get_value_or_default(tixi, GEOM_XPATH + "/description", description)

        self.IS_DOUBLE_FLOOR = get_value_or_default(tixi, GEOM_XPATH + "/isDoubleFloor", 0)

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

        return cpacs


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

    def __init__(self, ag):

        fuse_length = round(ag.fuse_length[0], 3)

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

        # [m] Common space dimension in longitudinal direction.
        # --- Value to be evaluated ---
        self.cabin_length = 0
        self.cabin_width = 0
        self.cabin_area = 0

        # Value from the aircraft geometry (TODO: could be simplified)
        self.nose_length = round(ag.fuse_nose_length[0], 3)
        self.tail_length = round(ag.fuse_tail_length[0], 3)
        self.cabin_length = round(ag.fuse_cabin_length[0], 3)

    def get_inside_dim(self, cpacs):
        """Get user input from the CPACS file

        The function 'get_inside_dim' extracts from the CPACS file the required
        aircraft inside dimension, the code will use the default value when they are
        missing.

        Args:
            cpacs (obj): Path to CPACS object

        """

        tixi = cpacs.tixi

        # Get inside dimension from the CPACS file if exit
        self.seat_width = get_value_or_default(tixi, WB_SEAT_WIDTH_XPATH, 0.525)
        self.seat_length = get_value_or_default(tixi, WB_SEAT_LENGTH_XPATH, self.seat_length)
        self.aisle_width = get_value_or_default(tixi, WB_AISLE_WIDTH_XPATH, 0.42)
        self.fuse_thick = get_value_or_default(tixi, WB_FUSELAGE_THICK_XPATH, 6.63)
        self.toilet_length = get_value_or_default(tixi, WB_TOILET_LENGTH_XPATH, self.toilet_length)


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
    toilet_nb (int): Number of toilets.
    crew_nb (int): Number of total crew members.
    cabin_crew_nb (int): Number of cabin crew members.
    wing_loading (float): Wing loading [kg/m^2].

    """

    def __init__(self):
        self.abreast_nb = 0
        self.row_nb = 0
        self.pass_nb = 0
        self.toilet_nb = 0
        self.crew_nb = 0
        self.cabin_crew_nb = 0
        self.wing_loading = 0


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":
    log.warning("#########################################################")
    log.warning("### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ###")
    log.warning("#####################1###################################")
