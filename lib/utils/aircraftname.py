"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Script to save the aircraft name from the CPACS file.
     
    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-11-21
    Last modifiction: 2019-01-25
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from lib.utils.ceasiomlogger import get_logger
from lib.utils import cpacsfunctions as cpf

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

""" No classes related to this function"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_name(out_xml): 
    """ The function saves the name of the aircraft from the cpacs file.
        
        INPUT      
        (char) out_xml  --Arg.: Path of the output file.

        OUTPUT
        (file) NAME     --Out.: Name of the aircraft.
    """
    tixi = cpf.open_tixi(out_xml)
    ceasiom_path = '/cpacs'
    
    if not tixi.checkElement(ceasiom_path + '/header/name'):
        log.warning('No aircraft name on cpacs file, using default name')
        NAME = 'Aircraft'
    else:
        NAME = tixi.getTextElement(ceasiom_path + '/header/name')
        
    cpf.close_tixi(tixi, out_xml)
    return(NAME)    
    
    
#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':   
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')
    
    