"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Functions to manipulate CPACS file, it uses TIXI and TIGL libraries,
    and add some simplified or complementary functions.

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-02
    Last modifiction: 2018-10-04

    TODO:  - 'copy_branch': change all uID of the copied branch? how?
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

import tixi3wrapper
from tixi3wrapper import Tixi3Exception
import tigl3wrapper
from tigl3wrapper import Tigl3Exception

from lib.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================



#==============================================================================
#   FUNCTIONS
#==============================================================================

def open_tixi(cpacs_path):
    """ Create TIXI handles for a CPACS file and return this handle.

    Function 'open_tixi' return the TIXI Handle of a CPACS file given as input
    by its path. If this operation is not possible, it returns 'None'

    Source : All TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    ARGUMENTS
    (str)           cpacs_path      -- Path to the CPACS file

    RETURNS
    (TIXI Handle)   tixi_handle     -- TIXI Handle of the CPACS file
    """

    try:
        tixi_handle = tixi3wrapper.Tixi3()
        tixi_handle.open(cpacs_path)
    except Tixi3Exception:
        return None

    log.info('TIXI handle has been created.')
    return tixi_handle


def open_tigl(tixi_handle):
    """ Create TIGL handles for a CPACS file and return this handle.

    Function 'open_tigl' return the TIGL Handle from its TIXI Handle.
    If this operation is not possible, it returns 'None'

    Source : All TIGL functions http://tigl.sourceforge.net/Doc/index.html

    ARGUMENTS
    (TIXI Handle)   tixi_handle     -- TIXI Handle of the CPACS file

    RETURNS
    (TIGL Handle)   tigl_handle     -- TIGL Handle
    """

    try:
        tigl_handle = tigl3wrapper.Tigl3()
        tigl_handle.open(tixi_handle, '')
    except Tigl3Exception:
        return None

    tigl_handle.logSetVerbosity(1)  # 1 - only error, 2 - error and warnings

    log.info('TIGL handle has been created.')
    return tigl_handle


def close_tixi(tixi_handle,cpacs_out_path):
    """ Close TIXI handle and save the CPACS file.

    Function 'close_tixi' close the TIXI Handle and save the CPACS file at the
    location given by 'cpacs_out_path'

    Source : All TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    ARGUMENTS
    (TIXI Handle)   tixi_handle     -- TIXI Handle of the CPACS file
    (str)           cpacs_out_path  -- Path to the CPACS output file

    RETURNS
    -
    """

    # Save CPACS file
    tixi_handle.save(cpacs_out_path)
    log.info("Output CPACS file has been saved at: " + cpacs_out_path)

    # Close TIXI handle
    tixi_handle.close()
    log.info("TIXI Handle has been closed.")


def create_branch(tixi, xpath, add_child = False):
    """ Function to create a CPACS branch.

    Function 'create_branch' create a branch in the tixi handle and also all
    the missing parent nodes. Be careful, the xpath must be unique until the
    last element, it means, if several element exit, its index must be precised
    (index start at 1).
    e.g.: '/cpacs/vehicles/aircraft/model/wings/wing[2]/name

    If the entire xpath already exist, the option 'add_child' (True/False) let
    the user decide if a named child should be added next to the existing
    one(s). This only valid for the last element of the xpath.

    Source : -

    ARGUMENTS
    (TIXI Handle)   tixi            -- TIXI Handle of the CPACS file
    (str)           xpath           -- xpath of the branch to create
    (boolean)       add_child       -- Choice of adding a name child if the
                                       last element of the xpath if one already
                                       exits

    RETURNS
    (TIXI Handle)   tixi            -- Modified TIXI Handle (with new branch)
    """

    xpath_split = xpath.split("/")
    xpath_count = len(xpath_split)

    for i in range(xpath_count-1):
        xpath_index = i + 2
        xpath_partial ='/'.join(str(m) for m in xpath_split[0:xpath_index])
        xpath_parent ='/'.join(str(m) for m in xpath_split[0:xpath_index-1])
        child = xpath_split[(xpath_index-1)]

        if tixi.checkElement(xpath_partial):
            log.info('Branch "' + xpath_partial + '" already exist')

            if child == xpath_split[-1] and add_child:
                namedchild_nb = tixi.getNamedChildrenCount(xpath_parent,child)
                tixi.createElementAtIndex (xpath_parent,child,namedchild_nb+1)
                log.info('Named child "' + child
                         + '" has been added to branch "'
                         + xpath_parent + '"')
        else:
            tixi.createElement(xpath_parent,child)
            log.info('Child "' + child + '" has been added to branch "'
                     + xpath_parent + '"')

    return tixi


def copy_branch(tixi, xpath_from, xpath_to):
    """ Function to copy a CPACS branch.

    Function 'copy_branch' copy the branch (with sub-branches) from
    'xpath_from' to 'xpath_to' by using recursion. The new branch should
    be identical (uiD, attribute, etc). There is no log in this function
    because of its recursivity.

    Source : -

    ARGUMENTS
    (TIXI Handle)   tixi            -- TIXI Handle of the CPACS file
    (str)           xpath_from      -- xpath of the branch to copy
    (str)           xpath_to        -- Destination xpath

    RETURNS
    (TIXI Handle)   tixi            -- Modified TIXI Handle(with copied branch)
    """

    if not tixi.checkElement(xpath_from):
        raise ValueError(xpath_from + ' this path does not exit!')
    if not tixi.checkElement(xpath_to):
        raise ValueError(xpath_to + ' this path does not exit!')

    child_nb = tixi.getNumberOfChilds(xpath_from)

    if child_nb:
        xpath_to_split = xpath_to.split("/")
        xpath_to_parent ='/'.join(str(m) for m in xpath_to_split[:-1])

        child_list = []
        for i in range(child_nb):
            child_list.append(tixi.getChildNodeName(xpath_from,i+1))

        # If it is a text Element --> no child
        if "#" in child_list[0]:
            elem_to_copy= tixi.getTextElement(xpath_from)
            tixi.updateTextElement(xpath_to,elem_to_copy)

        else:
            # If child are named child (e.g. wings/wing)
            if all(x == child_list[0] for x in child_list):
                namedchild_nb = tixi.getNamedChildrenCount(xpath_from,
                                                           child_list[0])

                for i in range(namedchild_nb):
                    new_xpath_from = xpath_from + "/" + child_list[0] \
                                     + '[' + str(i+1) + ']'
                    new_xpath_to = xpath_to + "/" +  child_list[0] \
                                   + '[' + str(i+1) + ']'
                    tixi.createElement(xpath_to,child_list[0])

                    # Call the function itself for recursion
                    copy_branch(tixi,new_xpath_from,new_xpath_to)

            else:
                for child in child_list:
                    new_xpath_from = xpath_from + "/" + child
                    new_xpath_to = xpath_to + "/" + child

                    # Create child
                    tixi.createElement(xpath_to,child)

                    # Call the function itself for recursion
                    copy_branch(tixi,new_xpath_from,new_xpath_to)

        # Copy attribute(s) if exists
        last_attrib = 0
        attrib_index=1
        while not last_attrib:
            try:
                attrib_name = tixi.getAttributeName(xpath_from,attrib_index)
                attrib_text = tixi.getTextAttribute(xpath_from,attrib_name)
                tixi.addTextAttribute(xpath_to,attrib_name,attrib_text)
                attrib_index = attrib_index + 1
            except:
                last_attrib = 1

    return tixi


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
