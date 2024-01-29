"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by Airinnova AB, Stockholm, Sweden

Function generate or modify M-Edge ainp files

Python version: >=3.8

| Author: Mengmeng Zhang
| Creation: 2024-01-05

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math, os

from pathlib import Path
from shutil import copyfile

from ambiance import Atmosphere

# from ceasiompy.SU2Run.func.su2actuatordiskfile import (
#    get_advanced_ratio,
#    get_radial_stations,
#    save_plots,
#    thrust_calculator,
#    write_actuator_disk_data,
#    write_header,
# )

# from ceasiompy.EdgeRun.func.edgeutils import get_edge_ainp_template
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import (
    AINP_CFD_NAME,
)
from ceasiompy.utils.commonxpath import (
    GMSH_SYMMETRY_XPATH,
    RANGE_XPATH,
    EDGE_MESH_XPATH,
    EDGE_AEROMAP_UID_XPATH,
    EDGE_SOLVER_XPATH,
    EDGE_CFL_NB_XPATH,
    EDGE_MAX_ITER_XPATH,
    EDGE_MG_LEVEL_XPATH,
    EDGE_NB_CPU_XPATH,
    EDGE_FIXED_CL_XPATH,
)

# from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.create_ainpfile import CreateAinp
from cpacspy.cpacsfunctions import (
    create_branch,
    get_string_vector,
    get_value,
    get_value_or_default,
)
from cpacspy.cpacspy import CPACS
from ceasiompy.EdgeRun.func.edgeutils import get_edge_queScript_template
from ceasiompy.EdgeRun.func.edge_queScript_gen import EdgeScripts

# import cpacs

log = get_logger()

MODULE_DIR = Path(__file__).parent

input_que_script_path = get_edge_queScript_template()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def edge_cfd(cpacs_path, cpacs_out_path, wkdir):
    # output_path = Path(case_dir_path, AINP_CFD_NAME)
    """Function to create Edge input (*.ainp) file.

    Function 'generate_edge_cfd_ainp' reads data in the CPACS file and generate configuration
    files for one or multiple flight conditions (alt,mach,aoa,aos)

    Source:
        * M-Edge ainp template:

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file
        wkdir (Path): Path to the working directory

    """

    cpacs = CPACS(cpacs_path)

    edge_mesh = Path(get_value(cpacs.tixi, EDGE_MESH_XPATH))
    edge_aboc = edge_mesh.with_suffix(".aboc")

    if not edge_mesh.is_file():
        raise FileNotFoundError(f"M-Edge mesh file {edge_mesh} not found")
    # copy edge_mesh and edge_aboc file to the Working directory

    grid_folder = Path(wkdir, "grid")
    # grid_folder = Path(wkdir) # Added by Mengmeng Zhang
    to_grid = grid_folder / edge_mesh.name
    to_aboc = grid_folder / edge_aboc.name

    if not os.path.exists(grid_folder):
        os.makedirs(grid_folder)
    copyfile(edge_mesh, to_grid)
    copyfile(edge_aboc, to_aboc)

    # Get the fixedCL value from CPACS
    fixed_cl = get_value_or_default(cpacs.tixi, EDGE_FIXED_CL_XPATH, "NO")
    if fixed_cl == "NO":
        # Get the first aeroMap as default one or create automatically one
        aeromap_list = cpacs.get_aeromap_uid_list()

        if aeromap_list:
            aeromap_default = aeromap_list[0]
            log.info(f"The aeromap is {aeromap_default}")

            aeromap_uid = get_value_or_default(cpacs.tixi, EDGE_AEROMAP_UID_XPATH, aeromap_default)

            activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
            alt_list = activate_aeromap.get("altitude").tolist()
            mach_list = activate_aeromap.get("machNumber").tolist()
            aoa_list = activate_aeromap.get("angleOfAttack").tolist()
            aos_list = activate_aeromap.get("angleOfSideslip").tolist()

        else:
            default_aeromap = cpacs.create_aeromap("DefaultAeromap")
            default_aeromap.description = "AeroMap created automatically"

            mach = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseMach", 0.3)
            alt = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseAltitude", 10000)

            default_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
            default_aeromap.save()

            alt_list = [alt]
            mach_list = [mach]
            aoa_list = [0.0]
            aos_list = [0.0]

            aeromap_uid = get_value_or_default(
                cpacs.tixi, EDGE_AEROMAP_UID_XPATH, "DefaultAeromap"
            )
            log.info(f"{aeromap_uid} has been created")

    else:  # if fixed_cl == 'YES':
        log.info("Configuration file for fixed CL calculation will be created.")

        fixed_cl_aeromap = cpacs.create_aeromap("aeroMap_fixedCL_SU2")
        # fixed_cl_aeromap.description = f"AeroMap created for SU2 fixed CL value of {target_cl}"

        mach = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseMach", 0.78)
        alt = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseAltitude", 12000)

        fixed_cl_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
        fixed_cl_aeromap.save()

        alt_list = [alt]
        mach_list = [mach]
        aoa_list = [0.0]
        aos_list = [0.0]

    # cfg = ConfigFile(get_su2_config_template())

    # Check if symmetry plane is defined (Default: False)
    sym_factor = 1.0
    if get_value_or_default(cpacs.tixi, GMSH_SYMMETRY_XPATH, False):
        log.info("Symmetry plane is defined. The reference area will be divided by 2.")
        sym_factor = 2.0

    # General parameters
    #
    BMSH = edge_mesh.name
    ABOC = edge_aboc.name
    CREF = cpacs.aircraft.ref_length
    SREF = cpacs.aircraft.ref_area / sym_factor
    BREF = SREF / CREF
    IXMP = [cpacs.aircraft.ref_point_x, cpacs.aircraft.ref_point_y, cpacs.aircraft.ref_point_z]

    # Settings

    ITMAX = int(get_value_or_default(cpacs.tixi, EDGE_MAX_ITER_XPATH, 1000))
    CFL = get_value_or_default(cpacs.tixi, EDGE_CFL_NB_XPATH, 1.5)
    NGRID = int(get_value_or_default(cpacs.tixi, EDGE_MG_LEVEL_XPATH, 1))
    NPART = int(get_value_or_default(cpacs.tixi, EDGE_NB_CPU_XPATH, 128))

    edge_solver = get_value_or_default(cpacs.tixi, EDGE_SOLVER_XPATH,"Euler")
    print(f'edge_solver: {edge_solver}')  
    if edge_solver == "Euler":
        INSEUL = 0
    if edge_solver == "RANS":
        INSEUL = 1
    else:
        raise Exception("Error, edge solver not assigned")

    # Parameters which will vary for the different cases (alt,mach,aoa,aos)
    for case_nb in range(len(alt_list)):
        # cfg["MESH_FILENAME"] = str(su2_mesh)

        alt = alt_list[case_nb]
        mach = mach_list[case_nb]
        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]

        Atm = Atmosphere(alt)

        PFREE = Atm.pressure[0]
        TFREE = Atm.temperature[0]
        speedofsound = Atm.speed_of_sound[0]
        airspeed = mach * speedofsound

        # aoa_rad = math.radians(aoa)
        # aos_rad = math.radians(aos)

        UFREE = airspeed * math.cos(aos) * math.cos(aoa)
        WFREE = airspeed * math.cos(aos) * math.sin(aoa)
        VFREE = airspeed * math.sin(aos) * (-1)

        IDCDP1 = math.cos(aos) * math.cos(aoa)
        IDCDP2 = math.sin(aos)
        IDCDP3 = math.cos(aos) * math.sin(aoa)

        IDCLP1 = math.sin(aoa) * (-1)
        IDCLP2 = 0
        IDCLP3 = math.cos(aoa)

        IDCCP1 = math.cos(aoa) * math.sin(aos) * (-1)
        IDCCP2 = math.cos(aos) * (-1)
        IDCCP3 = math.sin(aoa) * math.sin(aos) * (-1)
        IDCMP1 = IDCCP1
        IDCMP2 = IDCCP2
        IDCMP3 = IDCCP3
        IDCNP1 = IDCLP1
        IDCNP2 = IDCLP2
        IDCNP3 = IDCLP3
        IDCRP1 = IDCDP1
        IDCRP2 = IDCDP2
        IDCRP3 = IDCDP3

        IDCLP = f"{IDCLP1} {IDCLP2} {IDCLP3}"
        IDCDP = f"{IDCDP1} {IDCDP2} {IDCDP3}"
        IDCMP = f"{IDCMP1} {IDCMP2} {IDCMP3}"
        IDCCP = f"{IDCCP1} {IDCCP2} {IDCCP3}"
        IDCNP = f"{IDCNP1} {IDCNP2} {IDCNP3}"
        IDCRP = f"{IDCRP1} {IDCRP2} {IDCRP3}"

        case_dir_name = (
            f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
        )

        case_dir_path = Path(wkdir, case_dir_name)
        if not case_dir_path.exists():
            case_dir_path.mkdir()
        output_file_withpath = Path(case_dir_path, AINP_CFD_NAME)
        # template_path = get_edge_ainp_template()
        create_ainp_instance = CreateAinp()
        # create_ainp_instance = CreateAinp(get_edge_ainp_template())

        create_ainp_instance.create_ainp(
            BMSH,
            ABOC,
            UFREE,
            VFREE,
            WFREE,
            TFREE,
            PFREE,
            SREF,
            CREF,
            BREF,
            IXMP,
            IDCLP,
            IDCDP,
            IDCCP,
            IDCMP,
            IDCNP,
            IDCRP,
            NPART,
            ITMAX,
            INSEUL,
            NGRID,
            CFL,
            output_file_withpath,
        )

        # cfg.write_file(config_output_path, overwrite=True)
        # create and submit the edge-run scripts
        # run / submit edge commands

        jobname = case_dir_name
        edge_scripts_instance = EdgeScripts(
            jobname, case_dir_path, input_que_script_path, AINP_CFD_NAME
        )

        bedg_files_exist = True
        for i in range(1, NPART + 1):
            bedg_file_path = Path(case_dir_path, grid_folder, f"Edge.bedg_p{i}")
            if not bedg_file_path.exists():
                bedg_files_exist = False
                break

        if not bedg_files_exist:
            # edge_scripts_instance.submit_preprocessor_script(case_dir_path)
            log.info("Running Edge preprocessor ...")
            edge_scripts_instance.run_preprocessor(case_dir_path)
            log.info("Preprocessor is done. *.bedg files are generated")

        # edge_scripts_instance.submit_solver_script(case_dir_path,NPART)
        log.info("Running Edge solver... for " + case_dir_name)
        edge_scripts_instance.run_edgesolver(case_dir_path, NPART)
        log.info("Edge solver is done.")

        # postprocess for results
        log.info("Running Edge postprocessor...for " + case_dir_name)
        edge_scripts_instance.postprocess_script(case_dir_path, edge_mesh)
        log.info("Edge postprocessor is done.")
        # wait until the results are generated

        cpacs.save_cpacs(cpacs_out_path, overwrite=True)

        # =================================================================================================
        #    MAIN
        # =================================================================================================

        if __name__ == "__main__":
            log.info("Nothing to execute!")
