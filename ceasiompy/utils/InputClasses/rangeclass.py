"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the range analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-01-25
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np


#=============================================================================
#   CLASSES
#=============================================================================

class RangeInputs:
    """
    The class contains all the default values for the inputs required for
    the range analysis.

    ATTRIBUTES
    (int) WINGLET         --Att.: Winglet option (0 = no winglets, 1 = normale
                                  winglets, 2 = high efficiency
                                  winglet for cruise).
    (int) PILOT_NB        --Att.: Pilot number [-].
    (float) CRUISE_SPEED  --Att.: Aircraft speed during cruise [m/s].
    (float) LD            --Att.: Lift over drag coefficient [-].
    (float) LOITER_TIME   --Att.: Loiter length [min]
    (float) MASS_PILOT      --Att.: Pilot mass [kg].
    (float) MASS_CABIN_CREW --Att.: Cabin crew member mass [kg].
    (float) MASS_PASS       --Att.: Passenger mass [kg].
    (float) TSFC_CRUISE   --Att.: Thrust specific fuel consumption
                                  for cruise [1/hr].
    (float) TSFC_LOITER   --Att.: Thrust specific fuel consumption
                                  for Loiter [1/hr].
    (float) RES_FUEL_PERC --Att.: Unusable fuel percentage (0.01<value<0.2).
    (boolean) TURBOPROP      --Att.: Turboprop option ('True', 'False').

    METHODS
    Name            Description
    """

    def __init__(self):
        self.WINGLET = 1
        self.pilot_nb = 2
        self.cabin_crew_nb = np.nan

        self.CRUISE_SPEED = 272.0  # 141 190 272
        self.LD = 17               # A319 17, ATR72 15
        self.LOITER_TIME = 30.00   # Loiter length [min]
    # source:
    # https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf
        self.MASS_PILOT = 102.0
        self.MASS_CABIN_CREW = 68.0
        self.MASS_PASS = 105.0
                                  # TURBOPROP and TURBOFAN and CONCORDE
        self.TSFC_CRUISE = 0.5    #    0.6         0.5          0.8
        self.TSFC_LOITER = 0.4    #    0.7         0.4          0.9
        self.RES_FUEL_PERC = 0.06

    # Char
        self.TURBOPROP = False


class MassesWeights:
    """
    The class contains all the aircraft mass and weight values.

    ATTRIBUTES
    (float)  w_after_climb  -- Att.: Airplane weight after climb [N].
    (float)  w_after_cruise -- Att.: Airplane weight after cruise [N].
    (float)  w_after_land   -- Att.: Airplane weight after land [N].
    (float)  w_after_loiter -- Att.: Airplane weight after loiter [N].
    (float)  w_after_to     -- Att.: Airplane weight after take off [N].
    (float)  wf_tot         -- Att.: Airplane fuel total weight [N].
    (float)  w_al_maxfuel   -- Att.: Airplane weight after landing,
                                     taking off with full fuel tank
                                     and no passengers [N].
    (float)  w_g            -- Att.: Maximum take off weight [N].
    (float)  mf_for_climb   -- Att.: Mass of fuel required for climb [kg].
    (float)  mf_for_cruise  -- Att.: Mass of fuel required for cruise [kg].
    (float)  mf_for_loiter  -- Att.: Mass of fuel required for loiter [kg].
    (float)  mf_for_landing -- Att.: Mass of fuel required for landing [kg].
    (float)  mf_after_land  -- Att.: Mass of fuel remained after landing [kg].
    (float)  mf_for_to      -- Att.: Mass of fuel required for take off [kg].
    (float)  mass_fuel_maxpass --Att.: Max fuel mass with max payload [kg].
    (float)  mass_fuel_max  --Att.: Max fuel mass allowed (evaluated) [kg].
    (float)  maximum_take_off_mass --Att.: Maximum take off mass [kg].
    (float)  operating_empty_mass  --Att.: Operating empty mass [kg].
    (float)  mass_payload   --Att.: Payload mass [kg].
    (float)  m_pass_middle  --Att.: Maximum payload mass with
                                    maximum fuel [kg].

    METHODS
    Name            Description
    """

    def __init__(self):
        self.w_after_climb = 0    #Updated with the range analysis
        self.w_after_cruise = 0   #Updated with the range analysis
        self.w_after_land = 0     #Updated with the range analysis
        self.w_after_loiter = 0   #Updated with the range analysis
        self.w_after_to = 0       #Updated with the range analysis
        self.wf_tot = 0           #Updated with the range analysis
        self.w_al_maxfuel = 0     #Updated with the range analysis
        self.w_g = 0              #Updated with the range analysis
        self.mf_for_climb = 0     #Updated with the range analysis
        self.mf_for_cruise = 0    #Updated with the range analysis
        self.mf_for_landing = 0   #Updated with the range analysis
        self.mf_after_land = 0    #Updated with the range analysis
        self.mf_for_to = 0        #Updated with the range analysis
        self.mf_for_loiter = 0    #Updated with the range analysis
        self.mass_fuel_maxpass = np.nan       # To get from CPACS
        self.mass_fuel_max = np.nan           # To get from CPACS
        self.maximum_take_off_mass = np.nan   # To get from CPACS
        self.operating_empty_mass = np.nan    # To get from CPACS
        self.mass_payload = np.nan            # To get from CPACS
        self.m_pass_middle = 0    #Updated with the range analysis


class RangeOutput:
    """
    the class contains all the output values of the range analysis.

    ATTRIBUTES
    (int) crew_nb        --Att.: Number of total crew members.
    (int) cabin_crew_nb  --Att.: Number of cabin crew members.
    (int) pilot_nb       --Att.: Number of pilots.
    (float) mass_crew    --Att.: Crew members total mass.
    (float) fligth_time  --Att.: Appoximate fligth time [hr].
    (float_array) ranges --Att.: Array containing zero, the range at
                                 maximum paload, the range at maxium fuel
                                 and some payload, the range at maximum fuel
                                 and no payload [km].
    (float_array) ranges_cru --Att.: Similar array to the ranges one, but
                                     containing the cruise ranges [km].
    (float_array) payloads  --Att.: Array containing the payload corresponding
                                    to the ranges in the ranges array.

    METHODS
    Name            Description
    """

    def __init__(self):
        self.crew_nb = 0
        self.cabin_crew_nb = 0
        self.pilot_nb = 0
        self.mass_crew = 0
        self.flight_time = 0
        self.ranges = []
        self.ranges_cru = []
        self.payloads = []


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN Range_main.py ####')
    log.warning('###########################################################')
