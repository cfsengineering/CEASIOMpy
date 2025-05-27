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

import os
import re

from pathlib import Path

from ceasiompy import log

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def extract_edge_forces(results_dir: Path):
    # Use list comprehension to get a list of directory names starting with "Case"
    dir_names = [
        dir_name
        for dir_name in os.listdir(results_dir)
        if os.path.isdir(os.path.join(results_dir, dir_name)) and dir_name.startswith("Case")
    ]

    # Define the header for the forcemoments file
    header = " alt   mach  alfa beta     CL          CD          CDP         CDV         CM   "

    # Loop through the list and perform actions in each directory
    for dir_name in dir_names:
        dir_path = os.path.join(results_dir, dir_name)
        log.info(f"Extracting forces from Directory : {dir_name}")

        # Extract mach and alfa from directory name
        match = re.match(r".*alt(\d+\.\d+)_mach(\d+\.\d+)_aoa(\d+\.\d+)_aos(\d+\.\d+)*", dir_name)
        if match:
            alt = float(match.group(1))
            mach = float(match.group(2))
            aoa = float(match.group(3))
            aos = float(match.group(4))

            # Extract information from Edge.log file
            filelog = os.path.join(dir_path, "Edge.log")
            with open(filelog, "r") as log_file:
                lines = log_file.readlines()

            total_line_number = next(
                (i for i, line in enumerate(lines) if " Total:" in line), None
            )
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
                forcemoments = os.path.join(results_dir, "Edge_force_moment.dat")
                with open(forcemoments, "a") as output_file:
                    # Check if the file is empty and add the header
                    if os.stat(forcemoments).st_size == 0:
                        output_file.write(header + "\n")
                    output_file.write(
                        f"{alt:.8f} {mach:.8f} {aoa:.8f} {aos:.8f} {CL} {CD} {CDP} {CDV} {CM}\n"
                    )
                    log.info(f"Saving forces to file: {forcemoments}")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
