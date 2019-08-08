"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    This script updates the cpacs file and copy it on the ToolOutput folder.
    
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

"""No classes"""

   
#=============================================================================
#   FUNCTIONS
#=============================================================================
      
def copy_xml(cpacs_in, NAME):
    """ The function creates a copy of the cpacs file, inside the ToolInput 
        folder, into the ToolOutput folder. 
        
        INPUT
        (char) cpacs_in  --Arg.: Relative location of the xml file in the 
                                 ToolInput folder.                      
        (char) NAME      --Arg.: tooloutput.xml or user_tooloutput.xml
        
        OUTPUT
        (char) out_xml   --Out.: Relative location of the xml file in the 
                                 ToolOutut folder.
    """
        
    tixi = cpf.open_tixi(cpacs_in)
    out_xml = 'ToolOutput/' + NAME
    tixi.saveDocument(out_xml)
    cpf.close_tixi(tixi, out_xml)
    
    return(out_xml)   
    
    
#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':   
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')
    
    