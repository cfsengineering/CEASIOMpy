"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the engine analysis.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-12-11

"""


# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np


# =============================================================================
#   CLASSES
# =============================================================================


class EngineData:
    """
    The class contains all the engines information required for the
    unconventional aircraft analysis.

    Attributes
        NE (integer): Number of Engines [-].
        en_mass (float): Single engine total mass [kg].
        max_thrust (float): Maximum Take off Thrust of a single engine [kN].
        TSFC_CRUISE (float): Thrust specific fuel consumption for cruise [1/hr].
        position (float_array): Engine position coordinates in the aircraft
                                (x, y, z) [m, m, m], if multiple engines are
                                define the array should contain 1 row each.
        EN_NAME (list): Name of each engine.
        turboprop (boolean): False if Turbofan, True if Truboprop.
        APU (boolean): True if the aircraft will have the APU (Auxiliary Power Unit).
        WING_MOUNTED (boolean): True if the engines are mounted on the front
                                main wing (WARNING not for BWB aircraft).

    """

    def __init__(self):

        self.NE = 2
        self.en_mass = 0  # | CONCORDE 3175
        self.max_thrust = 0  # | CONCORDE 170
        # | turboprop and TURBOFAN and CONCORDE
        self.TSFC_CRUISE = 0.5  # |    0.6          0.5          0.8
        # |Balance input
        self.EN_PLACEMENT = np.array([])
        self.EN_NAME = ["Engine1", "Engine2", "Engine3", "Engine4"]
        # Concorde
        # self.EN_PLACEMENT=np.array([[42.0, 4.6, 0.0], [42.0, 6.4, 0.0],\
        # [42.0, -4.6, 0.0], [42.0, -6.4, 0.0]])
        # Bwb
        # self.EN_PLACEMENT=np.array([[32.0, -3.0, 1.0],[32.0, 0, 1.0],[32.0, 3.0, 1.0]])
        # WP46RM
        # self.EN_PLACEMENT=np.array([[26.0, 4.5, 2.0],[26.0, -4.5, 2.0]])

        # The name must be char tipe.
        self.turboprop = False
        self.APU = True
        self.WING_MOUNTED = True  # |Balance input


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("########################################################")
    print("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    print("########################################################")
