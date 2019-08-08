"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Center_of_gravity evaluation for unconventional aircraft with fuselage.
    
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

def center_of_gravity_evaluation(F_PERC, P_PERC, afg, awg, mw, ed, ui, bi):
    """ Function to evaluate the center of gravity of airplanes given the
    geometry from cpacs file and masses from weight_unc_main.py.
        
    Source: An introduction to mechanics, 2nd ed., D. Kleppner 
            and R. Kolenkow, Cambridge University Press.
        
    ARGUMENTS
    (int) F_PERC --Arg.: Percentage of the maximum amount of fuel allowed
    (int) P_PERC --Arg.: Percentage of the maximum amount of Payload allowed
    (class) afg  --Arg.: AircraftFuseGeometry class.
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
     
    max_seg_n = np.max([np.amax(afg.fuse_seg_nb), np.amax(awg.wing_seg_nb)])
    t_nb = afg.f_nb + awg.w_nb      # Number of parts not counting symmetry
    tot_nb = afg.fuse_nb + awg.wing_nb  # Number of parts counting symmetry
    segments_nb = []
    fuse_fuel_vol = 0
    pass_vol = 0
    
    for i in range(1,afg.f_nb+1):
        segments_nb.append(afg.fuse_seg_nb[i-1])
        if ui.F_FUEL[i-1]:
            fuse_fuel_vol += afg.fuse_fuel_vol[i-1]
        if np.all(afg.cabin_seg[:,i-1]) == 1:
            pass_vol += afg.fuse_vol[i-1]
        else:
            pass_vol += afg.fuse_cabin_vol[i-1]  
            
    htw = 0
    x0 = 0
    s = 0
    for i in range(1,awg.w_nb+1):
            segments_nb.append(awg.wing_seg_nb[i-1])
            if awg.wing_sym[i-1] != 0:  
                segments_nb.append(awg.wing_seg_nb[i-1])
                s += 1
            if awg.is_horiz[i-1+s]:
                if i != awg.main_wing_index:
                    htw = i
            else:
                x = np.amax(awg.wing_center_seg_point[:,i+s-1,0])
                if x > x0:
                    tw = i
                    x0 = x
                    
    mass_seg_i = np.zeros((max_seg_n,tot_nb))
    oem_vol = (awg.wing_tot_vol-awg.wing_fuel_vol)\
               + (np.sum(afg.fuse_vol)-fuse_fuel_vol)
  
    # Evaluating oem density, fuel density, passenger density
    if bi.USER_EN_PLACEMENT:
        oem_par = (mw.operating_empty_mass-mw.mass_engines) / oem_vol
        en = mw.mass_engines
    else:
        oem_par = mw.operating_empty_mass / oem_vol
        en = 0
        
    mpass_par = (mw.mass_payload*(P_PERC/100.0)) / pass_vol

    mfuel_par = (mw.mass_fuel_tot*(F_PERC/100.0))\
                 /(awg.wing_fuel_vol + fuse_fuel_vol)

    mtom = mw.operating_empty_mass + mw.mass_payload*(P_PERC/100)\
           + mw.mass_fuel_tot*(F_PERC/100) - en
    
    # Definition of the mass of each segment
    ex = False
    wg = []
    for i in range(1,afg.f_nb+1):
        if ui.F_FUEL[i-1]:  
            for j in range(1,afg.fuse_seg_nb[i-1]+1):
                mass_seg_i[j-1][i-1] = (oem_par+(mfuel_par*ui.F_FUEL[i-1]/100))\
                                        * afg.fuse_seg_vol[j-1][i-1]
        else:
            for j in range(1,afg.fuse_seg_nb[i-1]+1):
                if int(afg.cabin_seg[j-1][i-1]) == 1:
                    mass_seg_i[j-1][i-1] = (oem_par+mpass_par)\
                                            * afg.fuse_seg_vol[j-1][i-1]
                else: 
                    mass_seg_i[j-1][i-1] = oem_par * afg.fuse_seg_vol[j-1][i-1] 
    w = 0
    for i in range(afg.f_nb+1,t_nb+1):
        for j in range(1,awg.wing_seg_nb[i-1-afg.f_nb]+1):
            if awg.is_horiz[i+w-1-afg.f_nb]:
                mass_seg_i[j-1][i-1+w] = oem_par\
                    * (awg.wing_seg_vol[j-1][i-1-afg.f_nb]\
                    - awg.wing_fuel_seg_vol[j-1][i-1-afg.f_nb])\
                    + mfuel_par * (awg.wing_fuel_seg_vol[j-1][i-1-afg.f_nb])
            else:
                mass_seg_i[j-1][i-1+w] = oem_par\
                                       * awg.wing_seg_vol[j-1][i-1-afg.f_nb]
        wg.append(i-afg.f_nb)
        if awg.wing_sym[i-1-afg.f_nb] != 0:
            w += 1
            mass_seg_i[:,i-1+w]=mass_seg_i[:,i-2+w]
            wg.append(i-afg.f_nb)
            if i+w == tot_nb:
                break
    # Mass check   
    while not ex:
        if abs(round(mtom,3) - round(np.sum(mass_seg_i),3)) < 0.0001:     
            ex = True
        else:
            mass = (round(mtom,3) - round(np.sum(mass_seg_i),3))/2
            if not ed.WING_MOUNTED:
                if htw != 0:
                    a = wg.index(htw)
                else:
                    a = wg.index(tw)  
            else:
                a = wg.index(awg.main_wing_index)
            mass_seg_i[0][afg.fuse_nb+a] = mass_seg_i[0][afg.fuse_nb+a] + mass
            if awg.is_horiz[a]:
                mass_seg_i[0][afg.fuse_nb+a+1]\
                    = mass_seg_i[0][afg.fuse_nb+a+1] + mass
            else:
                mass_seg_i[0][afg.fuse_nb+a]\
                    = mass_seg_i[0][afg.fuse_nb+a] + mass           
    
    awg.wing_center_seg_point.resize(max_seg_n,awg.wing_nb,3)
    afg.fuse_center_seg_point.resize(max_seg_n,afg.fuse_nb,3)
    
    airplane_centers_segs = np.concatenate((afg.fuse_center_seg_point,\
                                            awg.wing_center_seg_point),1)
   
    # CoG evalution
    if bi.USER_EN_PLACEMENT:
        cog_enx = np.sum(ed.EN_PLACEMENT[:,0]*ed.en_mass) 
        cog_eny = np.sum(ed.EN_PLACEMENT[:,1]*ed.en_mass) 
        cog_enz = np.sum(ed.EN_PLACEMENT[:,2]*ed.en_mass) 
    else:
        cog_enx = 0.0
        cog_eny = 0.0
        cog_enz = 0.0

    center_of_gravity=[]    
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
    
    