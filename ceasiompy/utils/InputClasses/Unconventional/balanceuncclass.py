"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains the user inputs required for the
balance unconventional analysis.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""
# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np


# =============================================================================
#   CLASSES
# =============================================================================


class BalanceInputs:
    """
    The class contains all the  input from user needed
    for the balance analysis.

    Attributes:
        F_PERC (int): Fuel percentage for CoG and MoI evaluation to  define
                      only if USER_CASE = True.
        P_PERC (int): Payload percentage for CoG and MoI evaluation to  define
                      only if USER_CASE = True.
        WPP (float): Number of points to subdivide the wing upper or lower profile [-].
        SPACING_WING (float): Spacing of nodes for the wing along the span direction [m].
        SPACING_FUSE (float): Spacing of nodes for the fuselage along the radial,
                              circumferencial and longitudial directions [m].
        USER_CASE (boolean): Set True to e able to evaluate the CoG and the MoI
                             with a chosen percentage of fuel mass (F_PERC) and
                             payload percentage (P_PERC).
        USER_EN_PLACEMENT (boolean): Set True if the user defines the the engine
                                     position inside the CPACS file.

    """

    def __init__(self):
        self.F_PERC = 0
        self.P_PERC = 0
        self.WPP = 30.0
        self.SPACING_WING = 0.05
        self.SPACING_FUSE = 0.05
        self.USER_CASE = False
        self.USER_EN_PLACEMENT = False


# =============================================================================


class MassesWeights:
    """
    The class contains all the aircraft mass and weight value needed
    for the unconventional balance analysis.

    Attributes:
        mass_fuel_maxpass (float): Max fuel mass with max payload [kg].
        mass_fuel_mass (float): Max fuel mass allowed (evaluated) [kg].
        maximum_take_off_mass (float): Maximum take off mass [kg].
        operating_empty_mass (float): Operating empty mass [kg].
        mass_payload (float): Payload mass [kg].
        mass_engines (float): Engines total mass [kg].

    """

    def __init__(self):
        self.mass_fuel_maxpass = np.nan
        self.mass_fuel_tot = np.nan
        self.maximum_take_off_mass = np.nan
        self.operating_empty_mass = np.nan
        self.mass_payload = np.nan
        self.mass_engines = 0


# =============================================================================


class BalanceOutputs:
    """
    The class contains all the output value of the unconventional
    Balance analysis.

    Attributes:
        === Moment of inertia estimated with the lumped masses method ===
        Ixx_lump (float): Roll moment at maximum take off mass
        Iyy_lump (float): Pitch moment at maximum take off mass
        Izz_lump (float): Yaw moment at maximum take off mass
        Ixy_lump (float): xy moment at maximum take off mass
        Iyz_lump (float): yz moment at maximum take off mass
        Ixz_lump (float): xz moment at maximum take off mass

        Ixx_lump_zfm (float): Roll moment at zero fuel mass
        Iyy_lump_zfm (float): Pitch moment at zero fuel mass
        Izz_lump_zfm (float): Yaw moment at zero fuel mass
        Ixy_lump_zfm (float): xy moment at zero fuel mass
        Iyz_lump_zfm (float): yz moment at zero fuel mass
        Ixz_lump_zfm (float): xz moment at zero fuel mass

        Ixx_lump_zpm (float): Roll moment at zero payload mass
        Iyy_lump_zpm (float): Pitch moment at zero payload mass
        Izz_lump_zpm (float): Yaw moment at zero payload mass
        Ixy_lump_zpm (float): xy moment at zero payload mass
        Iyz_lump_zpm (float): yz moment at zero payload mass
        Ixz_lump_zpm (float): xz moment at zero payload mass

        Ixx_lump_oem (float): Roll moment at operating empty mass
        Iyy_lump_oem (float): Pitch moment at operating empty mass
        Izz_lump_oem (float): Yaw moment at operating empty mass
        Ixy_lump_oem (float): xy moment at operating empty mass
        Iyz_lump_oem (float): yz moment at operating empty mass
        Ixz_lump_oem (float): xz moment at operating empty mass

        Ixx_lump_user(float).: Roll moment with user options
        Iyy_lump_user(float).: Pitch moment with user options
        Izz_lump_user(float).: Yaw moment with user options
        Ixy_lump_user(float).: xy moment with user options
        Iyz_lump_user(float).: yz moment with user options
        Ixz_lump_user(float).: xz moment with user options

        Ixxen (float): Roll moment component relative to the egines
        Iyyen (float): Pitch moment component relative to the egines
        Izzen (float): Yaw moment component relative to the egines
        Ixyen (float): xy moment component relative to the egines
        Iyzen (float): yz moment component relative to the egines
        Ixzen (float): xz moment component relative to the egines

        center_of_gravity (float_array): x,y,z coordinates of the CoG with
                                         maximum take off mass.
        cg_zfm (float_array): x,y,z coordinates of the CoG with zero fuel mass.
        cg_zpm (float_array): x,y,z coordinates of the CoG with zero payload mass.
        cg_oem (float_array): x,y,z coordinates of the CoG with operating empty mass.
        cg_user (float_array): x,y,z coordinates of the CoG with user options.

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


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("#########################################################")
    print("# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #")
    print("#########################################################")
