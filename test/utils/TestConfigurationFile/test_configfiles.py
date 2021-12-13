"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2021-12-13
| Last modifiction: 2021-12-13
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import pytest

from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================


def test_configfiles():
    """Test the class 'ConfigFile' """
    
    # Test Simple ConfigFile class not from a file
    CONFIG_0 = os.path.join(MODULE_DIR,'config_test0.cfg')
    CONFIG_OUT_0 = os.path.join(MODULE_DIR,'config_test0_out.cfg')

    config0 = ConfigFile()
    config0['TEXT'] = 'text'
    config0['NUMBER'] = 4
    config0['LIST_OF_TEXT'] = ['abc','def','hij']
    config0['LIST_OF_NUM'] = [1,2.71,3.1416]
    
    config0.write_file(CONFIG_OUT_0,overwrite=True)
    
    with open(CONFIG_0, "r") as c, open(CONFIG_OUT_0, "r") as cout:
        assert c.readlines() == cout.readlines()


    # Chech if ValueError is raised when trying read a file with wrong extension
    with pytest.raises(ValueError):
        ConfigFile('config_test0.wrong')
        
    # Chech if ValueError is raised when trying read a non existing file
    with pytest.raises(FileNotFoundError):
        ConfigFile('config_test1000.cfg')
        
    
    # Read a config file modifing it and write it back
    CONFIG_1 = os.path.join(MODULE_DIR,'config_test1.cfg')
    CONFIG_OUT_1 = os.path.join(MODULE_DIR,'config_test1_out.cfg')
    
    config1 = ConfigFile(CONFIG_1)
    config1['NEWLINE'] = 'text'
    config1['VALUE1'] = 4
    
    config1.write_file(CONFIG_OUT_1,overwrite=True)
    
    assert config1['VALUE1'] == 4
    assert config1['LIST'] == ['a', 'b', 'c']
    assert config1['DIFFENT_LIST'] == ['( 1, 1.0 | a )','( 2, 2.0 | b )','( 3, 3.0 | c )']
    assert config1['NEWLINE'] == 'text'
    
    with open(CONFIG_OUT_1, "r") as cout:
        lines = cout.readlines()
        
    assert lines[1] == '% Comment 2\n'
    assert lines[2] == 'VALUE1 = 4\n'
    assert lines[5] == 'LIST = ( a, b, c )\n'
    assert lines[6] == 'DIFFENT_LIST = ( 1, 1.0 | a ); ( 2, 2.0 | b ); ( 3, 3.0 | c )\n'
    assert lines[7] == 'NEWLINE = text\n'
    
    with pytest.raises(FileExistsError):
        config1.write_file(CONFIG_OUT_1,overwrite=False)
        
    CONFIG_2 = os.path.join(MODULE_DIR,'config_test2.cfg')
    
    with pytest.raises(ValueError):
        config2 = ConfigFile(CONFIG_2)
    
    # Remove output files
    if os.path.isfile(CONFIG_OUT_0):
        os.remove(CONFIG_OUT_0)
    
    if os.path.isfile(CONFIG_OUT_1):
        os.remove(CONFIG_OUT_1)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Test configfile.py')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
