"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate SU2 Configuration and results.

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-09-30
| Last modifiction: 2021-03-25

TODO:

    * Create coresponding test functions
    * Config: save comment lines ???
    * Config: do something for lines which use '|' as separators

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

from collections import OrderedDict

import ceasiompy.utils.ceasiompyfunctions as ceaf

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

SOFT_LIST = ['SU2_DEF','SU2_CFD','SU2_SOL','mpirun.mpich','mpirun']


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def read_config(config_file_path):
    """ Function read a SU2 configuration file

    Function 'read_config' return a dictionary of the data found in the SU2
    configuration file.

    Args:
        config_file_path (str):  SU2 configuration file path

    Returns:
        data_dict (dict): Dictionary of the data from the SU2 configuration file

    """

    none_list = ['NONE','None','none']

    data_dict = OrderedDict()
    with open(config_file_path, 'r') as f:
        for line in f:
            if line.startswith('%') or '=' not in line:
                continue
            key, value = line.split('=')

            # if any 'None' in value
            find_none = any(ele in value for ele in none_list)

            if find_none:
                data_dict[key.strip()] = None
            elif '(' in value:
                new_value = value.replace('(','').replace(')','')
                value_list = new_value.split(',')
                strip_value_list = [item.strip() for item in value_list]
                if len(strip_value_list) == 1 and strip_value_list[0]=='':
                    data_dict[key.strip()] = None
                else:
                    data_dict[key.strip()] = strip_value_list
            else:
                data_dict[key.strip()] = value.strip()

    return data_dict


def write_config(config_file_path, config_dict):
    """ Function write a SU2 configuration file from a dictionary.

    Function 'write_config' write a SU2 configuration file with the infomation
    contained in the given 'config_dict'.

    Args:
        config_file_path (str):  SU2 configuration file path
        config_dict (dict): Dictionary of the data from the SU2 configuration file

    """

    # TODO: add somting to include commentary
    with open(config_file_path, 'w') as f:
        for key, value in config_dict.items():
            if isinstance(value,list):
                value_str = ' , '.join(value)
                f.write(str(key) + ' = ( ' + value_str + ' ) \n')
            else:
                if value is None or value == '':
                    value = 'NONE'
                f.write(str(key) + ' = ' + str(value) + '\n')


def get_mesh_marker(su2_mesh_path):
    """ Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_marker' return all the SU2 mesh marker (except Farfield)
    found in the SU2 mesh file.

    Args:
        su2_mesh_path (interger):  Path to the SU2 mesh

    Returns:
        marker_list (list): List of all mesh marker
    """

    wall_marker_list = []
    eng_bc_marker_list = []
    with open(su2_mesh_path) as f:
        for line in f.readlines():
            if ('MARKER_TAG' in line and 'Farfield' not in line):
                new_marker = line.split('=')[1][:-1]  # -1 to remove "\n"

                if new_marker.endswith('Intake') or new_marker.endswith('Exhaust'):
                    eng_bc_marker_list.append(new_marker)
                else:
                    wall_marker_list.append(new_marker)

    if not wall_marker_list and not eng_bc_marker_list:
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return wall_marker_list, eng_bc_marker_list


def run_soft(soft, config_path, wkdir, nb_proc):
    """Function run one of the existing SU2 software

    Function 'run_soft' create the comment line to run correctly a SU2 software
    (SU2_DEF, SU2_CFD, SU2_SOL) with MPI (if installed). The SOFT_DICT is
    create from the SOFT_LIST define at the top of this script.

    Args:
        soft (str): Software to execute (SU2_DEF, SU2_CFD, SU2_SOL)
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    # Get installation path for the following softwares
    SOFT_DICT = ceaf.get_install_path(SOFT_LIST)

    # mpi_install_path = SOFT_DICT['mpirun.mpich']
    mpi_install_path = SOFT_DICT['mpirun']

    soft_install_path = SOFT_DICT[soft]

    log.info('Number of proc available: ' + str(os.cpu_count()))
    log.info(str(nb_proc) +' will be used for this calculation.')

    logfile_path = os.path.join(wkdir,'logfile' + soft + '.log')

    # if mpi_install_path is not None:
    #     command_line =  [mpi_install_path,'-np',str(nb_proc),
    #                      soft_install_path,config_path,'>',logfile_path]
    if mpi_install_path is not None:
        command_line =  [mpi_install_path,'-np',str(int(nb_proc)),
                         soft_install_path,config_path,'>',logfile_path]
    # elif soft == 'SU2_DEF' a disp.dat must be there to run with MPI
    else:
        command_line = [soft_install_path,config_path,'>',logfile_path]

    original_dir = os.getcwd()
    os.chdir(wkdir)

    log.info('>>> ' + soft + ' Start Time')

    os.system(' '.join(command_line))

    log.info('>>> ' + soft + ' End Time')

    os.chdir(original_dir)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')


### HOW TO IMPORT THESE MODULES

#  from ceasiompy.utils.su2functions import read_config, write_config, get_mesh_marker
