"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from SU2 calculations

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-10-02
| Last modifiction: 2020-05-21

TODO:

    * Use Pandas datafarme to write aeromaps
    * Finish relusts saving for Control surface deflections
    * Solve other small issues

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import pandas as pd
import matplotlib

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.su2functions import read_config

from ceasiompy.SU2Run.func.extractloads import extract_loads

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_wetted_area(wkdir):
    """ Function get the wetted area calculated by SU2

    Function 'get_wetted_area' finds the SU2 logfile and returns the wetted
    area value previously calculated by SU2.

    Args:
        wkdir (str): Path to the working directory

    Returns:
        wetted_area (float): Wetted area calculated by SU2 [m^2]

    """

    wetted_area = None
    su2_logfile_path = ''

    # Find a logfile in wkdir
    for (root, dirs, files) in os.walk(wkdir):
        for file in files:
            if file == 'logfileSU2_CFD.log':
                su2_logfile_path = os.path.join(root, file)
                break

    if su2_logfile_path == '':
        log.warning('No logfile has been found for working directory!')

    # Read the logfile
    with open(su2_logfile_path) as f:
        for line in f.readlines():
            if 'Wetted area =' in line:
                wetted_area = float(line.split(' ')[3])
                break

    if wetted_area is None:
        # raise ValueError('No value has been found for the wetted area!')
        log.warning('No value has been found for the wetted area!')
        return 0

    else:
        log.info('Wetted area value has been found and is equal to '
                  + str(wetted_area) + ' [m^2]')
        return wetted_area


# This function should be modified maybe merge with get_aoa
def get_efficiency_and_aoa(force_path):
    """Function to get efficiency (CL/CD) and angle of attack (AoA)

    Function 'get_efficiency_and_aoa' search fot the efficiency (CL/CD) and
    the Angle of Attack (AoA) in the results file (forces_breakdown.dat)

    Args:
        force_path (str): Path to the Force Breakdown result file

    Returns:
        cl_cd (float):  CL/CD ratio [-]
        aoa (float):    Angle of Attack [deg]

    """

    cl_cd = None
    aoa = None

    with open(force_path) as f:
        for line in f.readlines():
            if 'CL/CD' in line:
                cl_cd = float(line.split(':')[1].split('|')[0])
                continue

            if 'Angle of attack (AoA):' in line:
                aoa = float(line.split('Angle of attack (AoA):')[1].split('deg,')[0].strip())
                continue

            if cl_cd and aoa:
                break

    if cl_cd is None or aoa is None:
        raise ValueError('No value has been found for the CL/CD ratio or AoA!')
    else:
        log.info('CL/CD ratio has been found and is equal to: '+ str(cl_cd) + '[-]')
        log.info('AoA has been found and is equal to: ' + str(aoa) + '[-]')

        return cl_cd, aoa


def get_su2_results(cpacs_path,cpacs_out_path,wkdir):
    """ Function to write SU2 results in a CPACS file.

    Function 'get_su2_results' get available results from the latest SU2
    calculation and put it at the correct place in the CPACS file.

    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aerpMap[n]/aeroPerformanceMap'

    Args:
        cpacs_path (str): Path to input CPACS file
        cpacs_out_path (str): Path to output CPACS file
        wkdir (str): Path to the working directory

    """

    tixi = cpsf.open_tixi(cpacs_path)

    # TODO Check and reactivate that
    # save_timestamp(tixi,SU2_XPATH) <-- ceaf.replace by get get_execution_date()

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    os.chdir(wkdir)
    dir_list = os.listdir(wkdir)

    # Get and save Wetted area
    wetted_area = get_wetted_area(wkdir)

    wetted_area_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea'
    cpsf.create_branch(tixi, wetted_area_xpath)

    tixi.updateDoubleElement(wetted_area_xpath,wetted_area,'%g')


    # Save aeroPerformanceMap
    su2_aeromap_xpath = SU2_XPATH + '/aeroMapUID'
    aeromap_uid = cpsf.get_value(tixi,su2_aeromap_xpath)

    # Check if loads shoud be extracted
    check_extract_loads_xpath = SU2_XPATH + '/results/extractLoads'
    check_extract_loads = cpsf.get_value_or_default(tixi, check_extract_loads_xpath,False)

    # Create an oject to store the aerodynamic coefficients
    apmf.check_aeromap(tixi,aeromap_uid)

    # TODO: create a function to earase previous results...
    Coef2 = apmf.get_aeromap(tixi, aeromap_uid)
    Coef = apmf.AeroCoefficient()
    Coef.alt = Coef2.alt
    Coef.mach = Coef2.mach
    Coef.aoa = Coef2.aoa
    Coef.aos = Coef2.aos

    case_dir_list = [dir for dir in dir_list if 'Case' in dir]

    for config_dir in sorted(case_dir_list):
        if os.path.isdir(config_dir):
            os.chdir(config_dir)
            force_file_name = 'forces_breakdown.dat'
            if not os.path.isfile(force_file_name):
                raise OSError('No result force file have been found!')

            fixed_cl_xpath = SU2_XPATH + '/fixedCL'
            fixed_cl = cpsf.get_value_or_default(tixi,fixed_cl_xpath,'NO')

            if fixed_cl == 'YES':
                force_file_name = 'forces_breakdown.dat'
                cl_cd, aoa = get_efficiency_and_aoa(force_file_name)

                # Save the AoA found during the fixed CL calculation
                Coef.aoa = [aoa]
                apmf.save_parameters(tixi,aeromap_uid,Coef)

                # Save cl/cd found during the fixed CL calculation
                # TODO: maybe save cl/cd somewhere else
                lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio'
                cpsf.create_branch(tixi, lDRatio_xpath)
                tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')


            # Read result file
            with open(force_file_name) as f:
                for line in f.readlines():
                    if 'Total CL:' in line:
                        cl = float(line.split(':')[1].split('|')[0])
                    if 'Total CD:' in line:
                        cd = float(line.split(':')[1].split('|')[0])
                    if 'Total CSF:' in line:
                        cs = float(line.split(':')[1].split('|')[0])
                    # TODO: Check which axis name corespond to waht: cml, cmd, cms
                    if 'Total CMx:' in line:
                        cmd = float(line.split(':')[1].split('|')[0])
                    if 'Total CMy:' in line:
                        cms = float(line.split(':')[1].split('|')[0])
                    if 'Total CMz:' in line:
                        cml = float(line.split(':')[1].split('|')[0])
                    if ('Free-stream velocity' in line and 'm/s' in line):
                        velocity = float(line.split(' ')[7])

            # Damping derivatives
            rotation_rate_xpath = SU2_XPATH + '/options/rotationRate'
            rotation_rate = cpsf.get_value_or_default(tixi,rotation_rate_xpath,1.0)
            ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
            ref_len = cpsf.get_value(tixi,ref_xpath + '/length')
            adim_rot_rate =  rotation_rate * ref_len / velocity

            if '_dp' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dp')

            elif '_dq' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dq')

            elif '_dr' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dr')

            elif '_TED_' in config_dir:

                config_dir_split = config_dir.split('_')
                ted_idx = config_dir_split.index('TED')
                ted_uid = config_dir_split[ted_idx+1]
                defl_angle = float(config_dir.split('_defl')[1])

                try:
                    print(Coef.IncrMap.dcl)
                except AttributeError:
                    Coef.IncrMap = apmf.IncrementMap(ted_uid)

                # TODO: still in development, for now only 1 ted and 1 defl
                print(ted_uid,defl_angle)

                dcl = (cl-Coef.cl[-1])
                dcd = (cd-Coef.cd[-1])
                dcs = (cs-Coef.cs[-1])
                dcml = (cml-Coef.cml[-1])
                dcmd = (cmd-Coef.cmd[-1])
                dcms = (cms-Coef.cms[-1])

                control_parameter = -1

                Coef.IncrMap.add_cs_coef(dcl,dcd,dcs,dcml,dcmd,dcms,ted_uid,control_parameter)

            else: # No damping derivative or control surfaces case
                Coef.add_coefficients(cl,cd,cs,cml,cmd,cms)

            if check_extract_loads:
                results_files_dir = os.path.join(wkdir,config_dir)
                extract_loads(results_files_dir)

            os.chdir(wkdir)

    # Save object Coef in the CPACS file
    apmf.save_coefficients(tixi,aeromap_uid,Coef)

    cpsf.close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
