"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.

| Author: Leon Deligny
| Creation: 2025-Feb-14

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import subprocess

import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from ceasiompy import log


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def convert_ps_to_pdf(wkdir: Path) -> None:
    """
    Function to convert AVL 'plot.ps' to 'plot.pdf'.

    Args:
        wkdir (Path): Path to the working directory.

    """
    if not Path(wkdir, "plot.ps").exists():
        log.warning("File 'plot.ps' does not exist. Nothing to convert.")
    else:
        subprocess.run(["ps2pdf", "plot.ps", "plot.pdf"], cwd=wkdir)
        subprocess.run(["rm", "plot.ps"], cwd=wkdir)


def plot_lift_distribution(
    force_file_fs: Path,
    aoa: float,
    aos: float,
    mach: float,
    alt: float,
    wkdir: Path
) -> None:
    """
    Plot the lift distribution from AVL strip forces file (fs.txt)

    Args:
        force_file_fs (Path): Path to the AVL strip forces file.
        aoa (float): Angle of attack [deg].
        aos (float): Angle of sideslip [deg].
        mach (float): Mach number.
        alt (float): Flight altitude [m].
        wkir (Path): Path to the directory on where to save the plot.

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

    data_df = pd.DataFrame({
        "y": y_list,
        "chord": chord_list,
        "cl": cl_list,
        "cl_norm": clnorm_list
    })

    data_df.sort_values(by="y", inplace=True)
    data_df.reset_index(drop=True, inplace=True)
    data_df["cl_cref"] = data_df["cl"] * data_df["chord"] / cref

    _, ax = plt.subplots(figsize=(10, 5))
    data_df.plot("y", "cl_norm", ax=ax, label=r"$c_{l\perp}$", linestyle="dashed", color="r")
    data_df.plot("y", "cl", label=r"$c_l$", ax=ax, linestyle="dashed", color="#FFA500")
    data_df.plot(
        "y", "cl_cref", ax=ax, label=r"$c_l \cdot C/C_{ref}$", linestyle="solid", color="#41EE33"
    )

    plt.title(
        (
            "Lift distribution along the wing span "
            r"($\alpha=%.1f^{\circ}$, $\beta=%.1f^{\circ}$, "
            r"$M=%.1f$, alt = %d m)"
        )
        % (aoa, aos, mach, alt),
        fontsize=14,
    )

    plt.ylabel(r"$C_l$", rotation=0, fontsize=12)
    plt.legend(fontsize=12)
    plt.grid()
    plt.savefig(Path(wkdir, "lift_distribution.png"))

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
