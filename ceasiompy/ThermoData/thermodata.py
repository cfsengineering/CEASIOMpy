"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate outlet conditions fot turbojet and turbofan engines by using the open source code PyCycle
and saving those conditions in a text file

| Author: Francesco Marcucci
| Creation: 2023-12-12
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
from pathlib import Path

from ceasiompy.ThermoData.func.turbofan_func import (
    turbofan_analysis,
    write_hbtf_file,
)

from ceasiompy.ThermoData.func.turbojet_func import (
    turbojet_analysis,
    write_turbojet_file,
)

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.moduleinterfaces import (
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import (
    ENGINE_TYPE_XPATH,
    ENGINE_BC,
    RANGE_XPATH,
    SU2_AEROMAP_UID_XPATH,
)
from ceasiompy.utils.commonnames import (
    ENGINE_BOUNDARY_CONDITIONS,
)
from cpacspy.cpacsfunctions import (
    get_value_or_default,
    add_float_vector,
    create_branch,
)
from cpacspy.cpacspy import CPACS


log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def thermo_data_run(cpacs_path, cpacs_out_path, wkdir):
    """Running the PyCycle code by choosing between turbojet or turbofan engine

    Args
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file
        wkdir (str): Path to the working directory
    """

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exit!")

    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    Fn = get_value_or_default(tixi, RANGE_XPATH + "/NetForce", 2000)

    aeromap_list = cpacs.get_aeromap_uid_list()

    if aeromap_list:
        aeromap_default = aeromap_list[0]
        log.info(f"The aeromap is {aeromap_default}")
        aeromap_uid = get_value_or_default(cpacs.tixi, SU2_AEROMAP_UID_XPATH, aeromap_default)
        activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
        alt_list = activate_aeromap.get("altitude").tolist()
        mach_list = activate_aeromap.get("machNumber").tolist()
        T_tot_out_array = []
        P_tot_out_array = []

        for case_nb, alt in enumerate(alt_list):
            alt = alt_list[case_nb]
            MN = mach_list[case_nb]
            case_dir_name = f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(MN, 2)}"
            case_dir_path = Path(wkdir, case_dir_name)

            if not case_dir_path.exists():
                case_dir_path.mkdir()

                EngineBC = Path(case_dir_path, ENGINE_BOUNDARY_CONDITIONS)

                f = open(EngineBC, "w")

                engine_type = get_value_or_default(tixi, ENGINE_TYPE_XPATH, 0)
                create_branch(cpacs.tixi, ENGINE_BC)

                if engine_type == 0:
                    (
                        T_tot_out,
                        V_stat_out,
                        MN_out,
                        P_tot_out,
                        massflow_stat_out,
                        T_stat_out,
                        P_stat_out,
                    ) = turbojet_analysis(alt, MN, Fn)

                    T_tot_out_array.append(T_tot_out)
                    P_tot_out_array.append(P_tot_out)

                    f = write_turbojet_file(
                        file=f,
                        T_tot_out=T_tot_out,
                        V_stat_out=V_stat_out,
                        MN_out=MN_out,
                        P_tot_out=P_tot_out,
                        massflow_stat_out=massflow_stat_out,
                        T_stat_out=T_stat_out,
                        P_stat_out=P_stat_out,
                    )

                else:

                    (
                        T_tot_out_byp,
                        V_stat_out_byp,
                        MN_out_byp,
                        P_tot_out_byp,
                        massflow_stat_out_byp,
                        T_stat_out_byp,
                        T_tot_out_core,
                        V_stat_out_core,
                        MN_out_core,
                        P_tot_out_core,
                        massflow_stat_out_core,
                        T_stat_out_core,
                    ) = turbofan_analysis(alt, MN, Fn)

                    T_tot_out_array.append(T_tot_out_core)
                    P_tot_out_array.append(P_tot_out_core)

                    f = write_hbtf_file(
                        file=f,
                        T_tot_out_byp=T_tot_out_byp,
                        V_stat_out_byp=V_stat_out_byp,
                        MN_out_byp=MN_out_byp,
                        P_tot_out_byp=P_tot_out_byp,
                        massflow_stat_out_byp=massflow_stat_out_byp,
                        T_stat_out_byp=T_stat_out_byp,
                        T_tot_out_core=T_tot_out_core,
                        V_stat_out_core=V_stat_out_core,
                        MN_out_core=MN_out_core,
                        P_tot_out_core=P_tot_out_core,
                        massflow_stat_out_core=massflow_stat_out_core,
                        T_stat_out_core=T_stat_out_core,
                    )
        add_float_vector(tixi, ENGINE_BC + "/temperatureOutlet", T_tot_out_array)
        add_float_vector(tixi, ENGINE_BC + "/pressureOutlet", P_tot_out_array)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    results_dir = get_results_directory("ThermoData")

    thermo_data_run(cpacs_path, cpacs_out_path, results_dir)

    folder_name = "reports"

    shutil.rmtree(folder_name)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
