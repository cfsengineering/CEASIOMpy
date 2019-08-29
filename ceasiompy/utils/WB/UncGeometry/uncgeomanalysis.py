"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main geometry evaluation script, it connects the wing and fuselage
geometry analysis for unconventional aircraft.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-07
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

# Classes
from ceasiompy.utils.InputClasses.Unconventional.aircraftgeometryclass\
    import AircraftWingGeometry
from ceasiompy.utils.InputClasses.Unconventional.aircraftgeometryclass\
    import AircraftFuseGeometry

# Geometry without fuselage
from .NoFuseGeom.bwbwingsanalysis import geom_eval
from .NoFuseGeom.volumesdefinition import wing_check_thickness
from .Output.outputgeom import produce_wing_output_txt

# Geometry with fuselage
from .WithFuseGeom.Wings.wingsgeom import wing_geom_eval
from .WithFuseGeom.Fuselages.fusegeom import fuse_geom_eval
from .Output.outputgeom import produce_geom_output_txt

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_number_of_parts(cpacs_in):
    """ The fuction counts the number of fuselage and wings.

        INPUT
        (char) cpacs_in     --Arg.: Relative position of the xml file.

        OUTPUT
        (int) f_nb          --Out.: Number of fuselages.
        (int) W_nb          --Out.: Number of wings.

    """
    # Opening tixi and tigl
    tixi = open_tixi(cpacs_in)

    if not tixi.checkElement('/cpacs/vehicles/aircraft\
                             /model/fuselages'):
        f_nb = 0
    else:
        f_nb = tixi.getNamedChildrenCount('/cpacs/vehicles/aircraft\
                                          /model/fuselages', 'fuselage')
    if not tixi.checkElement('/cpacs/vehicles/aircraft\
                             /model/wings'):
        w_nb = 0
    else:
        w_nb = tixi.getNamedChildrenCount('/cpacs/vehicles/aircraft\
                                          /model/wings', 'wing')
    close_tixi(tixi, cpacs_in)

    return(f_nb, w_nb)


#=============================================================================

def no_fuse_geom_analysis(FLOOR_NB, w_nb, h_min, FUEL_ON_CABIN,\
                          cpacs_in, NAME, TP):
    """ The fuction evaluates the geometry of an aircraft realized without
        fuselage, like the blended wing body.

        INPUT
        (int) FLOOR_NB        --Arg.: Number of floors.
        (int) w_nb            --Arg.: Number of wings.
        (float) h_min         --Arg.: Minimum height for the fuselage [m].
        (float) FUEL_ON_CABIN --Arg.: Percentage of fuel inside cabin segments.
        (char) cpacs_in       --Arg.: Relative position of the xml file.
        (char) NAME           --Arg.: Name of the aircraft.
        (boolean) TP          --Arg.: True if the aircraft is a turboprop.

        OUTPUT
        (float-array) wing_nodes    --Out.: 3D array containing the
                                            nodes coordinates (x,y,z)
                                            [m,m,m].
        (class) awg         --Out.: AircraftWingGeometry class look at
                                    aircraft_geometry_class.py in the
                                    classes folder for explanation.

    """
    awg = AircraftWingGeometry()
    awg = geom_eval(w_nb, awg, cpacs_in)
    (awg, wing_nodes) = wing_check_thickness(h_min, awg, cpacs_in,\
                                             TP, FUEL_ON_CABIN)
    produce_wing_output_txt(awg, NAME)

    return(awg, wing_nodes)


#=============================================================================

def with_fuse_geom_analysis(f_nb, w_nb, h_min, adui, TP,\
                            F_FUEL, cpacs_in, NAME):
    """ The fuction evaluates the geometry of an aircraft realized without
        fuselage.

        INPUT
        (int) f_nb              --Arg.: Number of fuselages.
        (int) w_nb              --Arg.: Number of wings.
        (float) h_min           --Arg.: Minimum height for the fuselage [m].
        (class) adui            --Arg.: AdvancedInputs class.
        ##=========== Class is defined in the InputClasses folder =========##
        (boolean) TP            --Arg.: True if the aircraft is a turboprop.
        (boolean-array) F_FUEL  --Arg.: True if the corresponding fuselage
                                        can contain fuel.
        (char) cpacs_in     --Arg.: Relative position of the xml file.
        (char) NAME         --Arg.: Name of the aircraft.

        OUTPUT
        (class) awg         --Out.: AircraftWingGeometry class look at
                                    aircraft_geometry_class.py in the
                                    classes folder for explanation.
        (class) afg         --Out.: AircraftFuseGeometry class look at
                                    aircraft_geometry_class.py in the
                                    classes folder for explanation.
    """
    awg = AircraftWingGeometry()
    afg = AircraftFuseGeometry(f_nb)

    awg = wing_geom_eval(w_nb, TP, awg, cpacs_in)
    afg = fuse_geom_eval(f_nb, h_min, adui.VRT_THICK, F_FUEL, afg, cpacs_in)
    produce_geom_output_txt(afg, awg, NAME)

    return(afg, awg)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
