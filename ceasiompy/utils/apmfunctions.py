"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to handle aeroMaps from CPACS file, it uses TIXI library

Python version: >=3.6
CPACS version: 3.1

| Author : Aidan Jungo
| Creation: 2019-08-15
| Last modifiction: 2020-07-01

TODO:

    * Create test functions
    * Developp other functions
    * Use Penda DataFrame instead of AeroCoefficient object? is it possible?
    * implement "IncrementMap" for damping_der and control_surf
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import time
import math

import numpy as np
import pandas as pd

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.ceasiompyfunctions as ceaf

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

AEROPERFORMANCE_XPATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance'
#==============================================================================
#   CLASSES
#==============================================================================


class DampingDerivative():

    def __init__(self):

        # Damping derivatives Coefficients
        self.dcldpstar = []
        self.dcddpstar = []
        self.dcsdpstar = []
        self.dcmldpstar = []
        self.dcmddpstar = []
        self.dcmsdpstar = []

        self.dcldqstar = []
        self.dcddqstar = []
        self.dcsdqstar = []
        self.dcmldqstar = []
        self.dcmddqstar = []
        self.dcmsdqstar = []

        self.dcldrstar = []
        self.dcddrstar = []
        self.dcsdrstar = []
        self.dcmldrstar = []
        self.dcmddrstar = []
        self.dcmsdrstar = []

    def add_damping_der_coef(self,dcl,dcd,dcs,dcml,dcmd,dcms,rot_axis):

        # The damping derivatives are calculated using rotational rates
        # [rad/s], normalized by: Rate*ReferenceLength/flow speed.
        # The rotations are performed around the global axis directions with
        # the aircraft model's global reference point as origin.

        if rot_axis == '_dp':
            self.dcldpstar.append(dcl)
            self.dcddpstar.append(dcd)
            self.dcsdpstar.append(dcs)
            self.dcmldpstar.append(dcml)
            self.dcmddpstar.append(dcmd)
            self.dcmsdpstar.append(dcms)
        if rot_axis == '_dq':
            self.dcldqstar.append(dcl)
            self.dcddqstar.append(dcd)
            self.dcsdqstar.append(dcs)
            self.dcmldqstar.append(dcml)
            self.dcmddqstar.append(dcmd)
            self.dcmsdqstar.append(dcms)
        if rot_axis == '_dr':
            self.dcldrstar.append(dcl)
            self.dcddrstar.append(dcd)
            self.dcsdrstar.append(dcs)
            self.dcmldrstar.append(dcml)
            self.dcmddrstar.append(dcmd)
            self.dcmsdrstar.append(dcms)


class IncrementMap():

    def __init__(self,ted_uid):
        self.cs_list = 0

        self.ted_uid = ted_uid
        self.control_parameter = 0

        self.dcl = []
        self.dcd = []
        self.dcs = []
        self.dcml = []
        self.dcmd = []
        self.dcms = []

    def add_cs_coef(self,dcl,dcd,dcs,dcml,dcmd,dcms,ted_uid,control_parameter):
        self.cs_list += 1
        self.control_parameter = control_parameter

        self.dcl.append(dcl)
        self.dcd.append(dcd)
        self.dcs.append(dcs)
        self.dcml.append(dcml)
        self.dcmd.append(dcmd)
        self.dcms.append(dcms)

    # TODO: how ?
    # <incrementMaps>
    #     <incrementMap uID="incMap_b3ac2">
    #         <controlSurfaceUID>InnerWingFlap</controlSurfaceUID>
    #         <controlParameters mapType="vector">-1;-0.5;0;1</controlParameters>
    #         <dcl mapType="array">11.; 12.; 13.; 14.; 15.; 21.; 22.; 23.; 24.; 25.; 31.; 32.; 33.; 34.; 35.</dcl>



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

        self.damping_derivatives = DampingDerivative()

        #self.increment_map = IncrementMap()

    def add_param_point(self,alt,mach,aoa,aos):

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
        dict = self.to_dict(self)

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

    def to_dict(self):
        dct = {'alt':self.alt,
        'mach': self.mach,
        'aoa':self.aoa,
        'aos':self.aos,
        'cl':self.cl,
        'cd':self.cd,
        'cs':self.cs,
        'cml':self.cml,
        'cmd':self.cmd,
        'cms':self.cms}
        return dct

    def print_coef_list(self):

        case_count = self.get_count()

        print('AeroMap name: ...')
        print('AeroMap description: ...')

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
    aeroPerformanceMap, no value will be stored but function like 'create_aeromap' and
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
        log.info(aeromap_uid + ' aeroMap will be created.')

    # Add the /aeroMap node, or a new child is already exists
    cpsf.create_branch(tixi,AEROPERFORMANCE_XPATH + '/aeroMap',True)
    am_count = tixi.getNamedChildrenCount(AEROPERFORMANCE_XPATH, 'aeroMap')
    aeromap_xpath = AEROPERFORMANCE_XPATH + '/aeroMap[' + str(am_count) + ']'

    # Add UID and sub nodes
    cpsf.add_uid(tixi, aeromap_xpath, aeromap_uid)
    tixi.addTextElement(aeromap_xpath, 'name', aeromap_uid)
    tixi.addTextElement(aeromap_xpath, 'description', description)
    apm_bc_xpath = aeromap_xpath + '/boundaryConditions'
    cpsf.create_branch(tixi, apm_bc_xpath)
    tixi.addTextElement(apm_bc_xpath,'atmosphericModel','ISA')

    # Add /AeroPerformanceMap and sub nodes
    apm_xpath = aeromap_xpath + '/aeroPerformanceMap'
    cpsf.create_branch(tixi,apm_xpath)
    cpsf.create_branch(tixi,apm_xpath+'/altitude')
    cpsf.create_branch(tixi,apm_xpath+'/machNumber')
    cpsf.create_branch(tixi,apm_xpath+'/angleOfAttack')
    cpsf.create_branch(tixi,apm_xpath+'/angleOfSideslip')
    cpsf.create_branch(tixi,apm_xpath+'/cl')
    cpsf.create_branch(tixi,apm_xpath+'/cd')
    cpsf.create_branch(tixi,apm_xpath+'/cs')
    cpsf.create_branch(tixi,apm_xpath+'/cml')
    cpsf.create_branch(tixi,apm_xpath+'/cmd')
    cpsf.create_branch(tixi,apm_xpath+'/cms')


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
        cpsf.get_value_or_default(tixi,aeromap_xpath+'/name', aeromap_uid)
        description = 'AeroMap checked and utdated by CEASIOMpy ' + str(local_time)
        cpsf.get_value_or_default(tixi,aeromap_xpath+'/description', description)
        aeromap_bc_xpath = aeromap_xpath + '/boundaryConditions'
        cpsf.create_branch(tixi,aeromap_bc_xpath)
        cpsf.get_value_or_default(tixi,aeromap_bc_xpath+'/atmosphericModel', 'ISA')

        # Check AeroPerformanceMap, parameters and coefficients nodes
        apm_xpath = aeromap_xpath + '/aeroPerformanceMap'
        cpsf.create_branch(tixi,apm_xpath)

        #TODO: Replace by a for loop
        cpsf.create_branch(tixi,apm_xpath+'/altitude')
        cpsf.create_branch(tixi,apm_xpath+'/machNumber')
        cpsf.create_branch(tixi,apm_xpath+'/angleOfAttack')
        cpsf.create_branch(tixi,apm_xpath+'/angleOfSideslip')
        cpsf.create_branch(tixi,apm_xpath+'/cl')
        cpsf.create_branch(tixi,apm_xpath+'/cd')
        cpsf.create_branch(tixi,apm_xpath+'/cs')
        cpsf.create_branch(tixi,apm_xpath+'/cml')
        cpsf.create_branch(tixi,apm_xpath+'/cmd')
        cpsf.create_branch(tixi,apm_xpath+'/cms')


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
    cpsf.add_float_vector(tixi,apm_xpath+'/altitude',Param.alt)
    cpsf.add_float_vector(tixi,apm_xpath+'/machNumber',Param.mach)
    cpsf.add_float_vector(tixi,apm_xpath+'/angleOfAttack',Param.aoa)
    cpsf.add_float_vector(tixi,apm_xpath+'/angleOfSideslip',Param.aos)



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
        cpsf.add_float_vector(tixi,apm_xpath+'/cl',Coef.cl)
        log.info('"cl" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cl" values is incorrect, it must be \
                          either equal to the number of parameters or 0')

    # CD coefficients
    if len(Coef.cd) == 0:
        log.warning('No "cd" value have been found, this node will stay empty')
    elif len(Coef.cd) == param_count:
        cpsf.add_float_vector(tixi,apm_xpath+'/cd',Coef.cd)
        log.info('"cd" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cd" values is incorrect, it must be \
                          either equal to the number of parameters or 0')

    # CS coefficients
    if len(Coef.cs) == 0:
        log.warning('No "cs" value have been found, this node will stay empty')
    elif len(Coef.cs) == param_count:
        cpsf.add_float_vector(tixi,apm_xpath+'/cs',Coef.cs)
        log.info('"cs" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cs" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # Cml coefficients
    if len(Coef.cml) == 0:
        log.warning('No "cml" value have been found, this node will stay empty')
    elif len(Coef.cml) == param_count:
        cpsf.add_float_vector(tixi,apm_xpath+'/cml',Coef.cml)
        log.info('"cml" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cml" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # Cmd coefficients
    if len(Coef.cmd) == 0:
        log.warning('No "cmd" value have been found, this node will stay empty')
    elif len(Coef.cmd) == param_count:
        cpsf.add_float_vector(tixi,apm_xpath+'/cmd',Coef.cmd)
        log.info('"cmd" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cmd" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # Cms coefficients
    if len(Coef.cms) == 0:
        log.warning('No "cms" value have been found, this node will stay empty')
    elif len(Coef.cms) == param_count:
        cpsf.add_float_vector(tixi,apm_xpath+'/cms',Coef.cms)
        log.info('"cms" values have been added to the corresponding node')
    else:
        raise ValueError('The number of "cms" values is incorrect, it must \
        either equal to the number of parameters or 0')

    # DampingDerivative
    if len(Coef.damping_derivatives.dcldpstar): # TODO: Improve this check
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcldpstar',Coef.damping_derivatives.dcldpstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcddpstar',Coef.damping_derivatives.dcddpstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcsdpstar',Coef.damping_derivatives.dcsdpstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmldpstar',Coef.damping_derivatives.dcmldpstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmddpstar',Coef.damping_derivatives.dcmddpstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmsdpstar',Coef.damping_derivatives.dcmsdpstar)

        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcldqstar',Coef.damping_derivatives.dcldqstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcddqstar',Coef.damping_derivatives.dcddqstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcsdqstar',Coef.damping_derivatives.dcsdqstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmldqstar',Coef.damping_derivatives.dcmldqstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmddqstar',Coef.damping_derivatives.dcmddqstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmsdqstar',Coef.damping_derivatives.dcmsdqstar)

        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcldrstar',Coef.damping_derivatives.dcldrstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcddrstar',Coef.damping_derivatives.dcddrstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcsdrstar',Coef.damping_derivatives.dcsdrstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmldrstar',Coef.damping_derivatives.dcmldrstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmddrstar',Coef.damping_derivatives.dcmddrstar)
        cpsf.add_float_vector(tixi,apm_xpath+'/dampingDerivatives/positiveRates/dcmsdrstar',Coef.damping_derivatives.dcmsdrstar)

# Add Control surace deflections
# if len(Coef.IncrMap.dcl): # TODO: Improve this check
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcl',Coef.IncrMap.dcl)
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcd',Coef.IncrMap.dcd)
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcs',Coef.IncrMap.dcs)
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcml',Coef.IncrMap.dcml)
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcmd',Coef.IncrMap.dcmd)
#     cpsf.add_float_vector(tixi,apm_xpath+'/incrementMaps/incrementMap/dcms',Coef.IncrMap.dcms)
#
#
#     cpsf.add_uid(tixi,apm_xpath+'/incrementMaps/incrementMap',Coef.IncrMap.ted_uid+'_incrementMap')
#
#     ctrl_dev_uid_xpath = apm_xpath+'/incrementMaps/incrementMap/controlDeviceUID'
#     cpsf.create_branch(tixi,ctrl_dev_uid_xpath)
#     tixi.updateTextElement(ctrl_dev_uid_xpath,Coef.IncrMap.ted_uid)
#
#     ctrl_param_xpath = apm_xpath+'/incrementMaps/incrementMap/controlParameters'
#     cpsf.create_branch(tixi,ctrl_param_xpath)
#     tixi.updateTextElement(ctrl_param_xpath,str(Coef.IncrMap.control_parameter))
#
#     cpsf.create_branch(tixi, apm_xpath+'/incrementMaps/incrementMap/controlParameters')


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

    Coef.alt = cpsf.get_float_vector(tixi,apm_xpath +'/altitude')
    Coef.mach  = cpsf.get_float_vector(tixi,apm_xpath +'/machNumber')
    Coef.aoa = cpsf.get_float_vector(tixi,apm_xpath +'/angleOfAttack')
    Coef.aos = cpsf.get_float_vector(tixi,apm_xpath +'/angleOfSideslip')

    cl_xpath = apm_xpath +'/cl'
    if tixi.checkElement(cl_xpath):
        check_str = tixi.getTextElement(cl_xpath)
        if check_str == '':
            log.warning('No /cl values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cl = []
        else:
            Coef.cl = cpsf.get_float_vector(tixi,cl_xpath)

    cd_xpath = apm_xpath +'/cd'
    if tixi.checkElement(cd_xpath):
        check_str = tixi.getTextElement(cd_xpath)
        if check_str == '':
            log.warning('No /cd values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cd = []
        else:
            Coef.cd = cpsf.get_float_vector(tixi,cd_xpath)

    cs_xpath = apm_xpath +'/cs'
    if tixi.checkElement(cs_xpath):
        check_str = tixi.getTextElement(cs_xpath)
        if check_str == '':
            log.warning('No /cs values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cs = []
        else:
            Coef.cs = cpsf.get_float_vector(tixi,cs_xpath)

    cml_xpath = apm_xpath +'/cml'
    if tixi.checkElement(cml_xpath):
        check_str = tixi.getTextElement(cml_xpath)
        if check_str == '':
            log.warning('No /cml values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cml = []
        else:
            Coef.cml = cpsf.get_float_vector(tixi,cml_xpath)

    cmd_xpath = apm_xpath +'/cmd'
    if tixi.checkElement(cmd_xpath):
        check_str = tixi.getTextElement(cmd_xpath)
        if check_str == '':
            log.warning('No /cmd values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cmd = []
        else:
            Coef.cmd = cpsf.get_float_vector(tixi,cmd_xpath)

    cms_xpath = apm_xpath +'/cms'
    if tixi.checkElement(cms_xpath):
        check_str = tixi.getTextElement(cms_xpath)
        if check_str == '':
            log.warning('No /cms values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.cms = []
        else:
            Coef.cms = cpsf.get_float_vector(tixi,cms_xpath)


    #Damping derivatives (TODO: inprove that)

    dcsdrstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcsdrstar'
    if tixi.checkElement(dcsdrstar_xpath):
        check_str = tixi.getTextElement(dcsdrstar_xpath)

        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcsdrstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcsdrstar = []
        else:
            Coef.dcsdrstar = cpsf.get_float_vector(tixi, dcsdrstar_xpath)

    dcsdpstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcsdpstar'
    if tixi.checkElement(dcsdpstar_xpath):
        check_str = tixi.getTextElement(dcsdpstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcsdpstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcsdpstar = []
        else:
            Coef.dcsdpstar = cpsf.get_float_vector(tixi, dcsdpstar_xpath)

    dcldqstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcldqstar'
    if tixi.checkElement(dcldqstar_xpath):
        check_str = tixi.getTextElement(dcldqstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcldqstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcddqstar = []
        else:
            Coef.dcldqstar = cpsf.get_float_vector(tixi, dcldqstar_xpath)

    dcmsdqstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmsdqstar'
    if tixi.checkElement(dcmsdqstar_xpath):
        check_str = tixi.getTextElement(dcmsdqstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmsdqstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmsdqstar = []
        else:
            Coef.dcmsdqstar = cpsf.get_float_vector(tixi, dcmsdqstar_xpath)

    dcddqstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcddqstar'
    if tixi.checkElement(dcddqstar_xpath):
        check_str = tixi.getTextElement(dcddqstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcddqstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcddqstar = []
        else:
            Coef.dcddqstar = cpsf.get_float_vector(tixi, dcddqstar_xpath)


    dcmddpstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmddpstar'
    if tixi.checkElement(dcmddpstar_xpath):
        check_str = tixi.getTextElement(dcmddpstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmddpstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmddpstar = []
        else:
            Coef.dcmddpstar = cpsf.get_float_vector(tixi, dcmddpstar_xpath)

    dcmldqstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmldqstar'
    if tixi.checkElement(dcmldqstar_xpath):
        check_str = tixi.getTextElement(dcmldqstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmldqstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmldqstar = []
        else:
            Coef.dcmldqstar = cpsf.get_float_vector(tixi, dcmldqstar_xpath)


    dcmldpstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmldpstar'
    if tixi.checkElement(dcmldpstar_xpath):
        check_str = tixi.getTextElement(dcmldpstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmldpstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmldpstar = []
        else:
            Coef.dcmldpstar = cpsf.get_float_vector(tixi, dcmldpstar_xpath)

    dcmldrstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmldrstar'
    if tixi.checkElement(dcmldrstar_xpath):
        check_str = tixi.getTextElement(dcmldrstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmldrstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmldrstar = []
        else:
            Coef.dcmldrstar = cpsf.get_float_vector(tixi, dcmldrstar_xpath)

    dcmddrstar_xpath = apm_xpath +'/dampingDerivatives/positiveRates/dcmddrstar'
    if tixi.checkElement(dcmddrstar_xpath):
        check_str = tixi.getTextElement(dcmddrstar_xpath)
        if check_str == '':
            log.warning('No /dampingDerivatives/positiveRates/dcmddrstar,  values have been found in the CPACS file')
            log.warning('An empty list will be returned.')
            Coef.dcmddrstar = []
        else:
            Coef.dcmddrstar = cpsf.get_float_vector(tixi, dcmddrstar_xpath)

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

    # Maybe shoud be remove
    AeroCoefficient.complete_with_zeros()

    # Create a dictionary from the AeroCoefficient object
    dict = AeroCoefficient.to_dict()

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


def create_aeromap(tixi, name, bound_values):
    """Create an aeromap

    This function  will generate an aeromap either as a CSV file or in a CPACS file
    depending on what is indicated.

    Args:
        tixi (Tixi3 handle): If no handle is given, a CSV file will be generated instead.
        name (str): Name of the aeromap.
        bounds (lst): List of the parameter entries as strings

    """

    bounds = []
    allowed = [str(i) for i in range(0,10)]
    allowed.extend([';','.','[',']','-'])
    for param in bound_values:
        for i in param:
            if i not in allowed:
                raise ValueError("""Not a valid entry : {}.
                      Only following entries are accepted : {}""".format(i,allowed))

        # Check for linspace declaration
        if '[' in param or ']' in param:
            log.info('Linspace generation')
            param = param.replace('[','')
            param = param.replace(']','')
            param = param.split(';')
            if len(param) != 3:
               raise ValueError("""Not the right number of parameters
                     (expected 3 as follows [start;step;stop])""")
            bounds.append(np.arange(float(param[0]),
                                    float(param[2]),
                                    float(param[1])))
        elif len(param) == 0:
            raise ValueError("""Empty parameter, please enter a number""")
        else:
            param = param.split(';')
            if '' in param:
                param.remove('')
            param = [float(i) for i in param]
            bounds.append(np.array(param))

    lengths = set([len(b) for b in bounds])

    if len(lengths) != 1:
        if len(lengths) == 2 and 1 in lengths:
            for i ,b in enumerate(bounds):
                if len(b) == 1:
                    b = np.full((1,max(lengths)),b[0])
                    bounds[i]=b[0].tolist()
        else:
            raise ValueError(""" Not the same number of element for each parameter
                  (each parameter must have the same number of elements or one
                   single value which will be repeated.)""")
    bounds = np.array(bounds)

    if name == '':
        raise ValueError("""Empty name, please enter a name !""")
    else:
        desc = 'Auto-generated Aeromap'
        create_empty_aeromap(tixi, name, description = desc)
        Param = AeroCoefficient()
        Param.alt = bounds[0,:]
        Param.mach = bounds[1,:]
        Param.aoa = bounds[2,:]
        Param.aos = bounds[3,:]

        save_parameters(tixi, name, Param)


def get_current_aeromap_uid(tixi, module_list):
    """Return uid of selected aeromap.

    Check the modules that will be run in the optimisation routine to specify
    the uID of the correct aeromap in the CPACS file.

    Args:
        module_list (lst): List of the modules that are run in the routine
        tixi (tixi handle): Tixi handle of the CPACS file.

    Returns:
        uid (str) : Name of the aeromap that is used for the routine
    """
    uid = 'None'

    for module in module_list:
        if module == 'SU2Run':
            log.info('Found SU2 analysis')
            xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/aeroMapUID'
            uid = tixi.getTextElement(xpath)
        elif module == 'PyTornado':
            log.info('Found PyTornado analysis')
            xpath = '/cpacs/toolspecific/pytornado/aeroMapUID'
            uid = tixi.getTextElement(xpath)
        elif module == 'SMUse':
            log.info('Found a Surrogate model')
            xpath = '/cpacs/toolspecific/CEASIOMpy/surrogateModelUse/aeroMapUID'

    if 'SkinFriction' in module_list:
        log.info('Found SkinFriction analysis')
        uid = uid + '_SkinFriction'

    return uid


def my_test_func():
    # this is just a github test
    pass

# def modify_aeromap_uid(tixi,aeromap_uid, new aeromap_uid):
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
