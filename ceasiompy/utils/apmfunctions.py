"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to handle aeroMaps from CPACS file, it uses TIXI library

Python version: >=3.6
CPACS version: 3.1

| Author : Aidan Jungo
| Creation: 2019-08-15
| Last modifiction: 2019-09-05

TODO:

    * Create test functions
    * Developp other functions
    * Use DataFrame instead of AeroCoefficient object? is it possible?
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import time
import math

import pandas as pd

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch, copy_branch, add_uid,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector, get_float_vector, \
                                           add_string_vector,get_string_vector


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

    def add_coefficients(self,cl,cd,cs,cml,cmd,cms):

        self.cl.append(cl)
        self.cd.append(cd)
        self.cs.append(cs)
        self.cml.append(cml)
        self.cmd.append(cmd)
        self.cms.append(cms)

    def check_validity(self):
        # TODO: this function could  probalby be simplified

        if  not (len(self.alt) == len(self.mach) == len(self.aoa) == len(self.aos)):
            raise ValueError('Not all parameter lists have the same lenght!')

        if any([math.isnan(a) for a in self.alt]):
            raise ValueError('Parameter "alt" containts "NaN"!')
        if any([math.isnan(a) for a in self.mach]):
            raise ValueError('Parameter "mach" containts "NaN"!')
        if any([math.isnan(a) for a in self.aoa]):
            raise ValueError('Parameter "aoa" containts "NaN"!')
        if any([math.isnan(a) for a in self.aos]):
            raise ValueError('Parameter "aos" containts "NaN"!')

        if not (len(self.cl) == len(self.cd) == len(self.cs)):
            # raise ValueError('Proebleme with the lenght of the coefficient list')
            log.warning('Proeblem with the lenght of the coefficient list')
        elif len(self.cl) != len(self.alt):
            log.warning('Not the same number of parameter and coerfficients')
        else:
            log.info('Lenght of the coefficient list: ' + str(len(self.alt)))

        if  not (len(self.cml) == len(self.cmd) == len(self.cms)):
            # raise ValueError('Proebleme with the lenght of the moment coefficient list')
            log.warning('Proebleme with the lenght of the moment coefficient list')
        elif len(self.cml) != len(self.alt):
            log.warning('Not the same number of parameter and moment coerfficients')
        else:
            log.info('Lenght of the moment coefficient list: ' + str(len(self.alt)))


    def get_count(self):
        """ get the number of parameters"""

        # Check validity first
        self.check_validity()

        # Get lenght of altitude list (should be the same if check_validity passes)
        alt_len = len(self.alt)

        return alt_len

    def complete_with_zeros(self):
        """ fill resuts vecotor (coefficient) with zero to avoid error when plot"""

        case_count = self.get_count()

        if self.cl == []:
            self.cl = [0]*case_count
            log.warning('No "cl" values have been found, a list of zeros will be used instead')
        if self.cd == []:
            self.cd = [0]*case_count
            log.warning('No "cd" values have been found, a list of zeros will be used instead')
        if self.cs == []:
            self.cs = [0]*case_count
            log.warning('No "cs" values have been found, a list of zeros will be used instead')
        if self.cml == []:
            self.cml = [0]*case_count
            log.warning('No "cml" values have been found, a list of zeros will be used instead')
        if self.cmd == []:
            self.cmd = [0]*case_count
            log.warning('No "cmd" values have been found, a list of zeros will be used instead')
        if self.cms == []:
            self.cms = [0]*case_count
            log.warning('No "cms" values have been found, a list of zeros will be used instead')


    def sort_by_key(self,sort_key):
        """ sort the data in AeroCoefficient object by the 'sort_key' """

        # Create a dictionary from data
        dict = {'alt':self.alt,
                'mach': self.mach,
                'aoa':self.aoa,
                'aos':self.aos,
                'cl':self.cl,
                'cd':self.cd,
                'cs':self.cs,
                'cml':self.cml,
                'cmd':self.cmd,
                'cms':self.cms}

        # Create a dataframe from dictionary
        df = pd.DataFrame(dict)
        # Sort the dataframe with the given key
        df_sorted = df.sort_values(sort_key)

        # Put back the data in the AeroCoefficient object
        self.alt = df_sorted['alt'].tolist()
        self.mach = df_sorted['mach'].tolist()
        self.aoa = df_sorted['aoa'].tolist()
        self.aos = df_sorted['aos'].tolist()

        self.cl = df_sorted['cl'].tolist()
        self.cd = df_sorted['cd'].tolist()
        self.cs = df_sorted['cs'].tolist()

        self.cml = df_sorted['cml'].tolist()
        self.cmd = df_sorted['cmd'].tolist()
        self.cms = df_sorted['cms'].tolist()


    def print_coef_list(self):

        case_count = self.get_count()

        print('======================================================================================')
        print('#\talt\tmach\taoa\taos\tcl\tcd\tcs\tcml\tcmd\tcms')

        for i in range(case_count):
            alt = str(int(self.alt[i]))
            mach = str(self.mach[i])
            aoa = str(self.aoa[i])
            aos =  str(self.aos[i])
            cl = str(round(self.cl[i],5))
            cd = str(round(self.cd[i],5))
            cs = str(round(self.cs[i],5))
            cml = str(round(self.cml[i],5))
            cmd = str(round(self.cmd[i],5))
            cms = str(round(self.cms[i],5))

            print(str(i) +'\t'+ alt +'\t'+ mach +'\t'+ aoa +'\t'+ aos +'\t'+  \
                  cl + '\t' + cd + '\t' + cs + '\t' +
                  cml + '\t' + cmd + '\t' + cms)
        print('======================================================================================')


    # def_get_number_of_unique_value
    #     #Could be useful
    #     # of "self.get_unique_value('aoa',2.0) should return all aoa == 2.0"


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

    if not tixi.checkElement(AEROPERFORMANCE_XPATH):
        return aeromap_list

    aeromap_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')
    if aeromap_count:
        log.info('There are : ' + str(aeromap_count) + ' aeroMap in this CPACS file: ')
        for i in range(aeromap_count):
            aeromap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(i+1) + ']'
            aeromap_uid = tixi.getTextAttribute(aeromap_xpath, 'uID')
            aeromap_list.append(aeromap_uid)
            log.info(aeromap_uid)
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


def check_aeromap(tixi, aeromap_uid):
    """ Check an aeroMap and add missing nodes

    Function 'check_aeromap' is similar to 'create_empty_aeromap' but for existing
    aeroMap. It will make sur that all node exist and create the missing ones.

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


# TODO: Could be improved
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

    # Check if the vality of parameters is OK
    Param.check_validity()

    # Add parameters to the aeroPerformanceMap
    add_float_vector(tixi,apm_xpath+'/altitude',Param.alt)
    add_float_vector(tixi,apm_xpath+'/machNumber',Param.mach)
    add_float_vector(tixi,apm_xpath+'/angleOfAttack',Param.aoa)
    add_float_vector(tixi,apm_xpath+'/angleOfSideslip',Param.aos)


# TODO: Could be improved
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

    # Cmd coefficients
    if len(Coef.cmd) == 0:
        log.warning('No "cmd" value have been found, this node will stay empty')
    elif len(Coef.cmd) == param_count:
        add_float_vector(tixi,apm_xpath+'/cmd',Coef.cmd)
        log.info('"cmd" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cmd" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # Cms coefficients
    if len(Coef.cms) == 0:
        log.warning('No "cms" value have been found, this node will stay empty')
    elif len(Coef.cms) == param_count:
        add_float_vector(tixi,apm_xpath+'/cms',Coef.cms)
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

    cl_xpath = apm_xpath +'/cl'
    if tixi.checkElement(cl_xpath):
        check_str = tixi.getTextElement(cl_xpath)
        if check_str == '':
            log.warning('No /cl values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cl = []
        else:
            Coef.cl = get_float_vector(tixi,cl_xpath)

    cd_xpath = apm_xpath +'/cd'
    if tixi.checkElement(cd_xpath):
        check_str = tixi.getTextElement(cd_xpath)
        if check_str == '':
            log.warning('No /cd values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cd = []
        else:
            Coef.cd = get_float_vector(tixi,cd_xpath)

    cs_xpath = apm_xpath +'/cs'
    if tixi.checkElement(cs_xpath):
        check_str = tixi.getTextElement(cs_xpath)
        if check_str == '':
            log.warning('No /cs values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cs = []
        else:
            Coef.cs = get_float_vector(tixi,cs_xpath)

    cml_xpath = apm_xpath +'/cml'
    if tixi.checkElement(cml_xpath):
        check_str = tixi.getTextElement(cml_xpath)
        if check_str == '':
            log.warning('No /cml values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cml = []
        else:
            Coef.cml = get_float_vector(tixi,cml_xpath)

    cmd_xpath = apm_xpath +'/cmd'
    if tixi.checkElement(cmd_xpath):
        check_str = tixi.getTextElement(cmd_xpath)
        if check_str == '':
            log.warning('No /cmd values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cmd = []
        else:
            Coef.cmd = get_float_vector(tixi,cmd_xpath)

    cms_xpath = apm_xpath +'/cms'
    if tixi.checkElement(cms_xpath):
        check_str = tixi.getTextElement(cms_xpath)
        if check_str == '':
            log.warning('No /cms values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cms = []
        else:
            Coef.cms = get_float_vector(tixi,cms_xpath)

    return Coef


def merge_aeroMap(tixi, aeromap_uid_1,aeromap_uid_2,aeromap_uid_merge,
                            keep_originals = True):
    """ Merge two existing aeroPerformanceMap into a new one

    Function 'merge_aeroMap' merge two aeroMap into one, an option
    allow to keep or not the orignal ones.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid_1 (str): UID of the first aeroMap to merge
        aeromap_uid_2 (str): UID of the second aeroMap to merge
        aeromap_uid_merge (str): UID of the merged aeroMap
        delete (boolean): Delete orignal aeroMap

    """

    # Check aeroMaps
    check_aeromap(tixi, aeromap_uid_1)
    check_aeromap(tixi, aeromap_uid_2)

    # Create AeroCoefficient objects
    Aero1 = get_aeromap(tixi,aeromap_uid_1)
    Aero2 = get_aeromap(tixi,aeromap_uid_2)

    # Create an empty aeroMap and AeroCoefficient object to recive values
    description = 'This aeroMap is a merge of ' + aeromap_uid_1 + ' and ' + aeromap_uid_2
    create_empty_aeromap(tixi, aeromap_uid_merge, description)
    MergeAero = AeroCoefficient()

    MergeAero.alt = Aero1.alt + Aero2.alt
    MergeAero.mach = Aero1.mach + Aero2.mach
    MergeAero.aoa = Aero1.aoa + Aero2.aoa
    MergeAero.aos = Aero1.aos + Aero2.aos

    MergeAero.cl = Aero1.cl + Aero2.cl
    MergeAero.cd = Aero1.cd + Aero2.cd
    MergeAero.cs = Aero1.cs + Aero2.cs

    MergeAero.cml = Aero1.cml + Aero2.cml
    MergeAero.cmd = Aero1.cmd + Aero2.cmd
    MergeAero.cms = Aero1.cms + Aero2.cms

    MergeAero.sort_by_key('aoa')

    save_parameters(tixi,aeromap_uid_merge,MergeAero)
    save_coefficients(tixi,aeromap_uid_merge,MergeAero)

    if not keep_originals:
        aeroMap_xpath_1 = tixi.uIDGetXPath(aeromap_uid_1)
        tixi.removeElement(aeroMap_xpath_1)
        log.info(aeromap_uid_1 + ' has been removed from the CPACS file')

        aeroMap_xpath_2 = tixi.uIDGetXPath(aeromap_uid_2)
        tixi.removeElement(aeroMap_xpath_2)
        log.info(aeromap_uid_2 + ' has been removed from the CPACS file')


def aeromap_from_csv(tixi,aeromap_uid,csv_path):
    """ Fill an aeroMap from an external CSV file.

    Function 'aeromap_from_csv' will look for a CSV file given at
    'csv_path' check if the data are valid and convert them as an
    AeroCoefficient object, to finally save them into the given TIXI Handle as a
    new aeroMap.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap to create
        csv_path (str): Absolute path the the CSV file

    """

    # Read CSV file
    df = pd.read_csv(csv_path,keep_default_na=False)
    log.info(csv_path + ' has been read.')
    print(df)

    # Create AeroCoefficient object and put data in it
    Aero = AeroCoefficient()

    try:
        Aero.alt = df['alt'].astype(float).tolist()
        Aero.mach = df['mach'].astype(float).tolist()
        Aero.aoa = df['aoa'].astype(float).tolist()
        Aero.aos = df['aos'].astype(float).tolist()
    except:
        raise ValueError('Some parameter lists containt "NaN" value, it is not permited!')

    try:
        Aero.cl = df['cl'].astype(float).tolist()
    except:
        log.warning('No "cl" value have been found in the CPACS file')
    try:
        Aero.cd = df['cd'].astype(float).tolist()
    except:
        log.warning('No "cd" value have been found in the CPACS file')
    try:
        Aero.cs = df['cs'].astype(float).tolist()
    except:
        log.warning('No "cs" value have been found in the CPACS file')
    try:
        Aero.cml = df['cml'].astype(float).tolist()
    except:
        log.warning('No "cml" value have been found in the CPACS file')
    try:
        Aero.cmd = df['cmd'].astype(float).tolist()
    except:
        log.warning('No "cmd" value have been found in the CPACS file')
    try:
        Aero.cms = df['cms'].astype(float).tolist()
    except:
        log.warning('No "cms" value have been found in the CPACS file')

    Aero.check_validity()

    # Create and save the new aeroMap in the TIXI handles
    csv_name = csv_path.split('/')[-1]
    description = 'AeroMap create from the CSV file: ' + csv_name
    create_empty_aeromap(tixi,aeromap_uid, description)
    save_parameters(tixi,aeromap_uid,Aero)
    save_coefficients(tixi,aeromap_uid,Aero)


def aeromap_to_csv(tixi, aeromap_uid, csv_path):
    """ Export an aeroMap into an external CSV file.

    Function 'aeromap_to_csv' will export the aeroMap given by its UID into
    a CSV file given by its path.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap to export
        csv_path (str): Absolute path the the CSV file to create

    """

    # Create an AeroCoefficient object from an aeroMap UID
    AeroCoefficient = get_aeromap(tixi,aeromap_uid)

    # Create a dictionary from the AeroCoefficient object
    dict = {'alt':AeroCoefficient.alt,
            'mach': AeroCoefficient.mach,
            'aoa':AeroCoefficient.aoa,
            'aos':AeroCoefficient.aos,
            'cl':AeroCoefficient.cl,
            'cd':AeroCoefficient.cd,
            'cs':AeroCoefficient.cs,
            'cml':AeroCoefficient.cml,
            'cmd':AeroCoefficient.cmd,
            'cms':AeroCoefficient.cms}

    # Create a DataFrame (pandas) from dictionary
    df = pd.DataFrame(dict)

    # Export the DataFrame to a CSV file
    df.to_csv(csv_path, index=False)


def delete_aeromap(tixi,aeromap_uid):
    """ Delete a given aeroMap by its UID.

    Function 'delete_aeromap' will chcek it the aeroMap exist and then delete it.

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        aeromap_uid (str): UID of the aeroMap to delete

    """

    aeroMap_xpath = tixi.uIDGetXPath(aeromap_uid)

    if not aeroMap_xpath:
        raise ValueError('Aeromap cannot be deleted. This UID does not exist')

    if not any(['aeroMap' in item for item in aeroMap_xpath.split('/')]):
        raise ValueError('This function cannot delete the UID, this is not an aeroMap!')

    tixi.removeElement(aeroMap_xpath)
    log.info(aeromap_uid + ' has been removed from the CPACS file')


# def modity_aeromap_uid(tixi,aeromap_uid, new aeromap_uid):
# modify uid
# modify name
# fing in CPACS where this name is used... ?


# def convert_coefficients():
     # """ Convert aerodynamic coefficients from fix frame to aircraft frame """


# def add_points(alt_list,mach_list,aoa_list,aos_list)
    # """ Add a calculation point to an existing aeroPerformanceMap """


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')


### HOW TO IMPORT THESE MODULE

# from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
#                                          create_empty_aeromap, check_aeromap,  \
#                                          save_parameters, save_coefficients,   \
#                                          get_aeromap, merge_aeroMap,           \
#                                          aeromap_from_csv, aeromap_to_csv,     \
#                                          delete_aeromap
