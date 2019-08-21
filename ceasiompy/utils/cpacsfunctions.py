"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate CPACS file, it uses TIXI and TIGL ceasiompy.aries,
and add some simplified or complementary functions.

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-02
| Last modifiction: 2019-08-21

TODO:

    * 'copy_branch': change all uID of the copied branch? how?
    * 'get_value' to improve, add checks
    * add test function for 'get_list_values'

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

# Should maybe be change depending how/where Tixi and Tigl are installed
#     import tixi3wrapper
#     import tigl3wrapper
#     from tixi3wrapper import Tixi3Exception
#     from tigl3wrapper import Tigl3Exception

import tixi3.tixi3wrapper as tixi3wrapper
import tigl3.tigl3wrapper as tigl3wrapper
from tixi3.tixi3wrapper import Tixi3Exception
from tigl3.tigl3wrapper import Tigl3Exception


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

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns::
        tixi_handle (handles): TIXI Handle of the CPACS file
    """

    tixi_handle = tixi3wrapper.Tixi3()
    tixi_handle.open(cpacs_path)


    log.info('TIXI handle has been created.')

    return tixi_handle


def open_tigl(tixi_handle):
    """ Create TIGL handles for a CPACS file and return this handle.

    Function 'open_tigl' return the TIGL Handle from its TIXI Handle.
    If this operation is not possible, it returns 'None'

    Source :
        * TIGL functions http://tigl.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file

    Returns:
        tigl_handle (handles): TIGL Handle of the CPACS file
    """

    tigl_handle = tigl3wrapper.Tigl3()
    tigl_handle.open(tixi_handle, '')

    tigl_handle.logSetVerbosity(1)  # 1 - only error, 2 - error and warnings

    log.info('TIGL handle has been created.')
    return tigl_handle


def close_tixi(tixi_handle, cpacs_out_path):
    """ Close TIXI handle and save the CPACS file.

    Function 'close_tixi' close the TIXI Handle and save the CPACS file at the
    location given by 'cpacs_out_path' after checking if the directory path
    exists

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file
        cpacs_out_path (str): Path to the CPACS output file

    """

    # Check if the directory of 'cpacs_out_path' exist, if not, create it
    path_split = cpacs_out_path.split('/')[:-1]
    dir_path = '/'.join(str(m) for m in path_split)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        log.info(str(dir_path) + ' directory has been created.')

    # Save CPACS file
    tixi_handle.save(cpacs_out_path)
    log.info("Output CPACS file has been saved at: " + cpacs_out_path)

    # Close TIXI handle
    tixi_handle.close()
    log.info("TIXI Handle has been closed.")


def add_uid(tixi, xpath, uid):
    """ Function that checks and add UID to a specific path,
        the function will automatically update the chosen UID if
        it is already existing.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        xpath (str): xpath of the branch to add the uid
        uid (str): uid to add at xpath

    Returns:
        tixi (handles): Modified TIXI Handle (with new uid)
    """

    exist = True
    uid_new = uid
    i = 0
    while exist is True:
        if not tixi.uIDCheckExists(uid_new):
            tixi.uIDSetToXPath(xpath, uid_new)
            exist = False
        else:
            i = i + 1
            uid_new = uid + str(i)
            log.warning('UID already existing changed to: ' + uid_new)

    return(tixi)


def create_branch(tixi, xpath, add_child=False):
    """ Function to create a CPACS branch.

    Function 'create_branch' create a branch in the tixi handle and also all
    the missing parent nodes. Be careful, the xpath must be unique until the
    last element, it means, if several element exit, its index must be precised
    (index start at 1).
    e.g.: '/cpacs/vehicles/aircraft/model/wings/wing[2]/name'

    If the entire xpath already exist, the option 'add_child' (True/False) let
    the user decide if a named child should be added next to the existing
    one(s). This only valid for the last element of the xpath.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        xpath (str): xpath of the branch to create
        add_child (boolean): Choice of adding a name child if the last element
                             of the xpath if one already exits

    Returns:
        tixi (handles): Modified TIXI Handle (with new branch)
    """

    xpath_split = xpath.split("/")
    xpath_count = len(xpath_split)

    for i in range(xpath_count-1):
        xpath_index = i + 2
        xpath_partial = '/'.join(str(m) for m in xpath_split[0:xpath_index])
        xpath_parent = '/'.join(str(m) for m in xpath_split[0:xpath_index-1])
        child = xpath_split[(xpath_index-1)]
        if tixi.checkElement(xpath_partial):
            log.info('Branch "' + xpath_partial + '" already exist')

            if child == xpath_split[-1] and add_child:
                namedchild_nb = tixi.getNamedChildrenCount(xpath_parent, child)
                tixi.createElementAtIndex (xpath_parent,child,namedchild_nb+1)
                log.info('Named child "' + child
                         + '" has been added to branch "'
                         + xpath_parent + '"')
        else:
            print(xpath_parent)
            tixi.createElement(xpath_parent, child)
            log.info('Child "' + child + '" has been added to branch "'
                     + xpath_parent + '"')

    return tixi


def copy_branch(tixi, xpath_from, xpath_to):
    """ Function to copy a CPACS branch.

    Function 'copy_branch' copy the branch (with sub-branches) from
    'xpath_from' to 'xpath_to' by using recursion. The new branch should
    be identical (uiD, attribute, etc). There is no log in this function
    because of its recursivity.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file
        xpath_from (str): xpath of the branch to copy
        xpath_to (str): Destination xpath

    Returns:
        tixi (handles): Modified TIXI Handle (with copied branch)
    """

    if not tixi.checkElement(xpath_from):
        raise ValueError(xpath_from + ' this path does not exit!')
    if not tixi.checkElement(xpath_to):
        raise ValueError(xpath_to + ' this path does not exit!')

    child_nb = tixi.getNumberOfChilds(xpath_from)

    if child_nb:
        xpath_to_split = xpath_to.split("/")
        xpath_to_parent = '/'.join(str(m) for m in xpath_to_split[:-1])

        child_list = []
        for i in range(child_nb):
            child_list.append(tixi.getChildNodeName(xpath_from, i+1))

        # If it is a text Element --> no child
        if "#" in child_list[0]:
            elem_to_copy = tixi.getTextElement(xpath_from)
            tixi.updateTextElement(xpath_to, elem_to_copy)

        else:
            # If child are named child (e.g. wings/wing)
            if all(x == child_list[0] for x in child_list):
                namedchild_nb = tixi.getNamedChildrenCount(xpath_from,
                                                           child_list[0])

                for i in range(namedchild_nb):
                    new_xpath_from = xpath_from + "/" + child_list[0] \
                                     + '[' + str(i+1) + ']'
                    new_xpath_to = xpath_to + "/" + child_list[0] \
                                   + '[' + str(i+1) + ']'
                    tixi.createElement(xpath_to, child_list[0])

                    # Call the function itself for recursion
                    copy_branch(tixi, new_xpath_from, new_xpath_to)

            else:
                for child in child_list:
                    new_xpath_from = xpath_from + "/" + child
                    new_xpath_to = xpath_to + "/" + child

                    # Create child
                    tixi.createElement(xpath_to, child)

                    # Call the function itself for recursion
                    copy_branch(tixi, new_xpath_from, new_xpath_to)

        # Copy attribute(s) if exists
        last_attrib = 0
        attrib_index = 1
        while not last_attrib:
            try:
                attrib_name = tixi.getAttributeName(xpath_from, attrib_index)
                attrib_text = tixi.getTextAttribute(xpath_from, attrib_name)
                tixi.addTextAttribute(xpath_to, attrib_name, attrib_text)
                attrib_index = attrib_index + 1
            except:
                last_attrib = 1

    return tixi


def get_value(tixi, xpath):
    """ Function to get value from a CPACS branch if this branch exist.

    Function 'get_value' check first if the the xpath exit and a value is store
    at this place. Then, it gets and returns this value. If the value or the
    xpath does not exit it raise an error and return 'None'.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file
        xpath (str): xpath of the value to get

    Returns:
         value (float or str): Value found at xpath
    """

    # Try to get the a value at xpath
    try:
        value = tixi.getTextElement(xpath)
    except:
        value = None

    if value:
        try: # check if it is a 'float'
            is_float = isinstance(float(value), float)
            value = float(value)
        except:
            pass
    else:
        # check if the path exist
        if tixi.checkElement(xpath):
            log.error('No value has been fournd at ' + xpath)
            raise ValueError('No value has been fournd at ' + xpath)
        else:
            log.error(xpath + ' cannot be found in the CPACS file')
            raise ValueError(xpath + ' cannot be found in the CPACS file')

    return value


def get_value_or_default(tixi,xpath,default_value):
    """ Function to get value from a CPACS branch if this branch exist, it not
        it returns the default value.

    Function 'get_value_or_default' do the same than the function 'get_value'
    but if no value is found at this place it returns the default value and add
    it at the xpath. If the xpath does not exit, it is created.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file
        xpath (str): xpath of the value to get
        default_value (str, float or int): Default value

    Returns:
        tixi (handles): Modified TIXI Handle (with added default value)
        value (str, float or int): Value found at xpath
    """

    value = None
    try:
        value = get_value(tixi, xpath)
    except:
        pass

    if value is None:
        log.info('Default value will be used instead')
        value = default_value

        xpath_parent = '/'.join(str(m) for m in xpath.split("/")[:-1])
        value_name = xpath.split("/")[-1]
        tixi = create_branch(tixi,xpath_parent,False)

        is_int = False
        is_float = False
        try: # check if it is an 'int' or 'float'
            is_int = isinstance(float(default_value), int)
            is_float = isinstance(float(default_value), float)
            value = float(default_value)
        except:
            pass

        if is_float or is_int:
           tixi.addDoubleElement(xpath_parent,value_name,value,'%g')
        else:
           tixi.addTextElement(xpath_parent,value_name,value)
        log.info('Default value has been add to the cpacs file at: ' + xpath)
    else:
        log.info('Value found at ' + xpath + ' will be used.')

    return tixi, value


def get_list_values(tixi, xpath):
    """ Function to get a list of float from an xpath.

    Function 'get_list_values' returns a list of float. Retruns empty list if
    nothing is found at the xpath.

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html

    Args:
        tixi_handle (handles): TIXI Handle of the CPACS file
        xpath (str): xpath of the value to get

    Returns:
         list_values (list): List of float fround at xpath
    """

    # Try to get the a value at xpath
    try:
        list_values_str = tixi.getTextElement(xpath)
    except:
        list_values_str = None

    if list_values_str is not None:
        list_values = list_values_str.split(';')
        if list_values[-1] == '':
            list_values.pop()
        list_values = [float(elem) for elem in list_values]

    else:
        # Check if the path exist
        if tixi.checkElement(xpath):
            log.warning('No value has been fournd at ' + xpath)
            log.warning('An empty list will be return')
            list_values = []
        else:
            log.warning(xpath + ' cannot be found in the CPACS file')
            log.warning('An empty list will be return')
            list_values = []

    return list_values


def aircraft_name(cpacs_path):
    """ The function gat the name of the aircraft from the cpacs file or add a
        default one if non-existant.

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns:
        name (str): Name of the aircraft.
    """

    tixi = open_tixi(cpacs_path)

    aircraft_name_xpath = '/cpacs/header/name'
    tixi, name = get_value_or_default(tixi,aircraft_name_xpath,'Aircraft')
    log.info('The name of the aircraft is : ' + name)

    close_tixi(tixi, cpacs_path)

    return(name)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
