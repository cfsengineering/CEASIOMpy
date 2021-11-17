"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from SU2 calculations

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-10-02
| Last modifiction: 2021-11-17

TODO:

    * Use Pandas datafarme to write aeromaps
    * Finish relusts saving for Control surface deflections
    * Solve other small issues

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import create_branch, get_value, get_value_or_default
from cpacspy.utils import COEFS
from ceasiompy.utils.xpath import SU2_XPATH, WETTED_AREA_XPATH

from ceasiompy.SU2Run.func.extractloads import extract_loads

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


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

    cpacs = CPACS(cpacs_path)

    # TODO Check and reactivate that
    # save_timestamp(tixi,SU2_XPATH) <-- ceaf.replace by get get_execution_date()

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    os.chdir(wkdir)
    dir_list = os.listdir(wkdir)

    # Get and save Wetted area
    wetted_area = get_wetted_area(wkdir)
    create_branch(cpacs.tixi, WETTED_AREA_XPATH)
    cpacs.tixi.updateDoubleElement(WETTED_AREA_XPATH,wetted_area,'%g')

    # Save aeroPerformanceMap
    su2_aeromap_xpath = SU2_XPATH + '/aeroMapUID'
    aeromap_uid = get_value(cpacs.tixi,su2_aeromap_xpath)

    # Check if loads shoud be extracted
    check_extract_loads_xpath = SU2_XPATH + '/results/extractLoads'
    check_extract_loads = get_value_or_default(cpacs.tixi, check_extract_loads_xpath,False)

    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    alt_list = aeromap.get('altitude').tolist()
    mach_list = aeromap.get('machNumber').tolist()
    aoa_list = aeromap.get('angleOfAttack').tolist()
    aos_list = aeromap.get('angleOfSideslip').tolist()

    case_dir_list = [dir for dir in dir_list if 'Case' in dir]

    for config_dir in sorted(case_dir_list):

        case_nb = int(config_dir.split('_')[0].split('Case')[1])
        
        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]
        mach = mach_list[case_nb]
        alt = alt_list[case_nb]
        
        if os.path.isdir(config_dir):
            os.chdir(config_dir)
            force_file_name = 'forces_breakdown.dat'
            if not os.path.isfile(force_file_name):
                raise OSError('No result force file have been found!')

            fixed_cl_xpath = SU2_XPATH + '/fixedCL'
            fixed_cl = get_value_or_default(cpacs.tixi,fixed_cl_xpath,'NO')

            if fixed_cl == 'YES':
                force_file_name = 'forces_breakdown.dat'
                cl_cd, aoa = get_efficiency_and_aoa(force_file_name)

                # Replace aoa with the with the value from fixed cl calculation
                aeromap.df.loc['angleOfAttack'][case_nb] = aoa

                # Save cl/cd found during the fixed CL calculation
                # TODO: maybe save cl/cd somewhere else
                lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio'
                create_branch(cpacs.tixi, lDRatio_xpath)
                cpacs.tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')


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
            rotation_rate = get_value_or_default(cpacs.tixi,rotation_rate_xpath,-1.0)
            ref_len = cpacs.aircraft.ref_lenght
            adim_rot_rate =  rotation_rate * ref_len / velocity

            coefs = {'cl':cl,'cd':cd,'cs':cs,
                         'cmd':cmd,'cms':cms,'cml':cml}

            if '_dp' in config_dir:
                for coef in COEFS:
                    coef_baseline = aeromap.get(coef,alt=alt,mach=mach,aoa=aoa,aos=aos)
                    dcoef = (coefs[coef]-coef_baseline)/adim_rot_rate
                    aeromap.add_damping_derivatives(alt=alt,mach=mach,aos=aos,aoa=aoa,coef=coef,axis='dp',value=dcoef,rate=rotation_rate)
               
            elif '_dq' in config_dir:
                for coef in COEFS:
                    coef_baseline = aeromap.get(coef,alt=alt,mach=mach,aoa=aoa,aos=aos)
                    dcoef = (coefs[coef]-coef_baseline)/adim_rot_rate
                    aeromap.add_damping_derivatives(alt=alt,mach=mach,aos=aos,aoa=aoa,coef=coef,axis='dq',value=dcoef,rate=rotation_rate)
               
            elif '_dr' in config_dir:
                for coef in COEFS:
                    coef_baseline = aeromap.get(coef,alt=alt,mach=mach,aoa=aoa,aos=aos)
                    dcoef = (coefs[coef]-coef_baseline)/adim_rot_rate
                    aeromap.add_damping_derivatives(alt=alt,mach=mach,aos=aos,aoa=aoa,coef=coef,axis='dr',value=dcoef,rate=rotation_rate)
               
            elif '_TED_' in config_dir:

                # TODO: convert when it is possible to save TED in cpacspy
                raise NotImplementedError('TED not implemented yet')
                
                # config_dir_split = config_dir.split('_')
                # ted_idx = config_dir_split.index('TED')
                # ted_uid = config_dir_split[ted_idx+1]
                # defl_angle = float(config_dir.split('_defl')[1])

                # try:
                #     print(Coef.IncrMap.dcl)
                # except AttributeError:
                #     Coef.IncrMap = apmf.IncrementMap(ted_uid)

                # # TODO: still in development, for now only 1 ted and 1 defl
                # print(ted_uid,defl_angle)

                # dcl = (cl-Coef.cl[-1])
                # dcd = (cd-Coef.cd[-1])
                # dcs = (cs-Coef.cs[-1])
                # dcml = (cml-Coef.cml[-1])
                # dcmd = (cmd-Coef.cmd[-1])
                # dcms = (cms-Coef.cms[-1])

                # control_parameter = -1

                # Coef.IncrMap.add_cs_coef(dcl,dcd,dcs,dcml,dcmd,dcms,ted_uid,control_parameter)

            else: # Baseline coefficients, (no damping derivative or control surfaces case)
                aeromap.add_coefficients(alt=alt,mach=mach,aos=aos,aoa=aoa,cd=cd,cl=cl,cs=cs,cml=cml,cmd=cmd,cms=cms)
 
            if check_extract_loads:
                results_files_dir = os.path.join(wkdir,config_dir)
                extract_loads(results_files_dir)

            os.chdir(wkdir)

    # Save object Coef in the CPACS file
    aeromap.save()

    # Save the CPACS file
    cpacs.save_cpacs(cpacs_out_path,overwrite=True)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
