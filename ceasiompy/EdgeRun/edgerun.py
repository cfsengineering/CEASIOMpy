"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for Airinnova AB, Stockholm, Sweden

Functions to manipulate Edge input file and results (TO-DO)

Python version: >=3.8

| Author : Mengmeng Zhang
| Creation: 2024-01-05
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================
import os, re
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.EdgeRun.func.edgeconfig import edge_cfd
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import (
    get_reasonable_nb_cpu,
    get_results_directory,
    #    run_software,
)

# from ceasiompy.utils.commonnames import AINP_CFD_NAME, SU2_FORCES_BREAKDOWN_NAME
from cpacspy.cpacsfunctions import (
    create_branch,
    get_string_vector,
    get_value,
    get_value_or_default,
)
from ceasiompy.utils.commonnames import AINP_CFD_NAME
from ceasiompy.utils.commonxpath import EDGE_NB_CPU_XPATH, EDGE_MESH_XPATH
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from cpacspy.cpacsfunctions import get_value_or_default, open_tixi
from ceasiompy.EdgeRun.func.edge_queScript_gen import EdgeScripts
from ceasiompy.EdgeRun.func.edgeutils import get_edge_queScript_template

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================
input_que_script_path = get_edge_queScript_template()


def run_edge_multi(wkdir, input_que_script_path, nb_proc=2):
    """Function to run a multiple Edge calculation.

    Function 'run_edge_multi' will run in the given working directory Edge calculations.
    The working directory must have a folder structure created by 'SU2Config'/ 'EdgeConfig' module.

    Args:
        wkdir (Path): Path to the working directory
        nb_proc (int): Number of processor that should be used to run the calculation in parallel
    """
    cpacs = CPACS(cpacs_path)

    edge_mesh = Path(get_value(cpacs.tixi, EDGE_MESH_XPATH))

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exist!")

    case_dir_name = (
        f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
        f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
    )

    case_dir_path = Path(wkdir, case_dir_name)
    if not case_dir_path.exists():
        case_dir_path.mkdir()
    output_path = Path(case_dir_path, AINP_CFD_NAME)


    case_dir_list = [dir for dir in wkdir.iterdir() if "Case" in dir.name]
    if not case_dir_list:
        raise OSError(f"No Case directory has been found in the working directory: {wkdir}")

    for config_dir in sorted(case_dir_list):
        current_dir = Path(case_dir_path, config_dir)

        config_cfd = [c for c in config_dir.iterdir() if c.name == AINP_CFD_NAME]

        if not config_cfd:
            raise ValueError(f"No '{AINP_CFD_NAME}' file has been found in this directory!")

        if len(config_cfd) > 1:
            raise ValueError(f"More than one '{AINP_CFD_NAME}' file in this directory!")

        # run / submit edge commands
        edge_scripts_instance = EdgeScripts(current_dir, input_que_script_path, AINP_CFD_NAME)
        # check if preprocessor is already run
        bedg_files_exist = True
        for i in range(1, nb_proc + 1):
            bedg_file_path = Path(case_dir_path, grid_folder, f"Edge.bedg_p{i}")
            if not bedg_file_path.exists():
                bedg_files_exist = False
                break
        if not bedg_files_exist:
            # edge_scripts_instance.submit_preprocessor_script(case_dir_path)
            edge_scripts_instance.run_preprocessor(case_dir_path)
            print("bedg files are generated")

        # edge_scripts_instance.submit_solver_script(nb_proc)
        edge_scripts_instance.run_solver(nb_proc)

        # postprocess for results
        edge_scripts_instance.postprocess_script(case_dir_path, edge_mesh)

def extract_edge_forces(results_dir):
    # Use list comprehension to get a list of directory names starting with "Case"
    dir_names = [dir_name for dir_name in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, dir_name)) and dir_name.startswith("Case")]

    # Define the header for the forcemoments file
    header = " alt   mach  alfa beta     CL          CD          CDP         CDV         CM   "


    # Loop through the list and perform actions in each directory
    for dir_name in dir_names:
        dir_path = os.path.join(results_dir, dir_name)
        #print(f"Processing directory: {dir_path}")
        log.info(f"Extracting forces from Directory : {dir_name}")
    
        # Extract mach and alfa from directory name
        match = re.match(r'.*alt(\d+\.\d+)_mach(\d+\.\d+)_aoa(\d+\.\d+)_aos(\d+\.\d+)*', dir_name)
        if match:
            alt = float(match.group(1))
            mach = float(match.group(2))
            aoa = float(match.group(3))
            aos = float(match.group(4))
            #print(f"  - alt: {alt}, mach: {mach}, aoa: {aoa}, aos: {aos}")

            # Extract information from Edge.log file
            filelog = os.path.join(dir_path, 'Edge.log')
            with open(filelog, 'r') as log_file:
                lines = log_file.readlines()

            total_line_number = next((i for i, line in enumerate(lines) if ' Total:' in line), None)
            if total_line_number is not None:
                line = total_line_number + 4
                CL = lines[line].split()[0]
                CD = lines[line].split()[1]
                CM = lines[line].split()[3]

                line += 2
                CDP = lines[line].split()[1]

                line += 2
                CDV = lines[line].split()[1]

                # Append values to forcemoments file
                forcemoments = os.path.join(results_dir, 'Edge_force_moment.dat')
                with open(forcemoments, 'a') as output_file:
                    # Check if the file is empty and add the header
                    if os.stat(forcemoments).st_size == 0:
                        output_file.write(header + "\n")
                    output_file.write(f"{alt:.8f} {mach:.8f} {aoa:.8f} {aos:.8f} {CL} {CD} {CDP} {CDV} {CM}\n")
                    log.info(f"Saving forces to file: {forcemoments}")

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    tixi = open_tixi(cpacs_path)
    nb_proc = get_value_or_default(tixi, EDGE_NB_CPU_XPATH, get_reasonable_nb_cpu())

    results_dir = get_results_directory("EdgeRun")

    # Temporary CPACS to be stored after "generate_edge_cfd_ainp"
    cpacs_tmp_cfg = Path(cpacs_out_path.parent, "ConfigTMP.xml")

    edge_cfd(cpacs_path, cpacs_tmp_cfg, results_dir)
    extract_edge_forces(results_dir)
    log.info("Edge Postprocess finished")
    # run_edge_multi(results_dir, nb_proc)
    # get_su2_results(cpacs_tmp_cfg, cpacs_out_path, results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
