"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    The script contains the user inputs required for the
    balance unconventional analysis.

    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-09-27
    Last modifiction: 2019-02-20

"""
#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np


#=============================================================================
#   CLASSES
#=============================================================================       

class BalanceInputs:
    """
    The class contains all the  input from user needed
    for the balance analysis.

    ATTRIBUTES
    (int) F_PERC      --Att.: Fuel percentage for CoG and MoI evaluation
                              to  define only if USER_CASE = True.
    (int) P_PERC      --Att.: Payload percentage for CoG and MoI evaluation
                              to  define only if USER_CASE = True.
    (float) WPP          --Att.: Number of points to subdivide the 
                                 wing upper or lower profile [-]. 
    (float) SPACING_WING --Att.: Spacing of nodes for the wing along the span
                                 direction [m].
    (float) SPACING_FUSE --Att.: Spacing of nodes for the fuselage along the
                                 radial, circumferencial and 
                                 longitudial directions [m].
    (boolean) USER_CASE  --Att.: Set True to e able to evaluate the CoG
                                 and the MoI with a chosen percentage of
                                 fuel mass (F_PERC) and payload 
                                 percentage (P_PERC).      
    (boolean) USER_EN_PLACEMENT --Att.: Set True if the user defines the
                                  the engine position inside the CPACS 
                                  file.
    METHODS 
    Name            Description
    """

    def __init__(self):
        self.F_PERC = 0
        self.P_PERC = 0
        self.WPP = 30.0
        self.SPACING_WING = 0.05
        self.SPACING_FUSE = 0.05
        self.USER_CASE = False
        self.USER_EN_PLACEMENT = False
        
        
#============================================================================= 

class MassesWeights:
    """
    The class contains all the aircraft mass and weight value needed
    for the unconventional balance analysis.

    ATTRIBUTES
    (float) mass_fuel_maxpass --Att.: Max fuel mass with max payload [kg].
    (float) mass_fuel_mass    --Att.: Max fuel mass allowed (evaluated) [kg].
    (float) maximum_take_off_mass  --Att.: Maximum take off mass [kg].
    (float) operating_empty_mass   --Att.: Operating empty mass [kg].
    (float) mass_payload   --Att.: Payload mass [kg].
    (float) mass_engines    --Att.: Engines total mass [kg].
   
    METHODS 
    Name            Description
    """
    
    def __init__(self):     
        self.mass_fuel_maxpass = np.nan
        self.mass_fuel_tot = np.nan
        self.maximum_take_off_mass = np.nan
        self.operating_empty_mass = np.nan
        self.mass_payload = np.nan 
        self.mass_engines = 0


#============================================================================= 

class BalanceOutputs:
    """
    The class contains all the output value of the unconventional
    Balance analysis.
    
    ATTRIBUTES
    ======= Moment of inertia estimated with the lumped masses method =======                  
    (float) Ixx_lump --Att.: Roll moment at maximum take off mass 
    (float) Iyy_lump --Att.: Pitch moment at maximum take off mass
    (float) Izz_lump --Att.: Yaw moment at maximum take off mass
    (float) Ixy_lump --Att.: xy moment at maximum take off mass 
    (float) Iyz_lump --Att.: yz moment at maximum take off mass
    (float) Ixz_lump --Att.: xz moment at maximum take off mass
    
    (float) Ixx_lump_zfm --Att.: Roll moment at zero fuel mass
    (float) Iyy_lump_zfm --Att.: Pitch moment at zero fuel mass
    (float) Izz_lump_zfm --Att.: Yaw moment at zero fuel mass
    (float) Ixy_lump_zfm --Att.: xy moment at zero fuel mass 
    (float) Iyz_lump_zfm --Att.: yz moment at zero fuel mass
    (float) Ixz_lump_zfm --Att.: xz moment at zero fuel mass
    
    (float) Ixx_lump_zpm --Att.: Roll moment at zero payload mass
    (float) Iyy_lump_zpm --Att.: Pitch moment at zero payload mass
    (float) Izz_lump_zpm --Att.: Yaw moment at zero payload mass
    (float) Ixy_lump_zpm --Att.: xy moment at zero payload mass 
    (float) Iyz_lump_zpm --Att.: yz moment at zero payload mass
    (float) Ixz_lump_zpm --Att.: xz moment at zero payload mass
    
    (float) Ixx_lump_oem --Att.: Roll moment at operating empty mass
    (float) Iyy_lump_oem --Att.: Pitch moment at operating empty mass
    (float) Izz_lump_oem --Att.: Yaw moment at operating empty mass 
    (float) Ixy_lump_oem --Att.: xy moment at operating empty mass 
    (float) Iyz_lump_oem --Att.: yz moment at operating empty mass
    (float) Ixz_lump_oem --Att.: xz moment at operating empty mass
    
    (float) Ixx_lump_user --Att.: Roll moment with user options
    (float) Iyy_lump_user --Att.: Pitch moment with user options
    (float) Izz_lump_user --Att.: Yaw moment with user options
    (float) Ixy_lump_user --Att.: xy moment with user options 
    (float) Iyz_lump_user --Att.: yz moment with user options 
    (float) Ixz_lump_user --Att.: xz moment with user options
    
    (float) Ixxen  --Att.: Roll moment component relative to the egines
    (float) Iyyen  --Att.: Pitch moment component relative to the egines
    (float) Izzen  --Att.: Yaw moment component relative to the egines
    (float) Ixyen  --Att.: xy moment component relative to the egines
    (float) Iyzen  --Att.: yz moment component relative to the egines
    (float) Ixzen  --Att.: xz moment component relative to the egines
    ========================================================================= 
    (float_array) center_of_gravity --Att.: x,y,z coordinates of the CoG
                                            with maximum take off mass.
    (float_array) cg_zfm    --Att.: x,y,z coordinates of the CoG
                                    with zero fuel mass.
    (float_array) cg_zpm    --Att.: x,y,z coordinates of the CoG
                                    with zero payload mass.
    (float_array) cg_oem    --Att.: x,y,z coordinates of the CoG
                                    with operating empty mass.
    (float_array) cg_user   --Att.: x,y,z coordinates of the CoG
                                    with user options.
    METHODS 
    Name            Description
    """

    def __init__(self):
        self.Ixx_lump = 0
        self.Iyy_lump = 0
        self.Izz_lump = 0
        self.Ixy_lump = 0
        self.Iyz_lump = 0
        self.Ixz_lump = 0
        
        self.Ixx_lump_zfm = 0
        self.Iyy_lump_zfm = 0
        self.Izz_lump_zfm = 0
        self.Ixy_lump_zfm = 0
        self.Iyz_lump_zfm = 0
        self.Ixz_lump_zfm = 0
        
        self.Ixx_lump_zpm = 0
        self.Iyy_lump_zpm = 0
        self.Izz_lump_zpm = 0
        self.Ixy_lump_zpm = 0
        self.Iyz_lump_zpm = 0
        self.Ixz_lump_zpm = 0
        
        self.Ixx_lump_oem = 0
        self.Iyy_lump_oem = 0
        self.Izz_lump_oem = 0
        self.Ixy_lump_oem = 0
        self.Iyz_lump_oem = 0
        self.Ixz_lump_oem = 0

        self.Ixx_lump_user = 0
        self.Iyy_lump_user = 0
        self.Izz_lump_user = 0
        self.Ixy_lump_user = 0
        self.Iyz_lump_user = 0
        self.Ixz_lump_user = 0
        
        self.Ixxen = 0
        self.Iyyen = 0
        self.Izzen = 0
        self.Ixyen = 0
        self.Iyzen = 0
        self.Ixzen = 0
        
        self.center_of_gravity = 0
        self.cg_zfm = 0
        self.cg_zpm = 0
        self.cg_oem = 0
        self.cg_user = 0
        
        
#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':   
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
    
    