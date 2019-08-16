"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to AeroPerformanceMap from CPACS file, it uses TIXI library

Python version: >=3.6
CPACS version: 3.1

| Author : Aidan Jungo
| Creation: 2019-08-15
| Last modifiction: 2019-08-16

TODO:

    * Almost erverything! :)
    * ...

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name

log = get_logger(__file__.split('.')[0])

#APM_PATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/'


#==============================================================================
#   CLASSES
#==============================================================================

class AeroCoefficient():

    def __init__(self):
        self.cl = None
        self.cd = None
        self.cs = None
        self.cml = None
        self.cmd = None
        self.cms = None

#==============================================================================
#   FUNCTIONS
#==============================================================================

def check_aeroPerfomanceMap(tixi, aeromap_uid):
    """ Check existance and validity of an aeroPerformanceMap

    Function 'check_aeroPerfomanceMap' ....

    Source :
        * TIXI functions: http://tixi.sourceforge.net/Doc/index.html
        * CPACS documentation: https://www.cpacs.de/pages/documentation.html

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap to check
    Returns::
        check_ok (boolean): ... # useful?
    """

    check_ok = True

    log.info('TODO')

    return check_ok


def save_aero_coef(tixi,apm_xpath,Coef):
    """ Get aerodynamic coefficients from SU2 resutls

    Function 'get_su2_aero_coef' ....TODO

    Source :
        * ...CPACS Documentation?

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        apm_xpath (str): XPath to the aeroMap to fill
        Coef (object): Object containing aerodynamic coefficients

    Returns::
        tixi (handles): Modified Handle of the CPACS file
    """

    create_branch(tixi,apm_xpath+'/cl')
    tixi.updateDoubleElement(apm_xpath+'/cl',Coef.cl,'%g')

    create_branch(tixi,apm_xpath+'/cd')
    tixi.updateDoubleElement(apm_xpath+'/cd',Coef.cd,'%g')

    create_branch(tixi,apm_xpath+'/cs')
    tixi.updateDoubleElement(apm_xpath+'/cs',Coef.cs,'%g')

    create_branch(tixi,apm_xpath+'/cml')
    tixi.updateDoubleElement(apm_xpath+'/cml',Coef.cml,'%g')

    create_branch(tixi,apm_xpath+'/cmd')
    tixi.updateDoubleElement(apm_xpath+'/cmd',Coef.cmd,'%g')

    create_branch(tixi,apm_xpath+'/cms')
    tixi.updateDoubleElement(apm_xpath+'/cms',Coef.cms,'%g')

    return tixi


# def merge_aeroPerfomanceMap(aeromap1_uid,aeromap2_uid,aeromap_new_uid):
    """ Merge two existing aeroPerformanceMap into a new one """

# def add_point(alt,mach,aoa,aos)
    """ Add a calculation point to an existing aeroPerformanceMap """

# def add_points(alt_list,mach_list,aoa_list,aos_list)
    """ Add a calculation point to an existing aeroPerformanceMap """

# def add_coefficient(alt,mach,aoa,aos,cl,cd,cs): ???
    """ Add a calculation point to an existing aeroPerformanceMap """



#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
