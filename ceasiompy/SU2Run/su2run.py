"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-06
| Last modifiction: 2020-02-24

TODO:

    * Add possibility of using SSH
    * Create test functions
    * complete input/output in __specs__
    * Check platform with-> sys.platform
    * Move run_SU2_fsi to /SU2Run/func/su2fsi.py

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import datetime

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f

from ceasiompy.SU2Run.func.su2config import generate_su2_config
from ceasiompy.SU2Run.func.extractloads import extract_loads
from ceasiompy.SU2Run.func.su2results import get_wetted_area, get_efficiency, get_su2_results

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def run_SU2_single(config_path, wkdir):
    """Function to run a single SU2 claculation.

    Function 'run_SU2_single' will run in the given working directory a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    su2f.run_soft('SU2_CFD',config_path,wkdir)
    su2f.run_soft('SU2_SOL',config_path,wkdir)

    os.chdir(original_dir)


def run_SU2_multi(wkdir):
    """Function to run a multiple SU2 claculation.

    Function 'run_SU2_multi' will run in the given working directory SU2
    calculations (SU2_CFD then SU2_SOL). The working directory must have a
    folder sctructure created by 'SU2Config' module.

    Args:
        wkdir (str): Path to the working directory

    """

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    # Check if there is some case directory
    case_dir_list = [dir for dir in os.listdir(wkdir) if 'Case' in dir]
    if case_dir_list == []:
        raise OSError('No folder has been found in the working directory: ' + wkdir)

    for dir in case_dir_list:
        config_dir = os.path.join(wkdir,dir)
        os.chdir(config_dir)

        find_config_cfd = False
        find_config_def = False
        find_config_rot = False
        find_config_rot_sym = False

        for file in os.listdir(config_dir):
            if file == 'ConfigCFD.cfg':
                if find_config_cfd:
                    raise ValueError('More than one "ConfigCFD.cfg" file in this directory!')
                config_cfd_path = os.path.join(config_dir,file)
                find_config_cfd = True

            if file == 'ConfigDEF.cfg':
                if find_config_def:
                    raise ValueError('More than one "ConfigDEF.cfg" file in this directory!')
                config_def_path = os.path.join(config_dir,file)
                find_config_def = True

            if file == 'ConfigDEF_rot.cfg':
                if find_config_rot:
                    raise ValueError('More than one "ConfigDEF_rot.cfg" file in this directory!')
                config_rot_path = os.path.join(config_dir,file)
                find_config_rot = True

            if file == 'ConfigDEF_rot_sym.cfg':
                if find_config_rot_sym:
                    raise ValueError('More than one "ConfigDEF_rot_sym.cfg" file in this directory!')
                config_rot_sym_path = os.path.join(config_dir,file)
                find_config_rot_sym = True


        if find_config_def:
            su2f.run_soft('SU2_DEF',config_def_path,config_dir)
        if find_config_rot:
            su2f.run_soft('SU2_DEF',config_rot_path,config_dir)
        if find_config_rot_sym:
            su2f.run_soft('SU2_DEF',config_rot_sym_path,config_dir)

        if not find_config_cfd:
            raise ValueError('No "ConfigCFD.cfg" file has been found in this directory!')

        su2f.run_soft('SU2_CFD',config_cfd_path,config_dir)
        # su2f.run_soft('SU2_SOL',config_file_path,config_dir)
        # Not usefuel to do at everytime exept if you need surface/volume flow
        # file, if not forces_breakdown.dat will be generated by SU2_CFD.

        os.chdir(wkdir)


# TODO: This function should be moved to /SU2Run/func/su2fsi.py
def run_SU2_fsi(config_path, wkdir):
    """Function to run a SU2 claculation for FSI .

    Function 'run_SU2_fsi' deforms an element of the mesh (e.g. wing) from
    point file 'disp.dat' given by a sctructural model and then runs a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path. Finally a
    load file is saved, to be send to the sctructural model.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    # Modify config file for SU2_DEF
    config_def_path = os.path.join(wkdir,'ConfigDEF.cfg')
    cfg_def = su2f.read_config(config_path)

    cfg_def['DV_KIND'] = 'SURFACE_FILE'
    cfg_def['DV_MARKER'] = 'Wing'
    cfg_def['DV_FILENAME'] = 'disp.dat' # TODO: Should be a constant or find in CPACS ?
    # TODO: Do we need that? if yes, find 'WING' in CPACS
    cfg_def['DV_PARAM'] = ['WING', '0', '0', '1', '0.0', '0.0', '1.0']
    cfg_def['DV_VALUE'] = 0.01
    su2f.write_config(config_def_path,cfg_def)

    # Modify config file for SU2_CFD
    config_cfd_path = os.path.join(wkdir,'ConfigCFD.cfg')
    cfg_cfd = su2f.read_config(config_path)
    cfg_cfd['MESH_FILENAME'] = 'mesh_out.su2'
    su2f.write_config(config_cfd_path,cfg_cfd)

    su2f.run_soft('SU2_DEF',config_def_path,wkdir) # does it work with mpi?
    su2f.run_soft('SU2_CFD',config_cfd_path,wkdir)
    su2f.run_soft('SU2_SOL',config_cfd_path,wkdir)

    extract_loads(wkdir)

    os.chdir(original_dir)


# def get_su2_results(cpacs_path,cpacs_out_path,wkdir):
#     """ Function to write SU2 results in a CPACS file.
#
#     Function 'get_su2_results' get available results from the latest SU2
#     calculation and put it at the correct place in the CPACS file.
#
#     '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aerpMap[n]/aeroPerformanceMap'
#
#     Args:
#         cpacs_path (str): Path to input CPACS file
#         cpacs_out_path (str): Path to output CPACS file
#         wkdir (str): Path to the working directory
#
#     """
#
#     tixi = cpsf.open_tixi(cpacs_path)
#
#     # TODO Check and reactivate that
#     # save_timestamp(tixi,SU2_XPATH) <-- ceaf.replace by get get_execution_date()
#
#     if not os.path.exists(wkdir):
#         raise OSError('The working directory : ' + wkdir + 'does not exit!')
#
#     os.chdir(wkdir)
#     dir_list = os.listdir(wkdir)
#
#     # Get and save Wetted area
#     wetted_area = get_wetted_area(wkdir)
#
#     wetted_area_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea'
#     cpsf.create_branch(tixi, wetted_area_xpath)
#
#     tixi.updateDoubleElement(wetted_area_xpath,wetted_area,'%g')
#
#     # Get and save CL/CD ratio
#     fixed_cl_xpath = SU2_XPATH + '/fixedCL'
#     fixed_cl = cpsf.get_value_or_default(tixi, fixed_cl_xpath,'NO')
#     # TODO
#     # if fixed_cl == 'YES':
#         # find force_file_name = 'forces_breakdown.dat'
#         # cl_cd = get_efficiency(force_path)
#         # lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio' # TODO: probalby change xpath and name
#         # cpsf.create_branch(tixi, lDRatio_xpath)
#         # tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')
#
#     # Save aeroPerformanceMap
#     su2_aeromap_xpath = SU2_XPATH + '/aeroMapUID'
#     aeromap_uid = cpsf.get_value(tixi,su2_aeromap_xpath)
#
#     # Check if loads shoud be extracted
#     check_extract_loads_xpath = SU2_XPATH + '/results/extractLoads'
#     check_extract_loads = cpsf.get_value_or_default(tixi, check_extract_loads_xpath,False)
#
#     # Create an oject to store the aerodynamic coefficients
#     apmf.check_aeromap(tixi,aeromap_uid)
#
#     # TODO: create a function to earase previous results...
#     Coef2 = apmf.get_aeromap(tixi, aeromap_uid)
#     Coef = apmf.AeroCoefficient()
#     Coef.alt = Coef2.alt
#     Coef.mach = Coef2.mach
#     Coef.aoa = Coef2.aoa
#     Coef.aos = Coef2.aos
#
#     case_dir_list = [dir for dir in dir_list if 'Case' in dir]
#
#     for config_dir in case_dir_list:
#         if os.path.isdir(config_dir):
#             os.chdir(config_dir)
#             force_file_name = 'forces_breakdown.dat'
#             if not os.path.isfile(force_file_name):
#                 raise OSError('No result force file have been found!')
#
#             # Read result file
#             with open(force_file_name) as f:
#                 for line in f.readlines():
#                     if 'Total CL:' in line:
#                         cl = float(line.split(':')[1].split('|')[0])
#                     if 'Total CD:' in line:
#                         cd = float(line.split(':')[1].split('|')[0])
#                     if 'Total CSF:' in line:
#                         cs = float(line.split(':')[1].split('|')[0])
#                     # TODO: Check which axis name corespond to waht: cml, cmd, cms
#                     if 'Total CMx:' in line:
#                         cmd = float(line.split(':')[1].split('|')[0])
#                     if 'Total CMy:' in line:
#                         cms = float(line.split(':')[1].split('|')[0])
#                     if 'Total CMz:' in line:
#                         cml = float(line.split(':')[1].split('|')[0])
#                     if ('Free-stream velocity' in line and 'm/s' in line):
#                         velocity = float(line.split(' ')[7])
#
#             # Damping derivatives
#             rotation_rate_xpath = SU2_XPATH + '/options/rotationRate'
#             rotation_rate = cpsf.get_value_or_default(tixi,rotation_rate_xpath,1.0)
#             ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
#             ref_len = cpsf.get_value(tixi,ref_xpath + '/length')
#             adim_rot_rate =  rotation_rate * ref_len / velocity
#
#             if '_dp' in config_dir:
#                 dcl = (cl-Coef.cl[-1])/adim_rot_rate
#                 dcd = (cd-Coef.cd[-1])/adim_rot_rate
#                 dcs = (cs-Coef.cs[-1])/adim_rot_rate
#                 dcml = (cml-Coef.cml[-1])/adim_rot_rate
#                 dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
#                 dcms = (cms-Coef.cms[-1])/adim_rot_rate
#                 Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dp')
#
#             elif '_dq' in config_dir:
#                 dcl = (cl-Coef.cl[-1])/adim_rot_rate
#                 dcd = (cd-Coef.cd[-1])/adim_rot_rate
#                 dcs = (cs-Coef.cs[-1])/adim_rot_rate
#                 dcml = (cml-Coef.cml[-1])/adim_rot_rate
#                 dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
#                 dcms = (cms-Coef.cms[-1])/adim_rot_rate
#                 Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dq')
#
#             elif '_dr' in config_dir:
#                 dcl = (cl-Coef.cl[-1])/adim_rot_rate
#                 dcd = (cd-Coef.cd[-1])/adim_rot_rate
#                 dcs = (cs-Coef.cs[-1])/adim_rot_rate
#                 dcml = (cml-Coef.cml[-1])/adim_rot_rate
#                 dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
#                 dcms = (cms-Coef.cms[-1])/adim_rot_rate
#                 Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dr')
#
#             elif '_cs' in config_dir:
#
#                 # TODO: how to store these results correctly (CPACS 3.1 doc)
#
#                 #controlDeviceUID
#                 #controlParameters
#                 dcl = (cl-Coef.cl[-1])
#                 dcd = (cd-Coef.cd[-1])
#                 dcs = (cs-Coef.cs[-1])
#                 dcml = (cml-Coef.cml[-1])
#                 dcmd = (cmd-Coef.cmd[-1])
#                 dcms = (cms-Coef.cms[-1])
#                 cs_uid = 'test'
#                 control_parameter = [0,1]
#
#                 Coef.increment_map.add_cs_coef(dcl,dcd,dcs,dcml,dcmd,dcms,cs_uid,control_parameter)
#
#             else: # No damping derivative or control surfaces case
#                 Coef.add_coefficients(cl,cd,cs,cml,cmd,cms)
#
#             if check_extract_loads:
#                 results_files_dir = os.path.join(wkdir,config_dir)
#                 extract_loads(results_files_dir)
#
#             os.chdir(wkdir)
#
#     # Save object Coef in the CPACS file
#     apmf.save_coefficients(tixi,aeromap_uid,Coef)
#
#     cpsf.close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    tixi = cpsf.open_tixi(cpacs_path)

    if len(sys.argv)>1:
        if sys.argv[1] == '-c':
            wkdir = ceaf.get_wkdir_or_create_new(tixi)
            generate_su2_config(cpacs_path,cpacs_out_path,wkdir)
        elif sys.argv[1] == '-s':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            config_path = os.path.join(wkdir,'ConfigCFD.cfg') # temporary
            run_SU2_single(config_path,wkdir)
        elif sys.argv[1] == '-m':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            run_SU2_multi(wkdir)
        elif sys.argv[1] == '-f':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            config_path = os.path.join(wkdir,'ConfigCFD.cfg')   # temporary
            run_SU2_fsi(config_path,wkdir)
        elif sys.argv[1] == '-r':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            get_su2_results(cpacs_path,cpacs_out_path,wkdir)
        else:
            print('This arugment is not a valid option!')
    else: # if no argument given
        wkdir = ceaf.get_wkdir_or_create_new(tixi)
        generate_su2_config(cpacs_path,cpacs_out_path,wkdir)
        run_SU2_multi(wkdir)
        get_su2_results(cpacs_path,cpacs_out_path,wkdir)

    # TODO: cpacs_out_path for 'create_config' should be a temp file, now it's erase by 'get_su2get_su2_results'

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')



# TODO: try to use subprocess instead of os.system, how to deal with log file...?
# import subprocess
# p = subprocess.Popen(command_line, stdout=subprocess.PIPE)
# log_lines = p.communicate()[0]
# logfile = open(logfile_path, 'w')
# logfile.writelines(log_lines)
# logfile.close()
