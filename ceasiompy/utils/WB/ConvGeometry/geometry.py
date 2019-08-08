"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    This file will connect the wing/fuse/output modules.

    Works with Python 2.7/3.4
    Author : Stefano Piccini
    Date of creation: 2018-09-27
    Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from lib.utils.ceasiomlogger import get_logger
from .Fuselage.fusegeom import fuse_geom_eval
from .Wings.winggeom import wing_geom_eval
from .Output.outputgeom import produce_output_txt

from lib.utils.InputClasses.Conventional.aircraftgeometryclass\
    import AircraftGeometry

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


#=============================================================================
#   FUNCTIONS
#=============================================================================  

def geometry_eval(cpacs_in, NAME):
    """This function exectute the functions to analyze the cpacs file and 
       evaluate the wings and fuselage geometry.
       
    ARGUMENTS
    (char) cpacs_in    -- Arg.: Cpacs xml file location.
    (char) NAME        -- Arg.: Name of the aircraft.
    
    OUTPUTS
    (class) AircraftGeometry    --Out.: Updated aircraft_geometry class.
    ##======= Class are defined in the InputClasses folder =======##
    """
    ag = AircraftGeometry()
    
##================================= FUSELAGES ==============================##  
    ag = fuse_geom_eval(ag, cpacs_in)
    
#==================================== WINGS ===============================##  
    ag = wing_geom_eval(ag, cpacs_in)
    
##======================== OUTPUT TXT FILE GENERATION ======================##      
    produce_output_txt(ag, NAME)

    return(ag)
    
    
#=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__': 
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')   
    
    