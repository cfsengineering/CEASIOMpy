"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the weight analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

""" No Inports Required """


#=============================================================================
#   CLASSES
#=============================================================================

class UserInputs:
    """
    The class contains all the default values for the inputs required for
    the weight analysis.

    Source:
    https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf

    ATTRIBUTES
    (int) IS_DOUBLE_FLOOR  --Att.: 1 = full 2nd floor (A380),
                                   2 = half 2nd floor (B747),
                                   0 = no 2nd floor.
    (INT) pilot_nb         --Att.: Number of pilots[-].
    (int) MASS_PILOT       --Att.: Pilot mass [kg] .
    (int) MASS_CABIN_CREW  --Att.: Cabin crew mass[kg].
    (int) MASS_PASS        --Att.: Passenger mass_cabin_crew [kg].
    (int) MAX_PAYLOAD      --Att.: Maximum payload allowed,
                                   set 0 if equal to max passenger mass.
    (int) MAX_FUEL_VOL     --Att.: Maximum fuel volume allowed [l].
    (int) PASS_PER_TOILET  --Att.: Min 1 toilette per 50 passenger.

    (float) FUEL_DENSITY    --Att.: Fuel density [kg/m^3].
    (float) RES_FUEL_PERC   --Att.: % of the total fuel,
                                   unusable fuel_consumption.
    (char) TURBOPROP       --Att.: Set True if the engine is a turboprop.

    METHODS
    Name            Description
    """

    def __init__(self):
        self.IS_DOUBLE_FLOOR=2
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


class InsideDimensions:
    """
    The class contains all the dimensions of the inside structure
    of the aircraft.

    ATTRIBUTES
    (float) seat_length   --Att.: Seats length [m].
    (float) seat_width    --Att.: Seats width [m].
    (float) aisle_width   --Att.: Aisles width [m].
    (float) nose_length   --Att.: Nose length [m].
    (float) tail_length   --Att.: Tail length [m].
    (float) fuse_thick    --Att.: Fuselage thickness, % of fuselage width [-]
    (float) toilet_length    --Att.: Common space length [m].

    (float) nose_length   --Att.: Length of the aircraft nose [m].
    (float) tail_length   --Att.: Length of the aircraft tail [m].
    (float) cabin_length  --Att.: Length of the aircraft cabin [m].
    (float) cabin_width   --Att.: Width of the aircraft cabin [m].
    (float) cabin_area    --Att.: Area of the aircraft cabin [m^2].

    METHODS
    Name            Description
    """


    def __init__(self, fuse_length, fuse_width, cpacs):

        if fuse_length < 15.00:
            self.seat_length = 1.4
        else:
           self.seat_length = 0.74

        self.seat_width  =  0.525
        self.aisle_width  =  0.42
        self.fuse_thick = 6.63

        if not cpacs:
            self.nose_length = 1.3 * fuse_width
            self.tail_length = 1.5 * fuse_width
            self.cabin_length = fuse_length - self.nose_length\
                                - self.tail_length
        else:
            self.nose_length = 0
            self.tail_length = 0

        #[m] Adding common space in relation with airplane dimensions.
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

class MassesWeights:
    """
    The class contains all the aircraft mass and weight value relative to the
    weight analysis.

    ATTRIBUTES
    (float)  mass_fuel_maxpass --Att.: Max fuel mass with max payload [kg].
    (float)  mass_fuel_mass    --Att.: Max fuel mass allowed (evaluated) [kg].
    (float)  maximum_take_off_mass --Att.: Maximum take off mass [kg].
    (float)  operating_empty_mass  --Att.: Operating empty mass [kg].
    (float)  mass_payload   --Att.: Payload mass [kg].
    (float)  MAX_FUEL_MASS  --Att.: Maximum fuel mass allowed (chosen) [kg].
    (float)  MAX_PAYLOAD    --Att.: Maximum payload mass allowed [kg].
    (float)  mass_people    --Att.: Mass of people inside the aircraft [kg].
    (float)  mass_cargo     --Att.: Extra possible payload [kg].
    (float)  zero_fuel_mass --Att.: Zero fuel mass [kg].
    (float) mass_crew    --Att.: Crew members total mass [kg].

    METHODS
    Name            Description
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

    ATTRIBUTES
    (int) abreast_nb     --Att.: Number of abreasts.
    (int) row_nb         --Att.: Number of rows.
    (int) pass_nb        --Att.: Number of passengers.
    (int) toilet_nb         --Att.: Numbre of toilets.
    (int) crew_nb        --Att.: Number of total crew members.
    (int) cabin_crew_nb  --Att.: Number of cabin crew members.
    (int) PILOT_NB       --Att.: Number of pilots.
    (float) wing_loading --Att.: Wing loading [kg/m^2].

    METHODS
    Name            Description
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


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ###')
    log.warning('#####################1###################################')
