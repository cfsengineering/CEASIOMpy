"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the range analysis.

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-07-08 (AJ)

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

    Source:
        * https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf

    Attributes:
        WINGLET         (int): Winglet option (0 = no winglets, 1 = normale winglets,
                                2 = high efficiency winglet for cruise).
        PILOT_NB        (int): Pilot number [-].
        CRUISE_SPEED    (float): Aircraft speed during cruise [m/s].
        LD              (float): Lift over drag coefficient [-].
        LOITER_TIME     (float): Loiter length [min]
        MASS_PILOT      (float): Pilot mass [kg].
        MASS_CABIN_CREW (float):Cabin crew member mass [kg].
        MASS_PASS       (float): Passenger mass [kg].
        TSFC_CRUISE     (float): Thrust specific fuel consumption for cruise [1/hr].
        TSFC_LOITER     (float): Thrust specific fuel consumption for Loiter [1/hr].
        RES_FUEL_PERC   (float): Unusable fuel percentage (0.01<value<0.2).
        TURBOPROP       (bool): Turboprop option.

    """

    def __init__(self):

        self.WINGLET = 1
        self.pilot_nb = 2
        self.cabin_crew_nb = np.nan
        self.CRUISE_SPEED = 272.0
        self.LD = 17               # A319 17, ATR72 15
        self.LOITER_TIME = 30.00
        self.MASS_PILOT = 102.0
        self.MASS_CABIN_CREW = 68.0
        self.MASS_PASS = 105.0
                                  # TURBOPROP and TURBOFAN and CONCORDE
        self.TSFC_CRUISE = 0.5    #    0.6         0.5          0.8
        self.TSFC_LOITER = 0.4    #    0.7         0.4          0.9
        self.RES_FUEL_PERC = 0.06

        self.TURBOPROP = False


class MassesWeights:
    """
    The class contains all the aircraft mass and weight values.

    Attributes:
         w_after_climb         (float): Airplane weight after climb [N].
         w_after_cruise        (float): Airplane weight after cruise [N].
         w_after_land          (float): Airplane weight after land [N].
         w_after_loiter        (float): Airplane weight after loiter [N].
         w_after_to            (float): Airplane weight after take off [N].
         wf_tot                (float): Airplane fuel total weight [N].
         w_al_maxfuel          (float): Airplane weight after landing,
                                        taking off with full fuel tank
                                        and no passengers [N].
         w_g                   (float): Maximum take off weight [N].
         mf_for_climb          (float): Mass of fuel required for climb [kg].
         mf_for_cruise         (float): Mass of fuel required for cruise [kg].
         mf_for_loiter         (float): Mass of fuel required for loiter [kg].
         mf_for_landing        (float): Mass of fuel required for landing [kg].
         mf_after_land         (float): Mass of fuel remained after landing [kg].
         mf_for_to             (float): Mass of fuel required for take off [kg].
         mass_fuel_maxpass     (float): Max fuel mass with max payload [kg].
         mass_fuel_max         (float): Max fuel mass allowed (evaluated) [kg].
         maximum_take_off_mass (float): Maximum take off mass [kg].
         operating_empty_mass  (float): Operating empty mass [kg].
         mass_payload          (float): Payload mass [kg].
         m_pass_middle         (float): Maximum payload mass with maximum fuel [kg].

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

    Attributes:
        crew_nb         (int): Number of total crew members.
        cabin_crew_nb   (int): Number of cabin crew members.
        pilot_nb        (int): Number of pilots.
        mass_crew       (float): Crew members total mass.
        fligth_time     (float): Appoximate fligth time [hr].
        ranges          (float_array): Array containing zero, the range at maximum paload,
                                       the range at maxium fuel and some payload, the
                                       range at maximum fuel and no payload [km].
        ranges_cru      (float_array): Similar array to the ranges one, but
                                       containing the cruise ranges [km].
        payloads        (float_array): Array containing the payload corresponding
                                       to the ranges in the ranges array.

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
