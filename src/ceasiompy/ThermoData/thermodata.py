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

from ceasiompy.ThermoData.func.turbofan import (
    write_hbtf_file,
    turbofan_analysis,
)
from ceasiompy.ThermoData.func.turbojet import (
    turbojet_analysis,
    write_turbojet_file,
)
from cpacspy.cpacsfunctions import (
    create_branch,
    add_float_vector,
    get_value_or_default,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.SU2Run import SU2_AEROMAP_UID_XPATH
from ceasiompy.utils.commonnames import ENGINE_BOUNDARY_CONDITIONS
from ceasiompy.utils.guixpaths import (
    RANGE_XPATH,
    RANGE_CRUISE_ALT_XPATH,
    RANGE_CRUISE_MACH_XPATH,
)
from ceasiompy.ThermoData import (
    THERMODATA_XPATH,
    THERMODATA_PRESSUREOUTLET_XPATH,
    THERMODATA_TEMPERATUREOUTLET_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Running the PyCycle code by choosing between turbojet or turbofan engine
    """

    tixi = gui_settings.tixi
    Fn = get_value_or_default(tixi, RANGE_XPATH + "/NetForce", 2000)

    default_aeromap = cpacs.create_aeromap("DefaultAeromap")
    default_aeromap.description = "AeroMap created automatically"
    mach = get_value_or_default(tixi, RANGE_CRUISE_MACH_XPATH, 0.3)
    alt = get_value_or_default(tixi, RANGE_CRUISE_ALT_XPATH, 10000)
    default_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
    default_aeromap.save()
    alt_list = [alt]
    mach_list = [mach]
    aeromap_uid = get_value_or_default(tixi, SU2_AEROMAP_UID_XPATH, "DefaultAeromap")
    log.info(f"{aeromap_uid} has been created")

    aeromap_list = cpacs.get_aeromap_uid_list()

    if not aeromap_list:
        log.warning("Could not compute Thermodata as did not find any AeroMap.")

    aeromap_default = aeromap_list[0]
    log.info(f"The aeromap is {aeromap_default}")
    aeromap_uid = get_value_or_default(tixi, SU2_AEROMAP_UID_XPATH, aeromap_default)
    activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
    alt_list = activate_aeromap.get("altitude").tolist()
    mach_list = activate_aeromap.get("machNumber").tolist()
    T_tot_out_array = []
    P_tot_out_array = []

    for case_nb, alt in enumerate(alt_list):
        alt = alt_list[case_nb]
        MN = mach_list[case_nb]
        case_dir_name = f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(MN, 2)}"
        case_dir_path = Path(results_dir, case_dir_name)

        if not case_dir_path.exists():
            case_dir_path.mkdir()

            EngineBC = Path(case_dir_path, ENGINE_BOUNDARY_CONDITIONS)

            f = open(EngineBC, "w")

            engine_type = get_value_or_default(tixi, THERMODATA_XPATH, 0)
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
                    t_tot_out_byp=T_tot_out_byp,
                    v_stat_out_byp=V_stat_out_byp,
                    mn_out_byp=MN_out_byp,
                    p_tot_out_byp=P_tot_out_byp,
                    massflow_stat_out_byp=massflow_stat_out_byp,
                    t_stat_out_byp=T_stat_out_byp,
                    t_tot_out_core=T_tot_out_core,
                    v_stat_out_core=V_stat_out_core,
                    mn_out_core=MN_out_core,
                    p_tot_out_core=P_tot_out_core,
                    massflow_stat_out_core=massflow_stat_out_core,
                    t_stat_out_core=T_stat_out_core,
                )
    add_float_vector(tixi, THERMODATA_TEMPERATUREOUTLET_XPATH, T_tot_out_array)
    add_float_vector(tixi, THERMODATA_PRESSUREOUTLET_XPATH, P_tot_out_array)
    log.info("Updating T_tot_out_array and P_tot_out_array.")
    shutil.rmtree("reports", ignore_errors=True)
