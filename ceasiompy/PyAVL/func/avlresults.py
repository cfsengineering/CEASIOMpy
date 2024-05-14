"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-18

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import CEASIOMPY_XPATH

from cpacspy.cpacsfunctions import get_value
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def get_avl_aerocoefs(force_file):
    """Get aerodynamic coefficients and velocity from AVL forces file (forces.txt)

    Args:
        force_file (Path): Path to the SU2 forces file

    Returns:
        cl, cd, cs, cmd, cms, cml: Aerodynamic coefficients
    """

    if not force_file.is_file():
        raise FileNotFoundError(f"The AVL forces file '{force_file}' has not been found!")

    cl, cd = None, None

    with open(force_file) as f:
        for line in f.readlines():
            if "CLtot" in line:
                cl = float(line.split("=")[1].strip())
            if "CDtot" in line:
                cd = float(line.split("=")[1].strip())
            if "Cmtot" in line:
                cm = float(line.split("=")[2].strip())

    return cl, cd, cm


def get_avl_results(cpacs_path, cpacs_out_path, wkdir):
    """Function to write AVL results in a CPACS file.

    Function 'get_avl_results' gets available results from the latest AVL calculation and put them
    at the correct place in the CPACS file.

    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aeroMap[n]/aeroPerformanceMap'

    Args:
        cpacs_path (Path): Path to input CPACS file
        cpacs_out_path (Path): Path to output CPACS file
        wkdir (Path): Path to the working directory

    """

    cpacs = CPACS(cpacs_path)
    AVL_XPATH = CEASIOMPY_XPATH + "/aerodynamics/avl"
    AVL_AEROMAP_UID_XPATH = AVL_XPATH + "/aeroMapUID"

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exit!")

    aeromap_uid = get_value(cpacs.tixi, AVL_AEROMAP_UID_XPATH)

    log.info(f"The aeromap uid is: {aeromap_uid}")
    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    alt_list = aeromap.get("altitude").tolist()
    mach_list = aeromap.get("machNumber").tolist()
    aoa_list = aeromap.get("angleOfAttack").tolist()
    aos_list = aeromap.get("angleOfSideslip").tolist()

    case_dir_list = [case_dir for case_dir in wkdir.iterdir() if "Case" in case_dir.name]

    for config_dir in sorted(case_dir_list):

        if not config_dir.is_dir():
            continue

        force_file_path = Path(config_dir, "ft.txt")
        if not force_file_path.exists():
            raise OSError("No result force file have been found!")

        case_nb = int(config_dir.name.split("_")[0].split("Case")[1])

        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]
        mach = mach_list[case_nb]
        alt = alt_list[case_nb]

        cl, cd, cm = get_avl_aerocoefs(force_file_path)

        aeromap.add_coefficients(
            alt=alt,
            mach=mach,
            aos=aos,
            aoa=aoa,
            cd=cd,
            cl=cl,
            cms=cm
        )
    aeromap.save()
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
