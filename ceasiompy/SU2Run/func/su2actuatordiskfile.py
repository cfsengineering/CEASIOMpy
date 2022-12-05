"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to generate the actuator disk file for SU2.

Source: https://github.com/su2code/SU2/blob/master/TestCases/rans/
        actuatordisk_variable_load/ActuatorDisk.dat

Python version: >=3.8

| Author : Aidan Jungo and Giacomo Benedetti
| Creation: 2022-12-05

TODO:


"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_radial_stations(radius, hub_radius, number_of_stations=40):
    """Function to adimensionalize the radius and remove values smaller than hub radius.

    Args:
        radius (float): Propeller radius [m]
        hub_radius (float): Hub radius [m]

    Returns:
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                    get the real radius value
    """

    if hub_radius >= radius:
        raise ValueError("hub radius should be smaller than radius")

    radial_stations = np.linspace(0, 1, number_of_stations + 1)[1:]
    i_hub = np.abs(radial_stations - hub_radius / radius).argmin()

    if radial_stations[i_hub] < hub_radius:
        i_hub += 1
    return radial_stations[i_hub:]


def write_header(file):
    """Write the header of the actuator disk file

    Args:
        file (file): File to write the header

    """

    file.write("# Automatic generated actuator disk input data file using\n")
    file.write("# the Optimal Propeller code.\n")
    file.write("# Data file needed for the actuator disk VARIABLE_LOAD type.\n")
    file.write("# The load distribution is obtained using\n")
    file.write("# the inviscid theory of the optimal propeller using global data.\n")
    file.write("#\n")
    file.write("# ADV_RATIO defined as Vinf/(nD) where: \n")
    file.write("#    n: propeller rounds per second,\n")
    file.write("#    D: propeller diameter.\n")
    file.write("# 'Renard' definition of propeller coefficients:\n")
    file.write("# reference force = rho*n^2*D^4, reference power = rho*n^3*D^5.\n")
    file.write("# Propeller center in grid coordinates.\n")
    file.write("# Propeller axis versor pointing backward.\n")
    file.write("# This output file is generated thanks to a script created by\n")
    file.write("# University of Naples Federico II and modified by CFS Engineering\n")
    file.write("# -----------------------------------------------------------------------------\n")

    return file


def write_actuator_disk_data(
    file,
    inlet_marker,
    outlet_marker,
    center,
    axis,
    radius,
    advanced_ratio,
    radial_stations,
    radial_thrust_coefs,
    radial_power_coefs,
):
    """Function to create a ActuatorDisk.dat file which is used to when rotor/propeller are define
    in the CPACS file.

    Args:
        file (file): File to write the actuator disk file
        inlet_marker (str): Marker of the inlet of the actuator disk
        outlet_marker (str): Marker of the outlet of the actuator disk
        center (tuple): Center of the actuator disk (x,y,z)
        axis (tuple): Axis of the actuator disk (x,y,z)
        radius (float): Radius of the actuator disk
        advanced_ratio (float): Advance ratio
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                       get the real radius value
        radial_thrust_coefs (np.array): Thrust coefficient at each radial_stations
        radial_power_coefs (np.array): Power coefficient at each radial_stations
    """

    total_thrust_coefficient = sum(radial_thrust_coefs * (radial_stations[1] - radial_stations[0]))
    file.write(f"# Total thurst coefficient= {total_thrust_coefficient:.5f}\n")

    file.write(f"MARKER_ACTDISK= {inlet_marker} {outlet_marker}\n")
    file.write(f"CENTER= {center[0]} {center[1]} {center[2]}\n")
    file.write(f"AXIS= {axis[0]} {axis[1]} {axis[2]}\n")
    file.write(f"RADIUS= {radius}\n")
    file.write(f"ADV_RATIO= {advanced_ratio:.5f}\n")
    file.write(f"NROW= {len(radial_stations)}\n")
    file.write("# rs=r/R    dCT/drs     dCP/drs     dCR/drs\n")

    for r, ctrs, cprs in zip(radial_stations, radial_thrust_coefs, radial_power_coefs):
        file.write(f"{r:.5f}     {ctrs:.5f}      {cprs:08.5f}     0.0\n")

    file.write("\n")

    return file


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
