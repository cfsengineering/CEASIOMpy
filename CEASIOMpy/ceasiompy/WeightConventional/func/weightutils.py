"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions and variables for CPACS2GMSH

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-05-24

TODO:

"""

# The following are quite standard values (found in ...)
# Source: https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000023189.pdf

PILOT_NB = 2
PILOT_MASS = 102.0  # kg
CABIN_CREW_MASS = 68.0  # kg
PASSENGER_MASS = 105.0  # kg

PASSENGER_PER_TOILET = 50
TOILET_LENGTH = 1.9  # m


UNUSABLE_FUEL_RATIO = 0.06  # 6% of the total fuel is unusable.

# a bit more tricky, it is an "official" CPACS value
fuel_density = 800  # kg/m^3
