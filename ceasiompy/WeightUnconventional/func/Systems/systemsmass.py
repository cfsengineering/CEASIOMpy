"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Evaluation of the mass of the unconventional aircraft systems.

    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-12-19
    Last modifiction: 2019-02-20
    
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the 
   InputClasses/Unconventional folder."""
   
   
#=============================================================================
#   FUNCTIONS
#=============================================================================

def estimate_system_mass(pass_nb, main_wing_surface, tail_wings_surface,\
                         SINGLE_HYDRAULICS, mw, ed):
    """ The function evaluates the number of crew members on board.
    
    Source : 
     - https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19770019162.pdf
     - Furnishings & Equipment from:
       https://uhra.herts.ac.uk/bitstream/handle/2299/10741/
       Aircraft_weight_estimation_in_interactive_design_process.pdf?sequence=2
    
    ARGUMENTS
    (int) pass-nb --Arg.: Passengers number [-].
    (float) main_wing_surface    --Arg.: Main wing planform area [m^2].
    (float_array) tail_wings_surface   --Arg.: Tail wings planform area [m^2].
    (boolean) SINGLE_HYDRAULICS  --Arg.: False is the aircraft will have a 
                                         multiple hydraulics system 
                                        (common for modern aircraft).
    (class) mw    --Arg.: Airgraft MassesWeight class.        
    (class) ed    --Arg.: EngineData class.
    ##======= Classes are defined in the InputClasses folder =======##
    
    RETURNS
    (float) system_mass --Arg.: Total systems mass [kg]. 
    
    """
    LB_TO_KG = 0.453592   # convert from pounds to kilograms 
    KG_TO_LB = 2.20462    # convert from kilograms to pounds
    KG_TO_GAL = 0.26      # convert from kilograms to gallons
    M2_TO_FEET2 = 10.7639 # convert from m^2 to feet^2
    
    #Prepocessing informations
    fuel = mw.mass_fuel_max*KG_TO_GAL        # Fuel in gallons
    mtom = mw.maximum_take_off_mass*KG_TO_LB # MTOM in gallons
    zfm = mw.zero_fuel_mass*LB_TO_KG
    T = ((ed.max_thrust*1000)/9.81) * KG_TO_LB # Take off thrust in lb
    s_main_wing = main_wing_surface*M2_TO_FEET2
    s_tail_wing = np.sum(tail_wings_surface)*M2_TO_FEET2
    sw = []
    s_n = []
    
    #Auxiliary power unit, pneumatic and air conditionigs
    if not ed.APU:
        sw.append(13.6*pass_nb)
        s_n.append('Pnew+Air')
    else:      
        sw.append(26.2*pass_nb**0.944)
        s_n.append('APU+Pnew+Air')
        
    #Anti-Icing weight
    s_n.append('De_ice')
    if ed.WING_MOUNTED:
        if ed.TURBOPROP:
            sw.append(0.520*s_main_wing)
        else:
            sw.append(0.238*s_main_wing)
    else:
        sw.append(0.436*s_main_wing)
        
    ##Furnishings and Equipment
    s_n.append('F&E') 
    sw.append((0.196*(zfm**0.91))) 
    
    #Instruments
    s_n.append('Instr')
    sw.append(1.875*pass_nb + 0.00714*fuel + (0.00145*T + 30)*ed.NE + 162)

    #Load and Handling
    s_n.append('Load')
    sw.append(50)
    
    #Avionics
    s_n.append('Avionics')
    sw.append(pass_nb + 370)
    
    #Electrical
    s_n.append('Electr')
    sw.append(16.2*pass_nb + 110)
    
    # Flight Controls and Hydraulics
    s_n.append('Controls')
    if SINGLE_HYDRAULICS:
        sw.append(45.0 + 0.269*(s_main_wing + 1.44 * s_tail_wing)**1.106)
    else: # Multi-hydraulics case, common on modern aircraft
        if (s_main_wing + 1.44 * s_tail_wing) <= 3000:
            sw.append(45.0 + 1.318*(s_main_wing + 1.44 * s_tail_wing))
        else:
            sw.append(18.7*(s_main_wing + 1.44 * s_tail_wing)**0.712 - 1620)
            
    # Engine Systems
    s_n.append('EngineSys')
    sw.append(133*ed.NE)
    
    # Landing gear weight evaluation
    s_n.append('LG')
    if mw.maximum_take_off_mass <= 108200:
        w_gear = 0.0302*mtom
    else:    
        w_gear = 0.0440 * mtom - 672
    sw.append(w_gear)

    systems_mass = np.sum(sw)*LB_TO_KG
    
    return(systems_mass)    
    
    
##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':   
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
    
    
