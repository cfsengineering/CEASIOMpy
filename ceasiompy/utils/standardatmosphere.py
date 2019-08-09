"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Give atmosphere parameters at any altitudes from 0 to 84000m

| Works with Python 2.7
| Test: /test/TestStandardAtmosphere/test_standardatmosphere.py
| Author : Aidan Jungo
| Creation: 2018-10-04
| Last modifiction: 2018-10-08

TODO:

    * move 'Example of use' in an exteranl document
    * Try compatibility with Python 3.4

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

import math
import numpy
import matplotlib.pyplot as plt

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

class Atmosphere:
    """
    Description of the class

    ATTRIBUTES
    (float)         temp            -- Temperature [K]
    (float)         pres            -- Pressure [Pa]
    (float)         dens            -- Density [kg/m^3]
    (float)         visc            -- Dynamic viscosity [Pa*s]
    (float)         sos             -- Speed of sound [m/s]
    (float)         re_len_ma       -- Reynolds number per length per Mach
    (float)         grav            -- Gravity [m/s^2] (not depend on
                                       atmosphere composition but vary with
                                       altitude)

    METHODS
    Name            Description
    """

    def __init__(self):
        """On earth surface, at altitude of 0m  (reference values or 0)"""

        self.temp = 288.15
        self.pres = 101325.0
        self.dens = 1.225
        self.visc = 0
        self.sos = 0
        self.re_len_ma = 0
        self.grav = 9.80665


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_atmosphere(alt):
    """ Return atmosphere parameters for any given altitude.

    Function which caluculate the Reynolds number per unit of length [m] per
    unit of Mach [-] for a given altitude between 0 and 84000m
    Calculate also Temperature, Pressure, Density, Viscosity, Speed of Sound at
    this altitude

    Source : 1976 Standard Atmosphere, coded from:
             http://www.digitaldutch.com/atmoscalc/graphs.htm
             and https://en.wikipedia.org/wiki/Gravity_of_Earth

    ARGUMENTS
    (float)     alt       -- Atmosphere altitude from earth surface [m]

    RETURNS
    (Object)    atm       -- Object Atmosphere (see example of use at the end)
    """

    # Create an object 'Atmosphere'
    atm = Atmosphere()

    # Air Constants
    MOL_WEIGHT = 28.9644  # [Mol]
    GAS_CONST = 8.31432  # Gas constant [kg/Mol/K]
    GMR = atm.grav * MOL_WEIGHT / GAS_CONST
    GAMMA = 1.4  # [-]
    R = 287.053  # [J/Kg/K]

    # Layers definition
    height = [0.0, 11000.0, 20000.0, 32000.0, 47000.0,
              51000.0, 71000.0, 84852.0]  # [m]
    temp_point = [288.15, 216.65, 216.65, 228.65, 270.65,
                  270.65, 214.65, 186.946]  # [K]
    temp_grad = [-6.5, 0.0, 1.0, 2.8, 0.0, -2.8, -2.0]  # [K/m]
    rel_pressure = [1.0, 2.23361105092158e-1, 5.403295010784876e-2,
                    8.566678359291667e-3, 1.0945601337771144e-3,
                    6.606353132858367e-4, 3.904683373343926e-5,
                    3.6850095235747942e-6]  # [-]

    # Reference values
    temp_ref = atm.temp
    pres_ref = atm.pres
    dens_ref = atm.dens
    grav_ref = atm.grav

    # Check if Altitude is valid and find to which layer it corresponds
    if alt >= 0 and alt < 84852:
        i = 0
        while alt > height[i+1]:
            i = i + 1
    else:
        log.warning('Altitude must be between 0 and 84000m!')
        raise ValueError('Altitude must be between 0 and 84000m!')
        return 0

    # Calculate gravity at altitude (Earth is assumed as a perfect
    # sphere with a radially symmetric distribution of mass; Radius=6371km)
    atm.grav = grav_ref * (6.371e6/(6.371e6 + float(alt)))**2

    # Calculate temperature at altitude (interpolation)
    atm.temp = temp_point[i] + temp_grad[i]/1000.0 * (alt-height[i])

    # Calculate pressure at altitude
    if abs(temp_grad[i]) < 0.1:
        atm.pres = pres_ref * rel_pressure[i] * math.exp(-GMR \
                   * (alt-height[i]) / 1000.0 / (temp_point[i]))
    else:
        atm.pres = pres_ref * rel_pressure[i] * (temp_point[i]/atm.temp) \
                   ** (GMR/(temp_grad[i]/1000.0)/1000.0)

    # Calculate density at altitude
    atm.dens = dens_ref * atm.pres/pres_ref * temp_ref/atm.temp

    # Calculate dynamic viscosity at altitude
    atm.visc = 1.512041288 * atm.temp**1.5 / (atm.temp+120) / 1000000.0

    # Calculate speed of sound at altitude
    atm.sos = math.sqrt(GAMMA*R*atm.temp)

    # Reynolds per unit of length [m] per unit of Mach [Ma] at Altitude
    atm.re_len_ma = atm.dens * atm.sos / atm.visc

    return atm


def plot_atmosphere():
    """ Plot Temperature (or other parameters) vs altitude.

    Source : -

    ARGUMENTS

    RETURNS
    (graph)      graph     -- Parameter vs altitude (0 to 84000m)
    """

    # Create 500 points between 0 and 84000m
    alt_list = numpy.arange(0.0, 84000., 500.0)

    temp_list = []
    pres_list = []
    dens_list = []
    visc_list = []
    sos_list = []
    grav_list = []

    for alt in alt_list:
        atm = get_atmosphere(alt)
        temp_list.append(atm.temp)
        pres_list.append(atm.pres)
        dens_list.append(atm.dens)
        visc_list.append(atm.visc)
        sos_list.append(atm.sos)
        grav_list.append(atm.grav)

    plt.plot(temp_list, alt_list)

    plt.xlabel('Temperature (K)')
    plt.ylabel('Altitude (m)')
    plt.title('Temperature vs Altitude')
    plt.grid(True)
    plt.show()


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Plot Standart atmosphere')

    plot_atmosphere()


# Example of use
#AtmAt1000m = atmosphere(1000)
#print(AtmAt1000m.Temp)
#print(AtmAt1000m.Pres)
#print(AtmAt1000m.Dens)
#print(AtmAt1000m.Visc)
#print(AtmAt1000m.SoS)
#print(AtmAt1000m.Gravity)
#print(AtmAt1000m.ReLMa)

#plot_atm_value()

# or to plot the graphs
#>>python standardatmosphere.py
