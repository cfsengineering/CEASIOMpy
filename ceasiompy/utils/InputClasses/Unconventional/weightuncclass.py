"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the
weight and balance unconventional analysis.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

TODO:

    * Simplify the classes and harmonise with inputs...

"""


# =============================================================================
#   IMPORTS
# =============================================================================

""" No inport """


# =============================================================================
#   CLASSES
# =============================================================================


class AdvancedInputs:
    """
    The class contains all the default values for the input needed for
    the weight and balance analysis.

    Attributes:

        #People
        PILOT_NB (int): Number of pilots.
        PASS_PER_TOILET (int): Number of passengers per each toilet.
        MASS_PILOT (float): Pilot mass  [kg].
        MASS_CABIN_CREW (float): Cabin crew mass  [kg].
        MASS_PASS (float): Passenger mass_cabin_crew  [kg].
        #Fuel
        FUEL_DENSITY (float): Fuel density [kg/m^3].
        RES_FUEL_PERC (float): % of the total fuel, unusable fuel_consumption.
        FMP (float): Percentage of the total fuel expected with maximum payload
                     for turbofan aircraft.
        FMP_tp (float): Percentage of the total fuel expected with maximum
                        payload for turboprop aircraft.
        #Structure
        VRT_THICK (float): Virtual thickness.
        VRT_EXP (float): Strutural mass exponential coefficient.
        VRT_STR_DENSITY (float): Virtual structural density [kg/m^3].
        FUSE_STR_DENSITY (float): Density of the fuselage structure [kg/m^3].
        LOW_PASS (boolean): Set True if the aircraft will have only business or
                            first class seats.
        #Hydraulics
        SINGLE_HYDRAULICS (boolean): False is the aircraft will have a multiple
                                     hydraulics system (common for modern aircraft).

    """

    def __init__(self):
        # People
        self.PILOT_NB = 2
        self.PASS_PER_TOILET = 50
        self.MASS_PILOT = 102.0
        self.MASS_CABIN_CREW = 68.0
        self.MASS_PASS = 105.0

        # Fuel
        self.FUEL_DENSITY = 800
        self.RES_FUEL_PERC = 0.06
        self.FPM = 80  # |80 all // 95 for the B777 or Concorde
        self.FPM_TP = 50

        # Structures
        self.VRT_THICK = 0.00014263  # |ok 0.00009 Concorde, #0.00014263 def
        self.VRT_EXP = 1.6276
        self.VRT_STR_DENSITY = 2700.0  # |ok

        # Hydraulics
        self.SINGLE_HYDRAULICS = False  # |ok


class UserInputs:
    """
    The class contains all the user input values for the input needed for
    the weight and balance analysis.

    Attributes:

        FLOORS_NB (int): Number of floors.
        H_LIM_CABIN (float): Minimum height of the fuselage segments that should
                             contain the cabin [m].
        MASS_CARGO (float): Extra cargo mass defined by the user WARNING the
                            code does not check if the cargo fits inside the
                            aircraft [kg].
        MAX_PAYLOAD (float): Massimum payload allowed by the user excluding the
                             cargo mass [kg].
        MAX_FUEL_VOL (float): Maximum fuel volume allowed [l].
        MAX_PASS (int): Maximum numbre of passengers allowed [-]. WARNING if
                        MAX PASS and MAX_PAYLOAD are defined at the same time
                        first the MAX_PASS limit will be taken into account
                        and then the MAX_PAYLOAD limit.
        PASS_BASE_DENSITY (float): Base passengers density [pass/m^2].
        LD (float): Lift over drag coefficient [-].
        wing_loading (float): Ratio between the maximum take off mass and the
                              wing area [kg/m^2].
        CRUISE_SPEED (float): Aircraft cruise speed [m/s]
        FUEL_ON_CABIN (float): Amount of fuel allowed inside the central wing
                               area, near the cabin for the blended wing body
                               confiuration, expressed as percentage of the free volume.
        F_FUEL (array): Define if the fuselage can contain fuel. If 0 the code
                        will try to add passengers inside. The order of the
                        values correspond to the order of the element in the CPACS file.
        USER_ENGINES (boolean): Set True if the user defines the the engine
                                characteristics inside the CPACS file.

    """

    def __init__(self):
        # Cabin
        self.FLOORS_NB = 1
        self.H_LIM_CABIN = 2.3  # Concorde 1.5, Conventional 2.3

        # Payload & fuel
        self.MASS_CARGO = 0.0
        self.MAX_PAYLOAD = 0.0
        self.MAX_FUEL_VOL = 0.0
        self.MAX_PASS = 0
        self.PASS_BASE_DENSITY = 1.66  # | Concorde 1.16, B777 1.66, ATR72 1.39, BWB 1.69

        # Aerodynamics and Flight
        self.LD = 17  # |
        self.wing_loading = 600.0  # |not save into the cpacs file
        self.CRUISE_SPEED = 272.0  # |600 272 141 190

        # |Not in the cpacs
        self.F_FUEL = [0.0, 0.0]  # Value must be less than 80.
        self.FUEL_ON_CABIN = 0  # Value must be less than 80,
        # WARNING (only for bwb analysis).
        self.USER_ENGINES = False


class MassesWeights:
    """
    The class contains all the aircraft mass and weight value relative to the
    weight unconventional analysis.

    Attributes:
        mass_fuse_fuel        (float): Mass of fuel inside the fuselage [kg].
        mass_wing_fuel        (float): Mass of fuel inside the main wing [kg].
        mass_fuel_max         (float): Total fuel mass [kg].
        mass_systems          (float): Systems mass [kg].
        mass_structure        (float): Mass of the aircraft struture [kg].
        mass_engines          (float): Engines total mass [kg].
        mass_fuel_maxpass     (float): Max fuel mass with max payload [kg].
        maximum_take_off_mass (float): Maximum take off mass [kg].
        operating_empty_mass  (float): Operating empty mass [kg].
        mass_payload          (float): Payload mass [kg].
        mass_crew             (float): Crew members total mass [kg].
        mass_people           (float): Mass of people inside the aircraft [kg].
        mass_pass             (float): Mass of passengers inside the aircraft [kg].
        zero_fuel_mass        (float): Zero fuel mass [kg].


    """

    def __init__(self):
        self.mass_fuse_fuel = 0
        self.mass_wing_fuel = 0
        self.mass_systems = 0
        self.mass_structure = 0
        self.mass_fuel_max = 0
        self.mass_engines = 0
        self.mass_fuel_maxpass = 0
        self.maximum_take_off_mass = 0
        self.operating_empty_mass = 0
        self.mass_payload = 0
        self.mass_crew = 0
        self.mass_people = 0
        self.mass_pass = 0
        self.zero_fuel_mass = 0


class WeightOutput:
    """
    The class contains some of the output value of the weight analysis.

    Attributes
        pass_nb       (int): Number of passengers.
        toilet_nb     (int): Numbre of toilets.
        crew_nb       (int): Number of total crew members.
        cabin_crew_nb (int): Number of cabin crew members.
        wing_loading (float): Final wing loading estimated [kg/m^2].

    """

    def __init__(self):
        self.pass_nb = 0
        self.toilet_nb = 0
        self.crew_nb = 0
        self.cabin_crew_nb = 0
        self.wing_loading = 0


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("########################################################")
    print("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    print("########################################################")
