"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Center_of_gravity evaluation for unconventional aircraft without fuselage.
    
    Function to evaluate the Center of Gravity of the aircraft.
    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-10-12
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

"""All classes are defined inside the classes and into 
   the InputClasses/Unconventional folder."""      
   
   
#=============================================================================
#   FUNCTIONS
#=============================================================================

def center_of_gravity_evaluation_bwb(F_PERC, P_PERC, awg, mw, ed, ui, bi):
    """ The function evaluates the center of gravity of airplanes given the
        geometry from cpacs file and masses from weight_unc_main.py.
        
    Source: An introduction to mechanics, 2nd ed., D. Kleppner 
            and R. Kolenkow, Cambridge University Press.
        
    ARGUMENTS
    (int) F_PERC --Arg.: Percentage of the maximum amount of fuel allowed
    (int) P_PERC --Arg.: Percentage of the maximum amount of Payload allowed

    (class) awg  --Arg.: AircraftWingGeometry class. 
    (class) mw   --Arg.: MassesWeights class.
    (class) ed   --Arg.: EngineData class.
    (class) ui   --Arg.: UserInputs class.
    (class) bi   --Arg.: UserInputs class.
    ##======= Classes are defined in the InputClasses folder =======##
                           
    RETURN
    (float_array) center_of_gravity --Out.: x,y,z coordinates of the CoG.
    (float_array) mass_seg_i        --Out.: mass of each segment of each 
                                           component of the aircraft.
    (float_array) airplane_centers_segs --Out.: point at the center of
                                                each segment of the
                                                aircraft.   
    """ 
    max_seg_n = np.amax(awg.wing_seg_nb)
    
    # Volumes
    oem_vol = np.sum(awg.wing_vol)- awg.cabin_vol - awg.fuel_vol_tot 
    op = (awg.fuse_vol - awg.cabin_vol - awg.fuse_fuel_vol)/awg.fuse_vol
    fp = awg.fuse_fuel_vol/awg.fuse_vol
    pp = awg.cabin_vol/awg.fuse_vol
    
    # Evaluating oem density, fuel density, passenger density
    if bi.USER_EN_PLACEMENT:
        oem_par = (mw.operating_empty_mass-mw.mass_engines) / oem_vol
        en = mw.mass_engines
    else:
        oem_par = mw.operating_empty_mass / oem_vol
        en = 0
        
    mpass_par = (mw.mass_payload*(P_PERC/100)) / awg.cabin_vol
    mfuel_par = (mw.mass_fuel_tot*(F_PERC/100)) / awg.fuel_vol_tot   
    mtom = mw.operating_empty_mass + mw.mass_payload*(P_PERC/100)\
           + mw.mass_fuel_tot*(F_PERC/100) - en

    # Definition of the mass of each segment
    mass_seg_i = np.zeros((max_seg_n,awg.wing_nb))
    ex = False
    wg = []
    w = 0
    for i in range(1,awg.w_nb+1):
        for j in range(1,awg.wing_seg_nb[i-1]+1):
            if awg.is_horiz[i+w-1] is True and\
               awg.wing_center_seg_point[j-1,i+w-1,1] <= awg.y_max_cabin:
                o = oem_par * (awg.wing_seg_vol[j-1][i-1]*op)
                f = mfuel_par * (awg.wing_seg_vol[j-1][i-1]*fp)
                p = mpass_par * (awg.wing_seg_vol[j-1][i-1]*pp)
                mass_seg_i[j-1][i-1+w] = o + f + p 
            elif awg.is_horiz[i+w-1] is True and\
                 awg.wing_center_seg_point[j-1,i+w-1,1] > awg.y_max_cabin:
                mass_seg_i[j-1][i-1+w] = (oem_par + mfuel_par)\
                                         * (0.5*awg.wing_seg_vol[j-1][i-1])
            else:
                mass_seg_i[j-1][i-1+w] = oem_par * awg.wing_seg_vol[j-1][i-1]
        wg.append(i)
        if awg.wing_sym[i-1] != 0:
            w += 1
            mass_seg_i[:,i-1+w]=mass_seg_i[:,i-2+w]
            wg.append(i)
            if i+w == awg.wing_nb:
                break
    
    # Mass check   
    while not ex:
        if abs(round(mtom,3) - round(np.sum(mass_seg_i),3)) < 0.0001:     
            ex = True
        else:
            mass = (round(mtom,3) - round(np.sum(mass_seg_i),3))/2
            a = wg.index(awg.main_wing_index)
            mass /= (awg.wing_seg_nb[a]*2)
            mass_seg_i[:][a:a+1] +=  mass         
    
    awg.wing_center_seg_point.resize(max_seg_n,awg.wing_nb,3)
    airplane_centers_segs = awg.wing_center_seg_point
  
    # CoG evalution
    if bi.USER_EN_PLACEMENT:
        cog_enx = np.sum(ed.EN_PLACEMENT[:,0]*ed.en_mass) 
        cog_eny = np.sum(ed.EN_PLACEMENT[:,1]*ed.en_mass) 
        cog_enz = np.sum(ed.EN_PLACEMENT[:,2]*ed.en_mass) 
    else:
        cog_enx = 0.0
        cog_eny = 0.0
        cog_enz = 0.0

    center_of_gravity = []  
    center_of_gravity.append(round((np.sum(airplane_centers_segs[:,:,0]\
                             *mass_seg_i) + cog_enx) / mtom,3))
    center_of_gravity.append(round((np.sum(airplane_centers_segs[:,:,1]\
                             *mass_seg_i) + cog_eny) / mtom,3))
    center_of_gravity.append(round((np.sum(airplane_centers_segs[:,:,2]\
                             *mass_seg_i) + cog_enz) / mtom,3))

    for i in range(1,4):
        if abs(center_of_gravity[i-1]) < 10**(-5):
            center_of_gravity[i-1] = 0.0
    
    return(center_of_gravity, mass_seg_i, airplane_centers_segs)
    
#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
    
    