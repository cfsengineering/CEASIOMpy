"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to handle AeroPerformanceMap from CPACS file, it uses TIXI library

Python version: >=3.6
CPACS version: 3.1

| Author : Aidan Jungo
| Creation: 2019-08-15
| Last modifiction: 2019-08-28

TODO:

    * Create test functions
    * Developp other functions
    * This script is still in developpment, function are not completly working

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import time

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector, get_float_vector, \
                                           add_string_vector, get_string_vector

log = get_logger(__file__.split('.')[0])

AEROPERFORMANCE_XPATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance'

#==============================================================================
#   CLASSES
#==============================================================================

class AeroCoefficient():

#TODO: add name and description ????
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
        # TODO: this function could be improved

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

        if not (cl_len == cd_len == cs_len):
            # raise ValueError('Proebleme with the lenght of the coefficient list')
            log.warning('Proeblem with the lenght of the coefficient list')
        elif cl_len != alt_len:
            log.warning('Not the same number of parameter and coerfficients')
        else:
            log.info('Lenght of the coefficient list: ' + str(alt_len))

        cml_len = len(self.cml)
        cmd_len = len(self.cmd)
        cms_len = len(self.cms)

        if  not (cml_len == cmd_len == cms_len):
            # raise ValueError('Proebleme with the lenght of the moment coefficient list')
            log.warning('Proebleme with the lenght of the moment coefficient list')
        elif cml_len != alt_len:
            log.warning('Not the same number of parameter and moment coerfficients')
        else:
            log.info('Lenght of the moment coefficient list: ' + str(alt_len))

        return alt_len

    def print_coef_list(self):

        case_count = self.get_count()

        print('======================================================================================')
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
        print('======================================================================================')

    # def complete_apm():  ???
    #    """ fill the aeroPerformanceMap with None value to have same lenght for all coefficients

    # def_get_number_of_unique_value
    #     #Could be useful

#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_aeromap_uid_list(tixi):
    """ Get the list of all aeroMap UID.

    Function 'get_aeromap_uid_list' looks for all aerMap in the CPACS file and
    create a list of their UID which is returned.

    Args:
        tixi (handles): TIXI Handle of the CPACS file

    Returns::
        aeromap_list (list): List (of string) of all aeroMap
    """

    aeromap_list = []

    aeromap_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')
    if aeromap_count:
        log.info('There are : ' + str(aeromap_count) + ' aeroMap in this CPACS file: ')
        for i in range(aeromap_count):
            aeromap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(i+1) + ']'
            aeromap_uid = tixi.getTextAttribute(aeromap_xpath, 'uID')
            aeromap_list.append(aeromap_uid)
            log.info('- ' + aeromap_uid)
    else:
        log.warning('No "aeroMap" has been found in the CPACS file')
        log.warning('An empty list will be returned!')

    return aeromap_list


def create_empty_aeromap(tixi, aeromap_uid, description = ''):
    """ Create an empty aeroPerformanceMap

    Function 'create_empty_apm' will add all the required nodes for a new
    aeroPerformanceMap, no value will be sored but function like '????' and
    '???' could be used to fill it then.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroPerformanceMap to create
        description (str): description of the aeroPerformanceMap to create

    """

    if tixi.uIDCheckExists(aeromap_uid):
        log.warning('This UID already exits!')
        aeromap_uid = aeromap_uid + '_bis'
        log.warning(' The following UID will be used instead: ' + aeromap_uid )
    else:
        log.info('This UID does not exit yet.')

    # Add the /aeroMap node, or a new child is already exists
    create_branch(tixi,AEROPERFORMANCE_XPATH + '/aeroMap',True)
    am_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')
    aeromap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(am_count) + ']'

    # Add UID and sub nodes
    add_uid(tixi, aeromap_xpath, aeromap_uid)
    tixi.addTextElement(aeromap_xpath, 'name', aeromap_uid)
    tixi.addTextElement(aeromap_xpath, 'description', description)
    apm_bc_xpath = aeromap_xpath + '/boundaryConditions'
    create_branch(tixi, apm_bc_xpath)
    tixi.addTextElement(apm_bc_xpath,'atmosphericModel','ISA')

    # Add /AeroPerformanceMap and sub nodes
    apm_xpath = aeromap_xpath + '/aeroPerformanceMap'
    create_branch(tixi,apm_xpath)
    create_branch(tixi,apm_xpath+'/altitude')
    create_branch(tixi,apm_xpath+'/machNumber')
    create_branch(tixi,apm_xpath+'/angleOfAttack')
    create_branch(tixi,apm_xpath+'/angleOfSideslip')
    create_branch(tixi,apm_xpath+'/cl')
    create_branch(tixi,apm_xpath+'/cd')
    create_branch(tixi,apm_xpath+'/cs')
    create_branch(tixi,apm_xpath+'/cml')
    create_branch(tixi,apm_xpath+'/cmd')
    create_branch(tixi,apm_xpath+'/cms')


def check_apm(tixi, aeromap_uid):
    """ Check an aeroMap and add missing nodes

    Function 'check_apm' is similar to 'create_empty_aeromap' but for existing
    aeroMap. It will that all node exist and create the missing ones.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroPerformanceMap to create

    """

    seconds = time.time()
    local_time = time.ctime(seconds)

    # If this aeroMap UID did not exist a new one will be create
    if not tixi.uIDCheckExists(aeromap_uid):
        log.warning(aeromap_uid + ' aeroMap has not been found!')
        log.warning('An empty one will be created')
        description = 'AeroMap created by CEASIOMpy ' + str(local_time)
        create_empty_aeromap(tixi, aeromap_uid,description)
    else:
        aeromap_xpath = tixi.uIDGetXPath(aeromap_uid)
        log.info('The aeroMap to check as been found')

        # Check name, description and boundary conditions
        get_value_or_default(tixi,aeromap_xpath+'/name', aeromap_uid)
        description = 'AeroMap checked and utdated by CEASIOMpy ' + str(local_time)
        get_value_or_default(tixi,aeromap_xpath+'/description', description)
        aeromap_bc_xpath = aeromap_xpath + '/boundaryConditions'
        create_branch(tixi,aeromap_bc_xpath)
        get_value_or_default(tixi,aeromap_bc_xpath+'/atmosphericModel', 'ISA')

        # Check AeroPerformanceMap, parameters and coefficients nodes
        apm_xpath = aeromap_xpath + '/aeroPerformanceMap'
        create_branch(tixi,apm_xpath)
        create_branch(tixi,apm_xpath+'/altitude')
        create_branch(tixi,apm_xpath+'/machNumber')
        create_branch(tixi,apm_xpath+'/angleOfAttack')
        create_branch(tixi,apm_xpath+'/angleOfSideslip')
        create_branch(tixi,apm_xpath+'/cl')
        create_branch(tixi,apm_xpath+'/cd')
        create_branch(tixi,apm_xpath+'/cs')
        create_branch(tixi,apm_xpath+'/cml')
        create_branch(tixi,apm_xpath+'/cmd')
        create_branch(tixi,apm_xpath+'/cms')


# TODO: from here, function to re-write  or improve >>>>>>>>>>>>>>>>>>>>>
# Could be improved
def save_parameters(tixi,aeromap_uid,Param):
    """ Save aerodynamic parameter in an aeroMap

    Function 'save_parameters' will save parameters (alt,mach,aoa,aos) into an
    aeroMap ...
    TODO: create it if not exist ???

    Source :
        * ...CPACS Documentation?

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap used to save parameters
        Param (object): Object containing aerodynamic parameters (alt,mach,aoa,aos)

    """

    apm_xpath = tixi.uIDGetXPath(aeromap_uid) + '/aeroPerformanceMap'

    # Check if the number of parameters in Param is OK
    Param.get_count()

    # Add parameters to the aeroPerformanceMap
    add_float_vector(tixi,apm_xpath+'/altitude',Param.alt)
    add_float_vector(tixi,apm_xpath+'/machNumber',Param.mach)
    add_float_vector(tixi,apm_xpath+'/angleOfAttack',Param.aoa)
    add_float_vector(tixi,apm_xpath+'/angleOfSideslip',Param.aos)

# Could be improved
def save_coefficients(tixi,aeromap_uid,Coef):
    """ Save aerodynamic coefficients in an aeroMap

    Function 'save_coefficients' will save aerodynamic coefficients into an
    aeroMap ...
    TODO: create it if not exist ???

    Source :
        * ...CPACS Documentation?

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap used to save coefficients
        Coef (object): Object containing aerodynamic coefficients

    """

    apm_xpath = tixi.uIDGetXPath(aeromap_uid) + '/aeroPerformanceMap'

    param_count = Coef.get_count()

    # CL coefficients
    if len(Coef.cl) == 0:
        log.warning('No "cl" value have been found, this node will stay empty')
    elif len(Coef.cl) == param_count:
        add_float_vector(tixi,apm_xpath+'/cl',Coef.cl)
        log.info('"cl" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cl" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # CD coefficients
    if len(Coef.cd) == 0:
        log.warning('No "cd" value have been found, this node will stay empty')
    elif len(Coef.cd) == param_count:
        add_float_vector(tixi,apm_xpath+'/cd',Coef.cd)
        log.info('"cd" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cd" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # CS coefficients
    if len(Coef.cs) == 0:
        log.warning('No "cs" value have been found, this node will stay empty')
    elif len(Coef.cs) == param_count:
        add_float_vector(tixi,apm_xpath+'/cs',Coef.cs)
        log.info('"cs" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cs" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # Cml coefficients
    if len(Coef.cml) == 0:
        log.warning('No "cml" value have been found, this node will stay empty')
    elif len(Coef.cml) == param_count:
        add_float_vector(tixi,apm_xpath+'/cml',Coef.cml)
        log.info('"cml" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cml" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # CD coefficients
    if len(Coef.cmd) == 0:
        log.warning('No "cmd" value have been found, this node will stay empty')
    elif len(Coef.cmd) == param_count:
        add_float_vector(tixi,apm_xpath+'/cmd',Coef.cmd)
        log.info('"cmd" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cmd" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # CS coefficients
    if len(Coef.cms) == 0:
        log.warning('No "cms" value have been found, this node will stay empty')
    elif len(Coef.cms) == param_count:
        add_float_vector(tixi,apm_xpath+'/cms',Coef.cs)
        log.info('"cms" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cms" values is incorrect, it must \
        either equal to the number of parameters or 0')


def get_aeromap(tixi,aeromap_uid):
    """ Get aerodynamic parameters and coefficients from an aeroMap

    Function 'get_aeromap' return an object 'AeroCoefficient' fill with the
    values found in the given aeroMap. Parameters are required but if a
    coefficients is not found, an empty list will be return in the corresponding
    node.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap to get

    Returns::
        Coef (object): Object containing parameters and aerodynamic coefficients from the aeroMap
    """

    apm_xpath = tixi.uIDGetXPath(aeromap_uid) + '/aeroPerformanceMap'

    Coef = AeroCoefficient()

    Coef.alt = get_float_vector(tixi,apm_xpath +'/altitude')
    Coef.mach  = get_float_vector(tixi,apm_xpath +'/machNumber')
    Coef.aoa = get_float_vector(tixi,apm_xpath +'/angleOfAttack')
    Coef.aos = get_float_vector(tixi,apm_xpath +'/angleOfSideslip')

    if tixi.checkElement(apm_xpath +'/cl'):
        Coef.cl = get_float_vector(tixi,apm_xpath +'/cl')
    if tixi.checkElement(apm_xpath +'/cd'):
        Coef.cd = get_float_vector(tixi,apm_xpath +'/cd')
    if tixi.checkElement(apm_xpath +'/cs'):
        Coef.cs = get_float_vector(tixi,apm_xpath +'/cs')
    if tixi.checkElement(apm_xpath +'/cml'):
        Coef.cml = get_float_vector(tixi,apm_xpath +'/cml')
    if tixi.checkElement(apm_xpath +'/cmd'):
        Coef.cmd = get_float_vector(tixi,apm_xpath +'/cmd')
    if tixi.checkElement(apm_xpath +'/cms'):
        Coef.cms = get_float_vector(tixi,apm_xpath +'/cms')

    return Coef





def merge_aeroPerfomanceMap(aeromap_uid_1,aeromap_uid_2,aeromap_uid_merge, delete = False):
    """ Merge two existing aeroPerformanceMap into a new one

    Function 'merge_aeroPerfomanceMap' merge two aeroMap into one, an option
    allow to keep or not the orignal ones.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid_1 (str): UID of the first aeroMap to merge
        aeromap_uid_2 (str): UID of the second aeroMap to merge
        aeromap_uid_merge (str): UID of the merged aeroMap
        delete (boolean): Delete orignal aeroMap

    """
    pass

    #TODO

def convert_coefficients():
    """ Convert aerodynamic coefficients from fix frame to aircraft frame """


# def add_points(alt_list,mach_list,aoa_list,aos_list)
    """ Add a calculation point to an existing aeroPerformanceMap """

# def "print_param_list" something like a csv file...?
    #  altitude     machNumber      angleOfAttack   angleOfSideslip
    #  1200         0.78            2.0             0.0

# def export_apm_to_csv(tixi, aeromap_uid, csv_path):


# def create_apm_from_csv(tixi, csv_path):


# def "print_coef_list" something like a csv file...? same with coef
    #  altitude     machNumber      angleOfAttack   angleOfSideslip     CL  CD ...
    #  1200         0.78            2.0             0.0

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
