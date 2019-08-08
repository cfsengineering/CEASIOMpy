"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Module to run SU2 Calculation in CEASIOMpy

    Works with Python 2.7/3.6
    Author : Aidan Jungo
    Creation: 2018-11-06
    Last modifiction: 2019-08-08

    TODO:  - Add check MPI installation
           - Add possibility of using SSH
           - Save coefficient in the new AeroPerformanceMap from CPACS 3.1

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_efficiency(force_path):
    """Function to get efficiency (CL/CD)

    Function 'get_efficiency' the CL/CD ratio in the results file
    (forces_breakdown.dat)

    Source : -

    ARGUMENTS
    (str)           force_path      -- Path to the Force Breakdown result file

    RETURNS
    (float)         cl_cd           -- CL/CD [-]

    """

    with open(force_path) as f:
        for line in f.readlines():
            if 'CL/CD' in line:
                cl_cd = float(line.split(':')[1].split('|')[0])
                break

    return cl_cd


def run_SU2(mesh_path, config_path):
    """ Function to run SU2 calculation

    Function 'run_SU2' runs a SU2 calculation with an SU2 Mesh (.su2) and an
    SU2 configuration file (.cfg)

    Source : -

    ARGUMENTS
    (str)           mesh_path            -- Path to the mesh file
    (str)           config_path          -- Path to the config file

    RETURNS
    """

    # Define paths
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    TMP_DIR = MODULE_DIR + '/tmp'
    config_tmp_path = TMP_DIR + '/configSU2.cfg'
    force_tmp_path = TMP_DIR + '/forces_breakdown.dat'
    force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat'

    #Check if SU2 is installed
    # with python3 could be maybe replace by "shutil.which("SU2_CFD")"
    # TODO: add check MPI
    check_SU2 = os.system('which SU2_CFD')  # give 0 if it works
    if check_SU2:
        log.error('SU2 does not seem to be installed on your computer!')
        return None
    else:
        log.info('SU2 has been found on your computer!')

    # Empty tmp directory
    tmp_file_list = os.listdir(TMP_DIR)
    for tmp_file in tmp_file_list:
        tmp_file_path = TMP_DIR + '/' + tmp_file
        os.remove(tmp_file_path)
    log.info('The /tmp directory has been cleared.')

    # Copy SU2 config file (.cfg) in the temp directory
    if os.path.isfile(config_path):
        shutil.copy(config_path, config_tmp_path)
        log.info('The input SU2 config file has been copied in /tmp ')
    else:
        log.error('The input SU2 config file cannot be found!')
        return None

    # Run Sumo to create a create a mesh
    su2_command = 'SU2_CFD '
    proc_nb = 4
    su2_inst_path = '/soft/SU2/bin/SU2_CFD'  # with python3 could be replace by shutil.which("SU2_CFD")
    su2_command = 'mpirun -np ' + str(proc_nb) + ' ' + su2_inst_path + ' '
    command_line = [su2_command, config_tmp_path]
    os.chdir(TMP_DIR)
    os.system(''.join(command_line))
    os.system('/soft/SU2/bin/SU2_SOL ' + config_tmp_path)
    os.chdir(MODULE_DIR)

    # Copy Force Breakdown (.dat) in ToolOutput directory
    if os.path.isfile(force_tmp_path):
        shutil.copy(force_tmp_path, force_path)
        log.info('The Force Breakdown file has been copied in /ToolOutput ')
    else:
        log.error('The Force Breakdown file cannot be found!')
        return None

#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('Running RunSU2 module')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    mesh_path = MODULE_DIR + '/ToolInput/ToolInput.su2'
    config_path = MODULE_DIR + '/ToolInput/ToolInput.cfg'

    run_SU2(mesh_path, config_path)

    force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat'
    print('Your aircraft achieve a CL/CD of :')
    print(get_efficiency(force_path))

    log.info('End of RunSU2 module')
