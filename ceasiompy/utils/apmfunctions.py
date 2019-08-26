"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to AeroPerformanceMap from CPACS file, it uses TIXI library

Python version: >=3.6
CPACS version: 3.1

| Author : Aidan Jungo
| Creation: 2019-08-15
| Last modifiction: 2019-08-23

TODO:

    * Crete test function
    * Developp other functions
    * This script is still in developpment, function are not completly working

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
                                           get_list_values, aircraft_name

log = get_logger(__file__.split('.')[0])

AEROPERFORMANCE_XPATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance'

#==============================================================================
#   CLASSES
#==============================================================================

class AeroCoefficient():

    def __init__(self):

        # Parameters
        self.alt = []
        self.mach = []
        self.aos = []
        self.aoa = []

        # Coefficients
        self.cl = []
        self.cd = []
        self.cs = []
        self.cml = []
        self.cmd = []
        self.cms = []


    def add_param_point(alt,mach,aoa,aos):

        self.alt.append(alt)
        self.mach.append(mach)
        self.aoa.append(aoa)
        self.aos.append(aos)


    def add_coefficients(self,cl,cd,cs,cml,cmd, cms):

        self.cl.append(cl)
        self.cd.append(cd)
        self.cs.append(cs)
        self.cml.append(cml)
        self.cmd.append(cmd)
        self.cms.append(cms)

    def get_count(self):

        alt_len = len(self.alt)
        mach_len = len(self.mach)
        aoa_len = len(self.aoa)
        aos_len = len(self.aos)

        if  not (alt_len == mach_len == aoa_len == aos_len):
            raise ValueError('Proebleme with the lenght of the parameter list')
        else:
            log.info('Lenght of the parameter list: ' + str(alt_len))

        cl_len = len(self.cl)
        cd_len = len(self.cd)
        cs_len = len(self.cs)

        if  not (cl_len == cd_len == cs_len):
            raise ValueError('Proebleme with the lenght of the coefficient list')
        elif cl_len != alt_len:
            log.warning('Not the same number of parameter and coerfficients')
        else:
            log.info('Lenght of the coefficient list: ' + str(alt_len))

        cml_len = len(self.cml)
        cmd_len = len(self.cmd)
        cms_len = len(self.cms)

        if  not (cml_len == cmd_len == cms_len):
            raise ValueError('Proebleme with the lenght of the moment coefficient list')
        elif cml_len != alt_len:
            log.warning('Not the same number of parameter and moment coerfficients')
        else:
            log.info('Lenght of the moment coefficient list: ' + str(alt_len))

        return alt_len


    def print_coef_list(self):

        case_count = self.get_count()

        print('=====================================================================================')
        print('#\talt\tmach\taoa\taos\tcl\tcd\tcs\tcml\tcmd\tcms')

        for i in range(case_count):
            alt = str(int(self.alt[i]))
            mach = str(self.mach[i])
            aoa = str(self.aoa[i])
            aos =  str(self.aos[i])
            cl = str(round(self.cl[i],3))
            cd = str(round(self.cd[i],3))
            cs = str(round(self.cs[i],3))
            cml = str(round(self.cl[i],3))
            cmd = str(round(self.cd[i],3))
            cms = str(round(self.cs[i],3))

            print(str(i) +'\t'+ alt +'\t'+ mach +'\t'+ aoa +'\t'+ aos +'\t'+  \
                  cl + '\t' + cd + '\t' + cs + '\t' +
                  cml + '\t' + cmd + '\t' + cms)
        print('=====================================================================================')


    # def_get_number_of_unique_value
    #     #Could be useful

#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_apm_xpath(tixi,active_aeroMap_xpath):
    """ Get aeroPerformanceMap XPath

    Function 'get_apm_xpath' will retrun the aeroPerformanceMap XPath from the
    XPath which contain its name. More details...

    Source :
        * ...CPACS Documentation?

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        active_aeroMap_xpath (str): XPath to the active aeroMap UID

    """

    # will it raise an error if probleme?
    if not tixi.checkElement(active_aeroMap_xpath):
        raise ValueError('Nothing has been found at: ' + active_aeroMap_xpath)

    aeroMap_uid = get_value(tixi,active_aeroMap_xpath)
    aeroMap_path = tixi.uIDGetXPath(aeroMap_uid)
    apm_xpath = aeroMap_path + '/aeroPerformanceMap'

    return apm_xpath


def create_aeromap_uid_list(tixi):
    """ Create a list of all aeroMap UID.

    Function 'create_aeromap_uid_list' ....TODO

    Source :
        * ...CPACS Documentation

    Args:
        tixi (handles): TIXI Handle of the CPACS file

    Returns::
        aeromap_list (list): List of string of all aeroMap
    """
    aeromap_list = []

    aeromap_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')
    if aeromap_count:
        log.info('There are : ' + str(aeromap_count) + ' in the CPACS file')

        for i in range(aeromap_count):
            aeromap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(i+1) + ']'
            aeromap_uid = tixi.getTextAttribute(aeromap_xpath, 'uID')
            aeromap_list.append(aeromap_uid)
            log.info(aeromap_uid)
    else:
        log.warning('No "aeroMap" has been found in the CPACS file')

    return aeromap_list


def create_empty_apm(tixi, apm_uid, description = ''):
    """ TODO """

    if tixi.uIDCheckExists(apm_uid):
        log.info('New UID does not exit yet')

    create_branch(tixi,AEROPERFORMANCE_XPATH + '/aeroMap',True)
    am_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')

    aeroMap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(am_count) + ']'
    add_uid(tixi, aeroMap_xpath, apm_uid)
    tixi.addTextElement(aeroMap_xpath, 'name', apm_uid)
    tixi.addTextElement(aeroMap_xpath, 'description', description)
    create_branch(tixi,aeroMap_xpath + '/boundaryConditions')
    tixi.addTextElement(aeroMap_xpath+'/boundaryConditions','atmosphericModel','ISA')

    create_branch(tixi,aeroMap_xpath + '/aeroPerformanceMap')


def get_apm(tixi,apm_xpath):
    """ Get aerodynamic parameters and coefficients from an aeroMap

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

    Coef = AeroCoefficient()

    Coef.alt = get_list_values(tixi,apm_xpath +'/altitude')
    Coef.mach  = get_list_values(tixi,apm_xpath +'/machNumber')
    Coef.aoa = get_list_values(tixi,apm_xpath +'/angleOfAttack')
    Coef.aos = get_list_values(tixi,apm_xpath +'/angleOfSideslip')

    Coef.cl = get_list_values(tixi,apm_xpath +'/cl')
    Coef.cd = get_list_values(tixi,apm_xpath +'/cd')
    Coef.cs = get_list_values(tixi,apm_xpath +'/cs')

    Coef.cml = get_list_values(tixi,apm_xpath +'/cml')
    Coef.cmd = get_list_values(tixi,apm_xpath +'/cmd')
    Coef.cms = get_list_values(tixi,apm_xpath +'/cms')

    return Coef


# Maybe combine this function with the next one
def save_param(tixi,apm_xpath,Param):
    """ Save aerodynamic parameter in an aeroMap

    Function 'save_param' ....TODO

    Source :
        * ...CPACS Documentation?

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        apm_xpath (str): XPath to the aeroMap to fill
        Coef (object): Object containing aerodynamic coefficients

    Returns::
        tixi (handles): Modified Handle of the CPACS file
    """

    create_branch(tixi,apm_xpath+'/altitude')
    alt_list_str = ";".join([str(c) for c in Param.alt])
    tixi.updateTextElement(apm_xpath+'/altitude',alt_list_str)

    create_branch(tixi,apm_xpath+'/machNumber')
    mach_list_str = ";".join([str(c) for c in Param.mach])
    tixi.updateTextElement(apm_xpath+'/machNumber',mach_list_str)

    create_branch(tixi,apm_xpath+'/angleOfAttack')
    aoa_list_str = ";".join([str(c) for c in Param.aoa])
    tixi.updateTextElement(apm_xpath+'/angleOfAttack',aoa_list_str)

    create_branch(tixi,apm_xpath+'/angleOfSideslip')
    aos_list_str = ";".join([str(c) for c in Param.aos])
    tixi.updateTextElement(apm_xpath+'/angleOfSideslip',aos_list_str)

    #tixi.addFloatVector(apm_xpath,angleOfSideslip)


def save_aero_coef(tixi,apm_xpath,Coef):
    """ Save aerodynamic coefficients in an aeroMap

    Function 'save_aero_coef' ....TODO

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
    cl_list_str = ";".join([str(round(c,6)) for c in Coef.cl])
    tixi.updateTextElement(apm_xpath+'/cl',cl_list_str)

    create_branch(tixi,apm_xpath+'/cd')
    cd_list_str = ";".join([str(round(c,6)) for c in Coef.cd])
    tixi.updateTextElement(apm_xpath+'/cd',cd_list_str)

    create_branch(tixi,apm_xpath+'/cs')
    cs_list_str = ";".join([str(round(c,6)) for c in Coef.cs])
    tixi.updateTextElement(apm_xpath+'/cs',cs_list_str)

    create_branch(tixi,apm_xpath+'/cml')
    cml_list_str = ";".join([str(round(c,6)) for c in Coef.cml])
    tixi.updateTextElement(apm_xpath+'/cml',cml_list_str)

    create_branch(tixi,apm_xpath+'/cmd')
    cmd_list_str = ";".join([str(round(c,6)) for c in Coef.cmd])
    tixi.updateTextElement(apm_xpath+'/cmd',cmd_list_str)

    create_branch(tixi,apm_xpath+'/cms')
    cms_list_str = ";".join([str(round(c,6)) for c in Coef.cms])
    tixi.updateTextElement(apm_xpath+'/cms',cms_list_str)


# def create_apm_from_csv(tixi, csv_path):

# def merge_aeroPerfomanceMap(aeromap1_uid,aeromap2_uid,aeromap_new_uid):
    """ Merge two existing aeroPerformanceMap into a new one """

# def add_points(alt_list,mach_list,aoa_list,aos_list)
    """ Add a calculation point to an existing aeroPerformanceMap """

# def "print_param_list" something like a csv file...?
    #  altitude     machNumber      angleOfAttack   angleOfSideslip
    #  1200         0.78            2.0             0.0

# def "print_coef_list" something like a csv file...? same with coef
    #  altitude     machNumber      angleOfAttack   angleOfSideslip     CL  CD ...
    #  1200         0.78            2.0             0.0

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
