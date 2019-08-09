"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the engine analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-11
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np


#=============================================================================
#   CLASSES
#=============================================================================

class EngineData():
    """
    The class contains all the engines information required for the
    unconventional aircraft analysis.

    ATTRIBUTES
    (integer) NE        --Att.: Number of Engines [-].

    (float) en_mass     --Att.: Single engine total mass [kg].
    (float) max_thrust
    --Att.: Maximum Take off Thrust
                                 of a single engine [kN].
    (float) TSFC_CRUISE   --Att.: Thrust specific fuel consumption
                                  for cruise [1/hr].
    (float_array) position --Att.: Engine position coordinates in the aircraft
                                   (x, y, z) [m, m, m], if multiple engines are
                                   define the array should contain 1 row each.
    (cahr) EN_NAME   --Att.: Name of each engine.
    (boolean) TURBOPROP    --Att.: False if Turbofan, True if Truboprop.
    (boolean) APU          --Att.: True if the aircraft will have the APU
                                   (Auxiliary Power Unit).
    (boolean) WING_MOUNTED --Att.: True if the engines are mounted on the front
                                   main wing (WARNING not for BWB aircraft).
    METHODS
    Name            Description
    """

    def __init__(self):
        self.NE = 2

        self.en_mass = 0          #| CONCORDE 3175
        self.max_thrust = 0       #| CONCORDE 170
                                  #| TURBOPROP and TURBOFAN and CONCORDE
        self.TSFC_CRUISE = 0.5    #|    0.6          0.5          0.8
        #|Balance input
        self.EN_PLACEMENT=np.array([])
        self.EN_NAME = ['Engine1', 'Engine2', 'Engine3', 'Engine4']
        #Concorde
        #self.EN_PLACEMENT=np.array([[42.0, 4.6, 0.0], [42.0, 6.4, 0.0],\
                                    #[42.0, -4.6, 0.0], [42.0, -6.4, 0.0]])
        #Bwb
        #self.EN_PLACEMENT=np.array([[32.0, -3.0, 1.0],[32.0, 0, 1.0],[32.0, 3.0, 1.0]])
        #WP46RM
        #self.EN_PLACEMENT=np.array([[26.0, 4.5, 2.0],[26.0, -4.5, 2.0]])

        # The name must be char tipe.
        self.TURBOPROP =  False
        self.APU = True
        self.WING_MOUNTED = True  #|Balance input


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')


