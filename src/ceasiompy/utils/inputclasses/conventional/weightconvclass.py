"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the weight analysis.

| Author : Stefano Piccini
| Date of creation: 2018-09-27

TODO:
    * Maybe gather all parameter in one class (or one class with subclasses)

"""

# Imports


from cpacspy.cpacsfunctions import add_uid, get_value_or_default
from ceasiompy.utils.commonxpaths import (
    F_XPATH,
    GEOM_XPATH,
    MASS_CARGO_XPATH,
    TURBOPROP_XPATH,
    WB_MASS_LIMIT_XPATH,
    WB_AISLE_WIDTH_XPATH,
    WB_DOUBLE_FLOOR_XPATH,
    WB_FUSELAGE_THICK_XPATH,
    WB_MAX_FUEL_VOL_XPATH,
    WB_MAX_PAYLOAD_XPATH,
    WB_SEAT_LENGTH_XPATH,
    WB_SEAT_WIDTH_XPATH,
    WB_TOILET_LENGTH_XPATH,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class UserInputs:
    """
    The class contains all the default values for the inputs required for
    the weight analysis.

    Source:
    https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf

    Attributes:
    is_double_floor (int):  0 = no 2nd floor.
                            1 = full 2nd floor (A380),
                            2 = half 2nd floor (B747)
    pilot_nb (int):         Number of pilots[-].
    max_payload (int):      Maximum payload allowed, set 0 if equal to max passenger mass.
    max_fuel_volume (int):     Maximum fuel volume allowed [l].
    fuel_density (float) :  Fuel density [kg/m^3].
    turboprop (bool):       Set True if the engine is a turboprop.

    """

    def __init__(self):
        self.is_double_floor = 0
        self.mass_cargo = 0.0
        self.max_payload = 0
        self.max_fuel_volume = 0
        self.fuel_density = 800
        self.turboprop = False

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

        self.is_double_floor = get_value_or_default(tixi, WB_DOUBLE_FLOOR_XPATH, 0)

        description = "Desired max fuel volume [m^3] and payload mass [kg]"
        get_value_or_default(tixi, WB_MASS_LIMIT_XPATH + "/description", description)

        self.max_payload = get_value_or_default(tixi, WB_MAX_PAYLOAD_XPATH, 0)
        self.max_fuel_volume = get_value_or_default(tixi, WB_MAX_FUEL_VOL_XPATH, 0)
        self.mass_cargo = get_value_or_default(tixi, MASS_CARGO_XPATH, 0.0)
        self.fuel_density = get_value_or_default(tixi, F_XPATH + "/density", 800)
        add_uid(tixi, F_XPATH, "kerosene")

        self.turboprop = get_value_or_default(tixi, TURBOPROP_XPATH, False)

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
