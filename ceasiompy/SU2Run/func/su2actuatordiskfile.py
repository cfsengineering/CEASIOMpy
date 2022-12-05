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

import math
import numpy as np

from ambiance import Atmosphere

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


def get_advanced_ratio(alt, mach, rotational_velocity, radius):
    """_summary_

    Args:
        alt (float): Altitude [m]
        mach (float): Mach number [-]
        rotational_velocity (float): Propeller rotational velocity [1/s]
        radius (float): Propeller radius [m]
    """

    if rotational_velocity <= 0:
        raise ValueError("Rotational velocity must be positive!")

    Atm = Atmosphere(alt)
    free_stream_velocity = mach * Atm.speed_of_sound[0]

    return free_stream_velocity / (rotational_velocity * (2 * radius))


def axial_interference_function(lagrangian_moltiplicator, non_dimensional_radius):
    """_summary_

    Args:
        lagrangian_moltiplicator (float): TODO
        non_dimensional_radius (float): TODO

    Returns:
        axial_interference_factor (np.array): TODO
    """

    axial_interference_factor = (lagrangian_moltiplicator * non_dimensional_radius**2) / (
        non_dimensional_radius**2 + (1 + lagrangian_moltiplicator) ** 2
    )
    return axial_interference_factor


def get_prandtl_correction_values(
    radial_stations, prandtl_correction, blades_number, omega, radius, free_stream_velocity
):
    """Function to correct the values of thrust and power coefficients near the tip, based on
        Prandtl formulation

        TODO

    Args:
        prandtl (_type_): _description_
        blades_number (_type_): _description_
        radial_stations (_type_): _description_
        omega (_type_): _description_
        radius (_type_): _description_
        free_stream_velocity (_type_): _description_

    Returns:
        correction function to correct Ct and Cp
    """

    if not prandtl_correction:
        return np.ones(len(radial_stations))

    return (2 / np.pi) * np.arccos(
        np.exp(
            -0.5
            * blades_number
            * (1 - radial_stations)
            * math.sqrt(1 + (omega * radius / free_stream_velocity) ** 2)
        )
    )


def thrust_calculator(
    radial_stations,
    total_thrust_coefficient,
    radius,
    free_stream_velocity,
    prandtl,
    blades_number,
    rotational_velocity,
):
    """Performing of a calculation to obtain thrust and power coefficients distribution

    Args:
            total_thrust_coefficient (float): Total thrust coefficient[-]
            radius (float): Blade radius [m]
            free_stream_velocity (float): Cruise velocity [m/s]
            prandtl (bool): Correction for tip losses
            blades_number (int): Blades propeller number[-]
            rotational_velocity (int): Blade velocity rotation [1/s]

    Returns:
        dCt_optimal (float): thrust coefficient at every radius [-]
        dCp (float): power coefficient at every radius [-]
        r (float): adimensional radius [-]
    """

    STATIONS = 40
    EPSILON = 5e-20

    advanced_ratio = free_stream_velocity / (rotational_velocity * (radius * 2))

    omega = rotational_velocity * 2 * np.pi

    log.info(f"Selected total thrust coeff= {total_thrust_coefficient}")
    log.info(f"Radius= {radius}")
    log.info(f"Number of radial station= {len(radial_stations)}")
    log.info(f"Advanced ratio= {advanced_ratio}")
    log.info(f"Free stream velocity= {free_stream_velocity}")
    log.info(f"Prandtl correction= {prandtl}")
    log.info(f"Number of blades= {blades_number}")

    vectorize_axial_interf_f = np.vectorize(axial_interference_function)

    prandtl_correction_values = get_prandtl_correction_values(
        radial_stations, prandtl, blades_number, omega, radius, free_stream_velocity
    )

    # Computation of the non-dimensional radius

    non_dimensional_radius = omega * radial_stations * radius / free_stream_velocity

    radial_stations_spacing = 1.0 / STATIONS

    # Computation of the first try induced velocity distribution
    induced_velocity_distribution = (2 / free_stream_velocity**2) * (
        (-1 / free_stream_velocity)
        + np.sqrt(
            1
            + (
                ((2 * radius) ** 4 * (total_thrust_coefficient) * rotational_velocity**2)
                / (free_stream_velocity**2 * np.pi * radial_stations)
            )
        )
    )

    first_lagrange_moltiplicator = np.sum(induced_velocity_distribution)

    first_lagrange_moltiplicator = first_lagrange_moltiplicator / (
        free_stream_velocity * len(radial_stations)
    )

    # Computation of the first try axial interference factor distribution
    initial_axial_interference_factor = vectorize_axial_interf_f(
        first_lagrange_moltiplicator * prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_0 = (
        np.pi
        * advanced_ratio**2
        * radial_stations
        * (1 + initial_axial_interference_factor)
        * initial_axial_interference_factor
    )

    # Computation of the total thrust coefficient
    initial_total_thrust_coefficient = np.sum(radial_stations_spacing * dCt_0)

    # Compute the error with respect to the thrust coefficient given in input
    inital_error = initial_total_thrust_coefficient - total_thrust_coefficient
    log.info(f"Convergence history: {inital_error}")

    # Computation of the second try Lagrange moltiplicator
    last_lagrange_moltiplicator = first_lagrange_moltiplicator + 0.1

    # Computation of the second try axial interference factor distribution
    old_axial_interference_factor = vectorize_axial_interf_f(
        last_lagrange_moltiplicator * prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_old = (
        np.pi
        * advanced_ratio**2
        * radial_stations
        * (1 + old_axial_interference_factor)
        * old_axial_interference_factor
    )

    # Computation of the total thrust coefficient
    old_total_thrust_coefficient = np.sum(radial_stations_spacing * dCt_old)

    # Compute the error with respect to the thrust coefficient given in input
    old_error = old_total_thrust_coefficient - total_thrust_coefficient
    log.info(f"old_error= {old_error}")

    # Iterate using the false position methods.
    # Based on the error from the thrust coefficient given in input
    iteration = 2
    new_error = old_error
    while math.fabs(new_error) >= EPSILON and inital_error != old_error:

        iteration += 1
        # Computation of the new Lagrange moltiplicator value based on the false position method
        new_lagrange_moltiplicator = (
            last_lagrange_moltiplicator * inital_error - first_lagrange_moltiplicator * old_error
        ) / (inital_error - old_error)

        # Computation of the new axial interference factor distribution
        new_axial_interference_factor = vectorize_axial_interf_f(
            new_lagrange_moltiplicator * prandtl_correction_values,
            non_dimensional_radius,
        )

        dCt_new = (
            np.pi
            * advanced_ratio**2
            * radial_stations
            * (1 + new_axial_interference_factor)
            * new_axial_interference_factor
        )

        # Computation of the new total thrust coefficient
        new_total_thrust_coefficient = 0.0
        new_total_thrust_coefficient = radial_stations_spacing * np.sum(dCt_new)

        # Computation of the total thrust coefficient error with respect to the input value
        new_error = new_total_thrust_coefficient - total_thrust_coefficient

        log.info(f"new error= {new_error}")

        # Updating the stored values for the next iteration
        inital_error = old_error
        old_error = new_error

        first_lagrange_moltiplicator = last_lagrange_moltiplicator
        last_lagrange_moltiplicator = new_lagrange_moltiplicator

    # Calculate radial Thrust coefficient at each stations
    optimal_axial_interference_factor = vectorize_axial_interf_f(
        new_lagrange_moltiplicator * prandtl_correction_values, non_dimensional_radius
    )

    radial_thrust_coefs = (
        np.pi
        * advanced_ratio**2
        * radial_stations
        * (1 + optimal_axial_interference_factor)
        * optimal_axial_interference_factor
    )

    # Calculate radial Power coefficient at each stations
    optimal_rotational_interference_factor = (
        new_lagrange_moltiplicator * prandtl_correction_values
    ) * (
        (1 + new_lagrange_moltiplicator * prandtl_correction_values)
        / (
            non_dimensional_radius * non_dimensional_radius
            + (1 + new_lagrange_moltiplicator * prandtl_correction_values) ** 2
        )
    )

    radial_power_coefs = (radius * 4 * np.pi / (rotational_velocity**3 * (2 * radius) ** 5)) * (
        free_stream_velocity**3
        * (1 + optimal_axial_interference_factor) ** 2
        * optimal_axial_interference_factor
        * radial_stations
        * radius
        + omega**2
        * free_stream_velocity
        * (1 + optimal_axial_interference_factor)
        * optimal_rotational_interference_factor**2
        * (radial_stations * radius) ** 3
    )

    # # Computation of the total power coefficient
    # total_power_coefficient = np.sum(radial_stations_spacing * dCp)
    # optimal_total_thrust_coefficient = np.sum(radial_stations_spacing * dCt_optimal)
    # delta_pressure = (
    #     (dCt_optimal) * (2 * free_stream_velocity**2) / (advanced_ratio**2 * pi * radial_stations)
    # )

    # # Computation of the thrust over density using the static pressure jump distribution
    # thrust_density_ratio = 0.0
    # thrust_density_ratio = np.sum(
    #     2 * pi * radial_stations * radius**2 * radial_stations_spacing * delta_pressure
    # )

    # # Computation of the thrust coefficient using thrust_density_ratio
    # computed_total_thrust_coefficient = thrust_density_ratio / (
    #     rotational_velocity**2 * (2 * radius) ** 4
    # )

    # # Computation of the efficiency.
    # eta = advanced_ratio * (optimal_total_thrust_coefficient / total_power_coefficient)

    # TODO: Add check
    # TODO: Add mardown results file

    # log.info("------- Check output values -------")
    # log.info(f"Optimal total thrust coefficient= {optimal_total_thrust_coefficient}")
    # log.info("Total thrust coefficient computed")
    # log.info(f"using the static pressure jump= {computed_total_thrust_coefficient}")
    # log.info(f"Power coefficient distribution integral= {total_power_coefficient}")
    # log.info(f"Thrust over Density= {thrust_density_ratio}")
    # log.info(f"Efficiency eta= {eta}")
    # log.info(f"Lagrangian moltiplicator/free_stream_velocity= {new_lagrange_moltiplicator}")

    # log.info("SU2 file generated!")

    return radial_thrust_coefs, radial_power_coefs

    # return (
    #     optimal_total_thrust_coefficient,
    #     total_power_coefficient,
    #     thrust_density_ratio,
    #     eta,
    #     r,
    #     dCt_optimal,
    #     dCp,
    #     non_dimensional_radius,
    #     optimal_axial_interference_factor,
    #     optimal_rotational_interference_factor,
    #     prandtl,
    #     correction_function,
    # )


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
