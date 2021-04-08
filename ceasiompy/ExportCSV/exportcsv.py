"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to export Aeromap (or other data?) to CSV

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2021-04-07
| Last modifiction: 2021-04-08

TODO:

    * export of other data...
    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import numpy
import matplotlib

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


#==============================================================================
#   CLASSES
#==============================================================================



#==============================================================================
#   FUNCTIONS
#==============================================================================

def export_aeromaps(cpacs_path, cpacs_out_path):

    tixi = cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)

    aeromap_to_export_xpath = '/cpacs/toolspecific/CEASIOMpy/export/aeroMapToExport'

    aeromap_uid_list = []
    aeromap_uid_list = cpsf.get_string_vector(tixi,aeromap_to_export_xpath)

    for aeromap_uid in aeromap_uid_list:

        csv_dir_path = os.path.join(wkdir,'CSVresults')
        if not os.path.isdir(csv_dir_path):
            os.mkdir(csv_dir_path)

        csv_path = os.path.join(csv_dir_path,aeromap_uid+'.csv')

        apmf.aeromap_to_csv(tixi, aeromap_uid, csv_path)

    cpsf.close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + MODULE_NAME + ' -----')

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # Call the function which check if imputs are well define
    mi.check_cpacs_input_requirements(cpacs_path)

    export_aeromaps(cpacs_path, cpacs_out_path)

    log.info('----- End of ' + MODULE_NAME + ' -----')
