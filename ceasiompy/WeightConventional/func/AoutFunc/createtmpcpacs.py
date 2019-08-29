"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Temporary xml file generator to store data in case of
the aircraft is defined with user inputs.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import xml.etree.cElementTree as ET

# Change Aidan
#import tixi3wrapper
#from tixi3wrapper import Tixi3Exception

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""No classes related to the sript"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def create_xml(cpacs_out, NAME):
    """ Function that creates a copy of the cpacs file, inside the ToolInput
        folder, into the ToolOutput folder

        INPUT
        (char) cpacs_out --Arg.: Relative location of the xml file in the
                                 ToolOutput folder.
        (char) NAME      --Arg.: Aircraft Name.

        OUTPUT
        (char) out_xml    --Out.: Relative location of the xml file in the
                                  ToolOutut folder.
    """

    root = ET.Element('cpacs')
    head = ET.SubElement(root, 'header')
    cp1 = ET.SubElement(head, 'cpacsVersion').text = '3.0'
    name = ET.SubElement(head, 'name').text = NAME
    ups = ET.SubElement(head, 'updates')
    up = ET.SubElement(ups, 'update')
    cp2 = ET.SubElement(up, 'cpacsVersion').text = '3.0'
    veh = ET.SubElement(root, 'vehicles')
    air = ET.SubElement(veh, 'aircraft')
    mod = ET.SubElement(air, 'model')

    tree = ET.ElementTree(root)
    tree.write(cpacs_out)
    tixi = open_tixi(cpacs_out)
    tixi.saveDocument(cpacs_out)
    close_tixi(tixi, cpacs_out)

    return(cpacs_out)


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
