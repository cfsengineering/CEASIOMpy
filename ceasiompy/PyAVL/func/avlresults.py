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
import pandas as pd
import matplotlib.pyplot as plt

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import AVL_AEROMAP_UID_XPATH

from cpacspy.cpacsfunctions import get_value
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_lift_distribution(force_file_fs, aoa, aos, mach, alt, wkdir):
    """Plot the lift distribution from AVL strip forces file (fs.txt)

    Args:
        force_file_fs (Path): Path to the AVL strip forces file
        aoa (float): angle of attack [deg]
        aos (float): angle of sideslip [deg]
        mach (float): mach number
        alt (float): flight altitude [m]
        wkir (path): path to save the plot

    Returns:
    """
    y_list = []
    chord_list = []
    cl_list = []
    clnorm_list = []

    with open(force_file_fs, "r") as fs:
        for line in fs:
            if "Cref =" in line:
                cref = float(line.split()[5])

            elif "# Spanwise =" in line:
                number_strips = int(line.split()[7])

            elif "Xle" in line:
                number_data = 0
                for line in fs:
                    data = line.split()
                    y_list.append(float(data[2]))
                    chord_list.append(float(data[4]))
                    cl_list.append(float(data[9]))
                    clnorm_list.append(float(data[8]))
                    number_data += 1

                    # break when every line has been extracted
                    if number_data == number_strips:
                        break

    data_df = pd.DataFrame(
        {"y": y_list, "chord": chord_list, "cl": cl_list, "cl_norm": clnorm_list}
    )

    data_df.sort_values(by="y", inplace=True)
    data_df.reset_index(drop=True, inplace=True)
    data_df["cl_cref"] = data_df["cl"] * data_df["chord"] / cref

    _, ax = plt.subplots(figsize=(10, 5))
    data_df.plot("y", "cl_norm", ax=ax, label="$c_{l\perp}$", linestyle="dashed", color="r")
    data_df.plot("y", "cl", label="$c_l$", ax=ax, linestyle="dashed", color="#FFA500")
    data_df.plot(
        "y", "cl_cref", ax=ax, label="$c_l \cdot C/C_{ref}$", linestyle="solid", color="#41EE33"
    )

    plt.title(
        (
            "Lift distribution along the wing span "
            "($\\alpha=%.1f^{\circ}$, $\\beta=%.1f^{\circ}$, "
            "$M=%.1f$, alt = %d m)"
        )
        % (aoa, aos, mach, alt),
        fontsize=14,
    )

    plt.ylabel("$C_l$", rotation=0, fontsize=12)
    plt.legend(fontsize=12)
    plt.grid()
    plt.savefig(Path(wkdir, "lift_distribution.png"))


def get_avl_aerocoefs(force_file_ft):
    """Get aerodynamic coefficients and velocity from AVL total forces file (ft.txt)

    Args:
        force_file_ft (Path): Path to the AVL total forces file

    Returns:
        cl, cd, cs, cmd, cms, cml: Aerodynamic coefficients
    """

    if not force_file_ft.is_file():
        raise FileNotFoundError(f"The AVL forces file '{force_file_ft}' has not been found!")

    cl, cd = None, None

    with open(force_file_ft) as f:
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

        ft_file_path = Path(config_dir, "ft.txt")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        for path in Path(config_dir).rglob('*'):
            print(path)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

        if not ft_file_path.exists():
            raise OSError("No result total forces file have been found!")

        fs_file_path = Path(config_dir, "fs.txt")
        if not fs_file_path.exists():
            raise OSError("No result strip forces file have been found!")

        case_nb = int(config_dir.name.split("_")[0].split("Case")[1])

        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]
        mach = mach_list[case_nb]
        alt = alt_list[case_nb]

        cl, cd, cm = get_avl_aerocoefs(ft_file_path)
        plot_lift_distribution(fs_file_path, aoa, aos, mach, alt, wkdir=config_dir)

        aeromap.add_coefficients(alt=alt, mach=mach, aos=aos, aoa=aoa, cd=cd, cl=cl, cms=cm)
    aeromap.save()
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
