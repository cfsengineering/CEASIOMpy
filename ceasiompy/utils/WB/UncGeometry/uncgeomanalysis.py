"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main geometry evaluation script, it connects the wing and fuselage
geometry analysis for unconventional aircraft.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-12-07

"""


# =============================================================================
#   IMPORTS
# =============================================================================

# Classes
from ceasiompy.utils.InputClasses.Unconventional.aircraftgeometryclass import AircraftWingGeometry
from ceasiompy.utils.InputClasses.Unconventional.aircraftgeometryclass import AircraftFuseGeometry

# Geometry without fuselage
from .NoFuseGeom.bwbwingsanalysis import geom_eval
from .NoFuseGeom.volumesdefinition import wing_check_thickness
from .Output.outputgeom import produce_wing_output_txt

# Geometry with fuselage
from .WithFuseGeom.Wings.wingsgeom import wing_geom_eval
from .WithFuseGeom.Fuselages.fusegeom import fuse_geom_eval
from .Output.outputgeom import produce_geom_output_txt

from cpacspy.cpacsfunctions import open_tixi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def get_number_of_parts(cpacs_in):
    """The fuction counts the number of fuselage and wings.

    Args:
        cpacs_in (str): Path to the CPACS file.

    Retrurns:
        fus_nb (int): Number of fuselages.
        wing_nb (int) : Number of wings.

    """

    tixi = open_tixi(cpacs_in)

    if tixi.checkElement("/cpacs/vehicles/aircraft/model/fuselages"):
        fus_nb = tixi.getNamedChildrenCount("/cpacs/vehicles/aircraft/model/fuselages", "fuselage")
    else:
        fus_nb = 0

    if tixi.checkElement("/cpacs/vehicles/aircraft/model/wings"):
        wing_nb = tixi.getNamedChildrenCount("/cpacs/vehicles/aircraft/model/wings", "wing")
    else:
        wing_nb = 0

    tixi.save(cpacs_in)

    return (fus_nb, wing_nb)


def no_fuse_geom_analysis(cpacs_in, FLOOR_NB, wing_nb, h_min, FUEL_ON_CABIN, NAME, TP):
    """The fuction evaluates the geometry of an aircraft realized without
        fuselage, like the blended wing body.

    Args:
        cpacs_in (str): Relative position of the xml file.
        FLOOR_NB (int): Number of floors.
        wing_nb (int): Number of wings.
        h_min  (float): Minimum height for the fuselage [m].
        FUEL_ON_CABIN (float): Percentage of fuel inside cabin segments.
        NAME (str): Name of the aircraft.
        TP (boolean): True if the aircraft is a turboprop.

    Retrurns:
        wing_nodes(float-array): 3D array containing the nodes coordinates (x,y,z)[m,m,m].
        awg (class): AircraftWingGeometry class look at (class) aircraft_geometry_class.py in the
                     classes folder for explanation.

    """
    awg = AircraftWingGeometry()
    awg = geom_eval(wing_nb, awg, cpacs_in)
    (awg, wing_nodes) = wing_check_thickness(h_min, awg, cpacs_in, TP, FUEL_ON_CABIN)
    produce_wing_output_txt(awg, NAME)

    return (awg, wing_nodes)


def with_fuse_geom_analysis(cpacs_in, fus_nb, wing_nb, h_min, adui, TP, F_FUEL, NAME):
    """The fuction evaluates the geometry of an aircraft realized without
        fuselage.

    Args:
        cpacs_in (str): Path to the CPACS file.
        fus_nb (int): Number of fuselages.
        wing_nb (int): Number of wings.
        h_min (float): Minimum height for the fuselage [m].
        adui (class): AdvancedInputs class.
        TP (boolean): True if the aircraft is a turboprop.
        F_FUEL (boolean-array): True if the corresponding fuselage can contain fuel.
        NAME (str): Name of the aircraft.

    Returns:
        awg (class): AircraftWingGeometry class look at aircraft_geometry_class.py
                     in the classes folder for explanation.
        afg (class): AircraftFuseGeometry class look at aircraft_geometry_class.py
                     in the classes folder for explanation.
    """

    awg = AircraftWingGeometry()
    afg = AircraftFuseGeometry(fus_nb)

    awg = wing_geom_eval(wing_nb, TP, awg, cpacs_in)
    afg = fuse_geom_eval(fus_nb, h_min, adui.VRT_THICK, F_FUEL, afg, cpacs_in)
    produce_geom_output_txt(afg, awg, NAME)

    return (afg, awg)


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    log.warning("#########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #")
    log.warning("#########################################################")
