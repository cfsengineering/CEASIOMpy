"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test all the function for 'lib/utils/cpacsfunctions.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-02
| Last modifiction: 2019-10-21

TODO:

    * test_get_path function should be tested on a Windows machine

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil

import pytest
from pytest import raises

from tixi3.tixi3wrapper import Tixi3Exception
from tigl3.tigl3wrapper import Tigl3Exception

import ceasiompy.utils.cpacsfunctions as cpsf

from ceasiompy.utils.ceasiomlogger import get_logger


log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR,'ToolInput','simpletest_cpacs.xml')
CPACS_OUT_PATH = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')



#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_open_tixi():
    """Test the function 'open_tixi'"""

    # Create TIXI handles for a valid CPACS file
    tixi_handle = cpsf.open_tixi(CPACS_IN_PATH)

    assert tixi_handle

    # Raise error for an invalid CPACS path
    with pytest.raises(Tixi3Exception):
        tixi_handle = cpsf.open_tixi('invalid/CPACS/path')


def test_open_tigl():
    """Test the function 'open_tigl'"""

    # Create TIGL handle for a valid TIXI handles
    tixi_handle = cpsf.open_tixi(CPACS_IN_PATH)
    tigl_handle = cpsf.open_tigl(tixi_handle)

    assert tigl_handle

    # Raise error for an invalid TIXI handles
    with pytest.raises(AttributeError):
        tixi_handle = cpsf.open_tigl('invalid_TIGL_handle')


def test_wing_nb():
    '''Test if the number of wing is equal to 1'''

    tixi_handle = cpsf.open_tixi(CPACS_IN_PATH)
    wing_nb = tixi_handle.getNamedChildrenCount('/cpacs/vehicles/aircraft\
              /model/wings', 'wing')
    assert wing_nb == 1


def test_fuse_nb():
    '''Test if the number of fuselage is equal to 1'''

    tixi_handle = cpsf.open_tixi(CPACS_IN_PATH)
    fuse_nb = tixi_handle.getNamedChildrenCount('/cpacs/vehicles/aircraft\
              /model/fuselages', 'fuselage')
    assert fuse_nb == 1


def test_close_tixi():
    """Test the function 'close_tixi'"""

    tixi_handle = cpsf.open_tixi(CPACS_IN_PATH)

    # Remove /ToolOutput directory
    tooloutput_dir = os.path.join(MODULE_DIR,'ToolOutput')
    shutil.rmtree(tooloutput_dir,ignore_errors=True)
    log.info(str(tooloutput_dir) + ' has been remove for a test.')

    # Save unmodified tixi in the output CPACS file
    cpsf.close_tixi(tixi_handle, CPACS_OUT_PATH)

    # Check if /ToolOutput directory has been created
    assert os.path.exists(tooloutput_dir)

    # Read Input and Ouput CPACS file as text, to compare them
    with open(CPACS_IN_PATH) as file_in:
        lines_cpacs_in = file_in.readlines()
    with open(CPACS_OUT_PATH) as file_out:
        lines_cpacs_out = file_out.readlines()

    assert lines_cpacs_in == lines_cpacs_out


def test_create_branch():
    """Test the function 'create_branch'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    update_branch = '/cpacs/header/updates/update'
    new_branch = '/cpacs/header/updates/update[3]/test/test1/test2'

    # This branch should be added
    cpsf.create_branch(tixi, update_branch, True)
    # This branch should not be added
    cpsf.create_branch(tixi, update_branch, False)
    # 'new_branch' should be added
    cpsf.create_branch(tixi, new_branch)

    # Save modified tixi in the output CPACS file
    cpsf.close_tixi(tixi, CPACS_OUT_PATH)

    # Reopen the output CPACS file to check if branches have been added
    tixi_out = cpsf.open_tixi(CPACS_OUT_PATH)

    # Check if the number of "update" child is equal to 3
    namedchild_nb = tixi_out.getNamedChildrenCount('/cpacs/header/updates',
                                                       'update')
    assert namedchild_nb == 3

    # Check if 'new_branch' has been added
    branch_check = tixi_out.checkElement(new_branch)
    assert branch_check


def test_copy_branch():
    """Test the function 'copy_branch'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    # Create a new 'header' branch and copy the original 'header' into it
    xpath_new = '/cpacs/header'
    xpath_from = '/cpacs/header[1]'
    xpath_to = '/cpacs/header[2]'
    cpsf.create_branch(tixi, xpath_new, True)
    cpsf.copy_branch(tixi, xpath_from, xpath_to)

    # Check if a specific element has been copied
    xpath_elem_from = '/cpacs/header[1]/updates/update[1]/timestamp'
    xpath_elem_to = '/cpacs/header[2]/updates/update[1]/timestamp'
    elem_from = tixi.getTextElement(xpath_elem_from)
    elem_to = tixi.getTextElement(xpath_elem_to)

    assert elem_from == elem_to

    # Check if a specific attribute has been copied
    attrib_text_from = tixi.getTextAttribute(xpath_elem_from, 'uID')
    attrib_text_to = tixi.getTextAttribute(xpath_elem_to, 'uID')

    assert attrib_text_from == attrib_text_to


def test_get_uid():
    """Test the function 'get_uid'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    # Check if a false xpath raises ValueError
    xpath = '/cpacs/vehicles/aircraft/MYmodel'
    with pytest.raises(ValueError):
        value_error = cpsf.get_uid(tixi,xpath)

    # Check if a no uid at xpath raises ValueError
    xpath = '/cpacs/vehicles/aircraft'
    with pytest.raises(ValueError):
        value_error = cpsf.get_uid(tixi,xpath)

    # Check if it get correctly the uid
    xpath = '/cpacs/vehicles/aircraft/model'
    uid = cpsf.get_uid(tixi,xpath)
    assert uid == 'Cpacs2Test'


def test_add_uid():
    """Test the function 'add_uid'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    # Update UID
    xpath = '/cpacs/vehicles/aircraft/model'
    new_uid = 'New_aircrat_name'
    cpsf.add_uid(tixi,xpath,new_uid)
    updated_uid = tixi.getTextAttribute(xpath, 'uID')

    assert updated_uid == new_uid

    # Add UID
    xpath = '/cpacs/vehicles/aircraft/model/name'
    new_uid = 'nameUID'
    cpsf.add_uid(tixi,xpath,new_uid)
    added_uid = tixi.getTextAttribute(xpath, 'uID')

    assert added_uid == new_uid

    # Add existing UID (should add "1" at the end of the UID)
    xpath = '/cpacs/vehicles/aircraft/model/name'
    new_uid = 'SimpleFuselage'
    cpsf.add_uid(tixi,xpath,new_uid)
    added_uid = tixi.getTextAttribute(xpath, 'uID')

    assert added_uid == 'SimpleFuselage1'


def test_get_value():
    """Test the function 'get_value'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    # Check if the correct value (float) is return from an xpath
    xpath = '/cpacs/vehicles/aircraft/model/reference/area'
    value = cpsf.get_value(tixi,xpath)
    assert value == 1.0

    # Check if the correct value (text) is return from an xpath
    xpath = '/cpacs/vehicles/aircraft/model/name'
    value = cpsf.get_value(tixi,xpath)
    assert value == 'Cpacs2Test'

    # Check if boolean are returned from an xpath or default value
    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/testBoolTrue'
    value = cpsf.get_value(tixi,xpath)
    assert value == True

    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/testBoolFalse'
    value = cpsf.get_value(tixi,xpath)
    assert value == False

    # Check if a false xpath raises ValueError
    xpath = '/cpacs/vehicles/aircraft/model/reference/aarreeaa'
    with pytest.raises(ValueError):
        value_error = cpsf.get_value(tixi,xpath)

    # Check if no value in the field raises ValueError
    xpath = '/cpacs/vehicles/aircraft/model'
    with pytest.raises(ValueError):
        value_text = cpsf.get_value(tixi,xpath)


def test_get_value_or_default():
    """Test the function 'get_value_or_default'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    # Check if the correct value (float) is return from an xpath
    xpath = '/cpacs/vehicles/aircraft/model/reference/area'
    value = cpsf.get_value_or_default(tixi,xpath,2.0)
    assert value == 1.0

    # Check if the correct value (text) is return from an xpath
    xpath = '/cpacs/vehicles/aircraft/model/name'
    value = cpsf.get_value_or_default(tixi,xpath,'name')
    assert value == 'Cpacs2Test'

    # Check if boolean are returned from an xpath or default value
    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/testBoolTrue'
    value = cpsf.get_value_or_default(tixi,xpath,False)
    assert value == True

    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/testBoolFalse'
    value = cpsf.get_value_or_default(tixi,xpath,True)
    assert value == False

    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/notExistTrue'
    value = cpsf.get_value_or_default(tixi,xpath,True)
    assert value == True

    xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/notExistFalse'
    value = cpsf.get_value_or_default(tixi,xpath,False)
    assert value == False

    # Check if a non exitant xpath leads to its creation (integer)
    xpath = '/cpacs/vehicles/aircraft/model/reference/newSpan'
    value = cpsf.get_value_or_default(tixi,xpath,100)
    assert value == 100
    new_elem = tixi.getDoubleElement(xpath)
    assert new_elem == 100

    # Check if a non exitant xpath leads to its creation (float)
    xpath = '/cpacs/vehicles/aircraft/model/reference/newArea'
    value = cpsf.get_value_or_default(tixi,xpath,1000.0)
    assert value == 1000.0
    new_elem = tixi.getDoubleElement(xpath)
    assert new_elem == 1000.0

    # Check if a non exitant xpath leads to its creation (text)
    xpath = '/cpacs/vehicles/aircraft/model/reference/newRef'
    value = cpsf.get_value_or_default(tixi,xpath,'test')
    assert value == 'test'
    new_elem = tixi.getTextElement(xpath)
    assert new_elem =='test'


def test_add_float_vector():
    """ Test the function 'add_float_vector'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)
    xpath = '/cpacs/toolspecific/CEASIOMpy/testVector/'

    # Add a new vector
    float_vector = [0.0, 1.1, 5.5]
    cpsf.add_float_vector(tixi,xpath,float_vector)
    added_float_vector = list(tixi.getFloatVector(xpath,3))

    assert added_float_vector == float_vector

    # Update a vector
    float_vector = [2.9, 10.999, 1e5]
    cpsf.add_float_vector(tixi,xpath,float_vector)
    added_float_vector = list(tixi.getFloatVector(xpath,3))

    assert added_float_vector == float_vector


def test_get_float_vector():
    """ Test the function 'get_float_vector'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)
    xpath = '/cpacs/toolspecific/CEASIOMpy/testVector'

    # Add a new vector
    float_vector = [0.0, 1.1, 5.5]
    cpsf.add_float_vector(tixi,xpath,float_vector)

    # Get a float vector
    float_vector_get = cpsf.get_float_vector(tixi,xpath)

    assert float_vector_get == float_vector

    # Raise an error when the XPath is wrong
    wrong_xpath = '/cpacs/toolspecific/CEASIOMpy/testVectorWrong'
    with pytest.raises(ValueError):
        vector = cpsf.get_float_vector(tixi,wrong_xpath)

    # Raise an error when no value at XPath
    no_value_xpath = '/cpacs/toolspecific/CEASIOMpy'
    with pytest.raises(ValueError):
        vector = cpsf.get_float_vector(tixi,no_value_xpath)


def test_add_sting_vector():
    """ Test the function 'add_sting_vector'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)
    xpath = '/cpacs/toolspecific/CEASIOMpy/testVector/'

    # Add a new vector
    string_vector = ['aaa','bbb','ccc']
    cpsf.add_string_vector(tixi,xpath,string_vector)
    added_sting_vector_str = tixi.getTextElement(xpath)
    added_sting_vector = added_sting_vector_str.split(';')
    added_sting_vector = [str(elem) for elem in added_sting_vector]

    assert added_sting_vector == string_vector

    # Update a vector
    string_vector = ['abc','123','test-01']
    cpsf.add_string_vector(tixi,xpath,string_vector)
    added_sting_vector_str = tixi.getTextElement(xpath)
    added_sting_vector = added_sting_vector_str.split(';')
    added_sting_vector = [str(elem) for elem in added_sting_vector]

    assert added_sting_vector == string_vector


def test_get_string_vector():
    """ Test the function 'get_string_vector'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)
    xpath = '/cpacs/toolspecific/CEASIOMpy/testVector'

    # Add a new vector
    string_vector = ['aaa', 'zzz']
    cpsf.add_string_vector(tixi,xpath,string_vector)

    # Get a string vector
    string_vector_get = cpsf.get_string_vector(tixi,xpath)

    assert string_vector_get == string_vector

    # Raise an error when the XPath is wrong
    wrong_xpath = '/cpacs/toolspecific/CEASIOMpy/testVectorWrong'
    with pytest.raises(ValueError):
        vector = cpsf.get_string_vector(tixi,wrong_xpath)

    # Raise an error when no value at XPath
    no_value_xpath = '/cpacs/toolspecific/CEASIOMpy'
    with pytest.raises(ValueError):
        vector = cpsf.get_string_vector(tixi,no_value_xpath)


def test_get_path():
    """ Test the function 'get_path'"""

    tixi = cpsf.open_tixi(CPACS_IN_PATH)

    linux_xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/linuxPath'
    windows_xpath = '/cpacs/toolspecific/testUtils/testCPACSFunctions/windowsPath'

    linux_path = cpsf.get_path(tixi,linux_xpath)
    windows_path = cpsf.get_path(tixi,windows_xpath)

    path_to_test = os.path.join('usr','test1','test2','mypath')

    assert path_to_test == linux_path
    assert path_to_test == windows_path

    with pytest.raises(ValueError):
        error_xpath1 = '/cpacs/toolspecific/testUtils/testCPACSFunctions/errorPath1'
        path = cpsf.get_path(tixi,error_xpath1)

    with pytest.raises(ValueError):
        error_xpath2 = '/cpacs/toolspecific/testUtils/testCPACSFunctions/errorPath2'
        path = cpsf.get_path(tixi,error_xpath2)


def test_aircraft_name():
    """Test the function 'aircraft_name'"""

    name = cpsf.aircraft_name(CPACS_IN_PATH)
    assert name == 'Cpacs2Test'


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test CPACS Functions')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
    log.info('or')
    log.info('>> pytest -vs  (for more details)')
