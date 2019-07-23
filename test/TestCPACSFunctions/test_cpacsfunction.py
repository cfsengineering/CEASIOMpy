"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test all the function for 'lib/utils/cpacsfunctions.py'

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-02
    Last modifiction: 2019-07-17

    TODO:  -
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import unittest

from lib.utils.ceasiomlogger import get_logger
from lib.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi, \
                                     get_value, get_value_or_default,  \
                                     create_branch, copy_branch

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


class TixiFunction(unittest.TestCase):
    """
    Unit test of Tixi Function from the module 'cpacsfunctions.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_open_tixi        Test the function 'open_tixi'
    test_wing_nb          Test if the number of wing is equal to 1
    test_fuse_nb          Test if the number of fuselage is equal to 1
    test_close_tixi       Test the function 'close_tixi'
    test_create_branch    Test the function 'create_branch'
    test_copy_branch      Test the function 'copy_branch'
    """

    # Default CPACS file to test
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    CPACS_IN_PATH = MODULE_DIR + '/ToolInput/simpletest_cpacs.xml'
    CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    def test_open_tixi(self):
        """Test the function 'open_tixi'"""

        tixi_handle = open_tixi(self.CPACS_IN_PATH)
        self.assertIsNotNone(tixi_handle)

    def test_wing_nb(self):
        '''Test if the number of wing is equal to 1'''

        tixi_handle = open_tixi(self.CPACS_IN_PATH)
        wing_nb = tixi_handle.getNamedChildrenCount('/cpacs/vehicles/aircraft\
                  /model/wings', 'wing')
        self.assertEqual(wing_nb, 1)

    def test_fuse_nb(self):
        '''Test if the number of fuselage is equal to 1'''

        tixi_handle = open_tixi(self.CPACS_IN_PATH)
        fuse_nb = tixi_handle.getNamedChildrenCount('/cpacs/vehicles/aircraft\
                  /model/fuselages', 'fuselage')
        self.assertEqual(fuse_nb, 1)

    def test_close_tixi(self):
        """Test the function 'close_tixi'"""

        tixi_handle = open_tixi(self.CPACS_IN_PATH)

        # Save unmodified tixi in the output CPACS file
        close_tixi(tixi_handle, self.CPACS_OUT_PATH)

        # Read Input and Ouput CPACS file as text, to compare them
        with open(self.CPACS_IN_PATH) as file_in:
            lines_cpacs_in = file_in.readlines()
        with open(self.CPACS_OUT_PATH) as file_out:
            lines_cpacs_out = file_out.readlines()

        self.assertEqual(lines_cpacs_in, lines_cpacs_out)

    def test_create_branch(self):
        """Test the function 'create_branch'"""

        tixi_handle = open_tixi(self.CPACS_IN_PATH)

        update_branch = '/cpacs/header/updates/update'
        new_branch = '/cpacs/header/updates/update[3]/test/test1/test2'

        # This branch should be added
        tixi = create_branch(tixi_handle, update_branch, True)
        # This branch should not be added
        tixi = create_branch(tixi, update_branch, False)
        # 'new_branch' should be added
        tixi = create_branch(tixi, new_branch)

        # Save modified tixi in the output CPACS file
        close_tixi(tixi, self.CPACS_OUT_PATH)

        # Reopen the output CPACS file to check if branches have been added
        tixi_out = open_tixi(self.CPACS_OUT_PATH)

        # Check if the number of "update" child is equal to 3
        namedchild_nb = tixi_out.getNamedChildrenCount('/cpacs/header/updates',
                                                       'update')
        self.assertEqual(namedchild_nb, 3)

        # Check if 'new_branch' has been added
        branch_check = tixi_out.checkElement(new_branch)
        self.assertEqual(branch_check, True)

    def test_copy_branch(self):
        """Test the function 'copy_branch'"""

        tixi_handle = open_tixi(self.CPACS_IN_PATH)

        # Create a new 'header' branch and copy the original 'header' into it
        xpath_new = '/cpacs/header'
        xpath_from = '/cpacs/header[1]'
        xpath_to = '/cpacs/header[2]'
        tixi = create_branch(tixi_handle, xpath_new, True)
        tixi = copy_branch(tixi, xpath_from, xpath_to)

        # Check if a specific element has been copied
        xpath_elem_from = '/cpacs/header[1]/updates/update[1]/timestamp'
        xpath_elem_to = '/cpacs/header[2]/updates/update[1]/timestamp'
        elem_from = tixi_handle.getTextElement(xpath_elem_from)
        elem_to = tixi.getTextElement(xpath_elem_to)
        self.assertEqual(elem_from, elem_to)

        # Check if a specific attribute has been copied
        attrib_text_from = tixi_handle.getTextAttribute(xpath_elem_from, 'uID')
        attrib_text_to = tixi.getTextAttribute(xpath_elem_to, 'uID')
        self.assertEqual(attrib_text_from, attrib_text_to)

    def test_get_value(self):
        """Test the function 'get_value'"""

        tixi = open_tixi(self.CPACS_IN_PATH)

        # Check if the correct value (float) is return from an xpath
        xpath = '/cpacs/vehicles/aircraft/model/reference/area'
        value = get_value(tixi,xpath)
        self.assertEqual(value,1.0)

        # Check if the correct value (text) is return from an xpath
        xpath = '/cpacs/vehicles/aircraft/model/name'
        value = get_value(tixi,xpath)
        self.assertEqual(value,'Cpacs2Test')

        # Check if a false xpath raises ValueError
        xpath = '/cpacs/vehicles/aircraft/model/reference/aarreeaa'
        with self.assertRaises(ValueError):
            value_error = get_value(tixi,xpath)

        # Check if no value in the field raises ValueError
        xpath = '/cpacs/vehicles/aircraft/model'
        with self.assertRaises(ValueError):
            value_text = get_value(tixi,xpath)

    def test_get_value_or_default(self):
        """Test the function 'get_value_or_default'"""

        tixi = open_tixi(self.CPACS_IN_PATH)

        # Check if the correct value (float) is return from an xpath
        xpath = '/cpacs/vehicles/aircraft/model/reference/area'
        tixi, value = get_value_or_default(tixi,xpath,2.0)
        self.assertEqual(value,1.0)

        # Check if the correct value (text) is return from an xpath
        xpath = '/cpacs/vehicles/aircraft/model/name'
        tixi, value = get_value_or_default(tixi,xpath,'name')
        self.assertEqual(value,'Cpacs2Test')

        # Check if a non exitant xpath leads to its creation (integer)
        xpath = '/cpacs/vehicles/aircraft/model/reference/newSpan'
        tixi, value = get_value_or_default(tixi,xpath,100)
        self.assertEqual(value,100)
        new_elem = tixi.getDoubleElement(xpath)
        self.assertEqual(new_elem,100)

        # Check if a non exitant xpath leads to its creation (float)
        xpath = '/cpacs/vehicles/aircraft/model/reference/newArea'
        tixi, value = get_value_or_default(tixi,xpath,1000.0)
        self.assertEqual(value,1000.0)
        new_elem = tixi.getDoubleElement(xpath)
        self.assertEqual(new_elem,1000.0)

        # Check if a non exitant xpath leads to its creation (text)
        xpath = '/cpacs/vehicles/aircraft/model/reference/newRef'
        tixi, value = get_value_or_default(tixi,xpath,'test')
        self.assertEqual(value,'test')
        new_elem = tixi.getTextElement(xpath)
        self.assertEqual(new_elem,'test')


class TiglFunction(unittest.TestCase):
    """
    Unit test of TIGL functions from the module 'cpacsfunctions.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_open_tigl        Test the function 'open_tigl'
    """

    # Default CPACS file to test
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    CPACS_IN_PATH = MODULE_DIR + '/ToolInput/simpletest_cpacs.xml'
    CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    def test_open_tigl(self):
        """Test the function 'open_tigl'"""

        tixi_handle = open_tixi(self.CPACS_IN_PATH)
        tigl_handle = open_tigl(tixi_handle)

        self.assertIsNotNone(tigl_handle)


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test CPACS Functions')
    unittest.main()


# Other temporary test

    # MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    # CPACS_IN_PATH = MODULE_DIR + '/ToolInput/simpletest_cpacs.xml'
    # CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'
    #
    # tixi_handle = open_tixi(CPACS_IN_PATH)
    #
    # xpath = '/cpacs/header/...'
    #
    # tixi= ...
    #
    # close_tixi(tixi,CPACS_OUT_PATH)
