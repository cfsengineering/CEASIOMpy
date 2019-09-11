"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the
weight and balance unconventional analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

""" No inport """


#=============================================================================
#   CLASSES
#=============================================================================

class AdvancedInputs:
    """
    The class contains all the default values for the input needed for
    the weight and balance analysis.

    ATTRIBUTES
    #People
    (int) PILOT_NB           --Att.: Number of pilots.
    (int) PASS_PER_TOILET       --Att.: Number of passengers per each toilet.
    (float) MASS_PILOT       --Att.: Pilot mass  [kg].
    (float) MASS_CABIN_CREW  --Att.: Cabin crew mass  [kg].
    (float) MASS_PASS        --Att.: Passenger mass_cabin_crew  [kg].
    #Fuel
    (float) FUEL_DENSITY   --Att.: Fuel density [kg/m^3].
    (float) RES_FUEL_PERC  --Att.: % of the total fuel,
                                   unusable fuel_consumption.
    (float) FMP             --Att.: Percentage of the total fuel
                                    expected with maximum payload
                                    for turbofan aircraft.
    (float) FMP_tp          --Att.: Percentage of the total fuel
                                    expected with maximum payload
                                    for turboprop aircraft.
    #Structure
    (float) VRT_THICK       --Att.: Virtual thickness.
    (float) VRT_EXP         --Att.: Strutural mass exponential coefficient.
    (float) VRT_STR_DENSITY --Att.: Virtual structural density [kg/m^3].

    (float) VRT_THICK
    (float) FUSE_STR_DENSITY --Att.: Density of the fuselage structure [kg/m^3].
    (boolean) LOW_PASS     --Att.: Set True if the aircraft will have only
                                   business or first class seats.
    #Hydraulics
    (boolean) SINGLE_HYDRAULICS  --Att.: False is the aircraft will have a
                                         multiple hydraulics system
                                        (common for modern aircraft).
    METHODS
    Name            Description
    """

    def __init__(self):
        #People
        self.PILOT_NB = 2
        self.PASS_PER_TOILET = 50
        self.MASS_PILOT = 102.0
        self.MASS_CABIN_CREW = 68.0
        self.MASS_PASS = 105.0

        #Fuel
        self.FUEL_DENSITY = 800
        self.RES_FUEL_PERC = 0.06
        self.FPM = 80         #|80 all // 95 for the B777 or Concorde
        self.FPM_TP = 50

        #Structures
        self.VRT_THICK = 0.00014263    #|ok 0.00009 Concorde, #0.00014263 def
        self.VRT_EXP = 1.6276
        self.VRT_STR_DENSITY = 2700.0  #|ok

        #Hydraulics
        self.SINGLE_HYDRAULICS = False   #|ok


class UserInputs:
    """
    The class contains all the user input values for the input needed for
    the weight and balance analysis.

    (int) FLOORS_NB      --Att.: Number of floors.
    (float) H_LIM_CABIN  --Att.: Minimum height of the fuselage segments
                                 that should contain the cabin [m].
    (float) MASS_CARGO   --Att.: Extra cargo mass defined by the user
                                 WARNING the code does not check if the
                                 cargo fits inside the aircraft [kg].
    (float) MAX_PAYLOAD  --Att.: Massimum payload allowed by the user
                                 excluding the cargo mass [kg].
    (float) MAX_FUEL_VOL --Att.: Maximum fuel volume allowed [l].
    (int)   MAX_PASS     --Att.: Maximum numbre of passengers allowed [-].
                                 WARNING if MAX PASS and MAX_PAYLOAD are
                                 defined at the same time first the MAX_PASS
                                 limit will be taken into account and then the
                                 MAX_PAYLOAD limit.
    (float) PASS_BASE_DENSITY  --Att.: Base passengers density [pass/m^2].
    (float) LD           --Att.: Lift over drag coefficient [-].
    (float) wing_loading --Att.: Ratio between the maximum take off mass
                                 and the wing area [kg/m^2].
    (float) CRUISE_SPEED --Att.: Aircraft cruise speed [m/s]
    (float) FUEL_ON_CABIN --Att.: Amount of fuel allowed inside the central
                                  wing area, near the cabin for the blended
                                  wing body confiuration, expressed as
                                 percentage of the free volume.
    (array) F_FUEL     --Att.: Define if the fuselage can contain fuel.
                               If 0 the code will try to add passengers
                               inside. The order of the values correspond to the
                               order of the element in the CPACS file.
    (boolean) USER_ENGINES --Att.: Set True if the user defines the
                                  the engine characteristics inside the CPACS
                                  file.
    METHODS
    Name            Description
    """

    def __init__(self):
       #Cabin
       self.FLOORS_NB = 1
       self.H_LIM_CABIN = 2.3 # Concorde 1.5, Conventional 2.3

       # Payload & fuel
       self.MASS_CARGO = 0.0
       self.MAX_PAYLOAD = 0.0
       self.MAX_FUEL_VOL = 0.0
       self.MAX_PASS = 0
       self.PASS_BASE_DENSITY = 1.66 #| Concorde 1.16, B777 1.66, ATR72 1.39, BWB 1.69

       #Aerodynamics and Flight
       self.LD = 17        #|
       self.wing_loading = 600.0      #|not save into the cpacs file
       self.CRUISE_SPEED = 272.0      #|600 272 141 190

       #|Not in the cpacs
       self.F_FUEL = [0.0, 0.0]  # Value must be less than 80.
       self.FUEL_ON_CABIN = 0    # Value must be less than 80,
                                 # WARNING (only for bwb analysis).
       self.USER_ENGINES = False


class MassesWeights:
    """
    The class contains all the aircraft mass and weight value relative to the
    weight unconventional analysis.

    ATTRIBUTES
    (float) mass_fuse_fuel  --Att.: Mass of fuel inside the fuselage [kg].
    (float) mass_wing_fuel  --Att.: Mass of fuel inside the main wing [kg].
    (float) mass_fuel_max   --Att.: Total fuel mass [kg].
    (float) mass_systems    --Att.: Systems mass [kg].
    (float) mass_structure  --Att.: Mass of the aircraft struture [kg].
    (float) mass_engines    --Att.: Engines total mass [kg].
    (float) mass_fuel_maxpass     --Att.: Max fuel mass with max payload [kg].
    (float) maximum_take_off_mass --Att.: Maximum take off mass [kg].
    (float) operating_empty_mass  --Att.: Operating empty mass [kg].
    (float) mass_payload    --Att.: Payload mass [kg].
    (float) mass_crew       --Att.: Crew members total mass [kg].
    (float) mass_people     --Att.: Mass of people inside the aircraft [kg].
    (float) mass_pass      --Att.: Mass of passengers inside the aircraft [kg].
    (float) zero_fuel_mass  --Att.: Zero fuel mass [kg].

    METHODS
    Name            Description
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

    ATTRIBUTES
    (int) pass_nb        --Att.: Number of passengers.
    (int) toilet_nb      --Att.: Numbre of toilets.
    (int) crew_nb        --Att.: Number of total crew members.
    (int) cabin_crew_nb  --Att.: Number of cabin crew members.
    (float) wing_loading --Att.: Final wing loading estimated [kg/m^2].
    METHODS
    Name            Description
    """

    def __init__(self):
        self.pass_nb = 0
        self.toilet_nb = 0
        self.crew_nb = 0
        self.cabin_crew_nb = 0
        self.wing_loading = 0


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
