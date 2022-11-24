"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This the function created by University of Naples Federico II and adepted for Ceasiompy to generate
a file .dat with thrust coefficient distribution

Python version: >=3.8

| Author: Giacomo Benedetti
| Creation: 2022-11-03

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from math import fabs, pi, sqrt
from pathlib import Path

import numpy as np
from ceasiompy.ActuatorDisk.func.prandtl_correction import prandtl_corr
from ceasiompy.ActuatorDisk.func.axial_interf_func import axial_interference_function
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_external_file(CTrs, CPrs, stations, radius, advanced_ratio, r, Ct_total):

    """Function to write on an external file the result of the thrust and power coefficients
        distribution, performed by thrust calculation function

    Args:
        dCt_optimal (float): thrust coefficient at every radius [-]
        dCp (float): power coefficient at every radius [-]
        r (float): adimensional radius [-]

    Returns:
        file filled with thrust and power coefficient distribution
    """

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dat_path = Path(results_dir, "ActuatorDisk.dat")
    file = open(actuator_disk_dat_path, "w")
    file.write("# Automatic generated actuator disk input data file using\n")
    file.write("# the Optimal Propeller code.\n")
    file.write("# Data file needed for the actuator disk VARIABLE_LOAD type.\n")
    file.write("# The load distribution is obtained using\n")
    file.write("# the inviscid theory of the optimal propeller using global data.\n")
    file.write("#\n")
    file.write("# The first three lines must be filled.\n")
    file.write("# An example of this file can be found in the TestCases directory.\n")
    file.write("#\n")
    file.write(f"# It was choseen a total thrust coefficient= {Ct_total:.4f}\n")
    file.write("# This output file is generated thanks to a script created by\n")
    file.write("# University of Naples Federico II and modified by CFS Engineering\n")
    file.write("# with the aim of integrating it in CEASIOMpy\n")
    file.write(
        "# ---------------------------------------------------------------------------------\n"
    )
    file.write("#\n")
    file.write("MARKER_ACTDISK= Propeller_AD_Inlet Propeller_AD_Outlet\n")
    file.write("CENTER= 0.0 2.0 0.0\n")
    file.write("AXIS= 1.0 0.0 0.0\n")
    file.write(f"RADIUS= {radius}    \n")
    file.write(f"ADV_RATIO= {advanced_ratio}   \n")
    file.write(f"NROW= {stations}   \n")
    file.write("#rs=r/R        dCT/drs       dCP/drs       dCR/drs\n")
    for r, ctrs, cprs in zip(r, CTrs, CPrs):
        file.write(f"{r:.7f}     {ctrs:.7f}      {cprs:.7f}     0.0\n")

    file.write("#\n")
    file.write("MARKER_ACTDISK= Propeller_mirrored_AD_Inlet Propeller_mirrored_AD_Outlet\n")
    file.write("CENTER= 0.0 -2.0 0.0\n")
    file.write("AXIS= 1.0 0.0 0.0\n")
    file.write(f"RADIUS= {radius}    \n")
    file.write(f"ADV_RATIO= {advanced_ratio}   \n")
    file.write(f"NROW= {stations}   \n")

    file.close()


def thrust_calculator(
    stations,
    total_thrust_coefficient,
    radius,
    hub_radius,
    advanced_ratio,
    free_stream_velocity,
    prandtl,
    blades_number,
):

    """Performing of a calculation to obtain thrust and power coefficients distribution

    Args:
            stations (float): Number of elements for blade discretization [-]
            total_thrust_coefficient (float): Total thrust coefficient[-]
            radius (float): Blade radius [m]
            hub_radius (float): Radius of the blade at the hub [m]
            advanced_ratio (float): Free_stream_velocity/(rotational_velocity*diameter)[-]
            free_stream_velocity (float): Cruise velocity [m/s]
            prandtl (bool): Correction for tip losses
            blades_number (int): Blades propeller number[-]

    Returns:
        dCt_optimal (float): thrust coefficient at every radius [-]
        dCp (float): power coefficient at every radius [-]
        r (float): adimensional radius [-]
    """

    log.info("-------------- Check input values choseen --------------")
    log.info(f"Number of station= {stations}")
    log.info(f"Selected total thrust coeff= {total_thrust_coefficient}")
    log.info(f"Radius= {radius}")
    log.info(f"Hub radius= {hub_radius}")
    log.info(f"Advanced ratio= {advanced_ratio}")
    log.info(f"Free stream velocity= {free_stream_velocity}")
    log.info(f"Prandtl correction= {prandtl}")
    log.info(f"Number of blades= {blades_number}")

    # Resize the vectors using the number of radial stations.
    r = np.empty(stations)
    non_dimensional_radius = np.empty(stations)
    dCp = np.empty(stations)
    induced_velocity_distribution = np.empty(stations)
    new_axial_interference_factor = np.empty(stations)
    old_axial_interference_factor = np.empty(stations)
    initial_axial_interference_factor = np.empty(stations)
    dCt_new = np.empty(stations)
    dCt_old = np.empty(stations)
    dCt_0 = np.empty(stations)
    delta_pressure = np.empty(stations)
    optimal_axial_interference_factor = np.empty(stations)
    optimal_rotational_interference_factor = np.empty(stations)
    dCt_optimal = np.empty(stations)

    non_dimensional_hub_radius = hub_radius / radius

    # Computation of the non-dimensional radial stations.
    for i in range(1, stations + 1):
        r[i - 1] = i / float(stations)
        if r[i - 1] <= non_dimensional_hub_radius:
            i_hub = i - 1

    n = free_stream_velocity / (2 * radius * advanced_ratio)
    omega = n * 2 * pi

    correction_function = prandtl_corr(
        prandtl, stations, blades_number, r, omega, radius, free_stream_velocity
    )

    # Computation of the non-dimensional radius

    non_dimensional_radius = omega * r * radius / free_stream_velocity

    EPSILON = 5e-20

    radial_stations_spacing = 1.0 / stations

    first_lagrange_moltiplicator = 0.0
    # Computation of the first try induced velocity distribution
    for i in range(stations):
        induced_velocity_distribution[i] = (2 / free_stream_velocity**2) * (
            (-1 / free_stream_velocity)
            + sqrt(
                1
                + (
                    ((2 * radius) ** 4 * (total_thrust_coefficient) * n**2)
                    / (free_stream_velocity**2 * pi * r[i])
                )
            )
        )

        first_lagrange_moltiplicator = np.sum(induced_velocity_distribution)

    first_lagrange_moltiplicator = first_lagrange_moltiplicator / (free_stream_velocity * stations)

    # Computation of the first try axial interference factor distribution
    vectorize_axial_interf_f = np.vectorize(axial_interference_function)

    initial_axial_interference_factor = vectorize_axial_interf_f(
        first_lagrange_moltiplicator * correction_function,
        non_dimensional_radius,
    )

    dCt_0 = (
        pi
        * advanced_ratio**2
        * r
        * (1 + initial_axial_interference_factor)
        * initial_axial_interference_factor
    )

    # Computation of the total thrust coefficient
    initial_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        initial_total_thrust_coefficient += radial_stations_spacing * dCt_0[i]

    # Compute the error with respect to the thrust coefficient given in input
    inital_error = initial_total_thrust_coefficient - total_thrust_coefficient
    log.info(f"Convergence history: {inital_error}")

    # Computation of the second try Lagrange moltiplicator
    last_lagrange_moltiplicator = first_lagrange_moltiplicator + 0.1

    # Computation of the second try axial interference factor distribution
    vectorize_axial_interf_f = np.vectorize(axial_interference_function)

    old_axial_interference_factor = vectorize_axial_interf_f(
        last_lagrange_moltiplicator * correction_function,
        non_dimensional_radius,
    )

    dCt_old = (
        pi
        * advanced_ratio**2
        * r
        * (1 + old_axial_interference_factor)
        * old_axial_interference_factor
    )

    # Computation of the total thrust coefficient
    old_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        old_total_thrust_coefficient += radial_stations_spacing * dCt_old[i]

    # Compute the error with respect to the thrust coefficient given in input
    old_error = old_total_thrust_coefficient - total_thrust_coefficient
    log.info(f"old_error= {old_error}")

    # Iterate using the false position methods.
    # Based on the error from the thrust coefficient given in input
    iteration = 2
    new_error = old_error
    while fabs(new_error) >= EPSILON and inital_error != old_error:

        iteration += 1
        # Computation of the new Lagrange moltiplicator value based on the false position method
        new_lagrange_moltiplicator = (
            last_lagrange_moltiplicator * inital_error - first_lagrange_moltiplicator * old_error
        ) / (inital_error - old_error)

        # Computation of the new axial interference factor distribution
        vectorize_axial_interf_f = np.vectorize(axial_interference_function)
        new_axial_interference_factor = vectorize_axial_interf_f(
            new_lagrange_moltiplicator * correction_function,
            non_dimensional_radius,
        )

        dCt_new = (
            pi
            * advanced_ratio**2
            * r
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

    # Computation of the correct axial and rotational interference factors
    vectorize_axial_interf_f = np.vectorize(axial_interference_function)

    optimal_axial_interference_factor = vectorize_axial_interf_f(
        new_lagrange_moltiplicator * correction_function, non_dimensional_radius
    )
    optimal_rotational_interference_factor = (new_lagrange_moltiplicator * correction_function) * (
        (1 + new_lagrange_moltiplicator * correction_function)
        / (
            non_dimensional_radius * non_dimensional_radius
            + (1 + new_lagrange_moltiplicator * correction_function) ** 2
        )
    )
    dCt_optimal = (
        pi
        * advanced_ratio**2
        * r
        * (1 + optimal_axial_interference_factor)
        * optimal_axial_interference_factor
    )

    dCp = (radius * 4 * pi / (n**3 * (2 * radius) ** 5)) * (
        free_stream_velocity**3
        * (1 + optimal_axial_interference_factor) ** 2
        * optimal_axial_interference_factor
        * r
        * radius
        + omega**2
        * free_stream_velocity
        * (1 + optimal_axial_interference_factor)
        * optimal_rotational_interference_factor**2
        * (r * radius) ** 3
    )

    # Computation of the total power coefficient
    total_power_coefficient = 0.0
    optimal_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        total_power_coefficient += radial_stations_spacing * dCp[i]
        optimal_total_thrust_coefficient += radial_stations_spacing * dCt_optimal[i]
        delta_pressure[i] = (
            (dCt_optimal[i]) * (2 * free_stream_velocity**2) / (advanced_ratio**2 * pi * r[i])
        )

    # Computation of the thrust over density using the static pressure jump distribution
    thrust_density_ratio = 0.0
    for i in range(i_hub, stations):
        thrust_density_ratio += (
            2 * pi * r[i] * radius**2 * radial_stations_spacing * delta_pressure[i]
        )

    # Computation of the thrust coefficient using thrust_density_ratio
    computed_total_thrust_coefficient = thrust_density_ratio / (n**2 * (2 * radius) ** 4)

    # Computation of the efficiency.
    eta = advanced_ratio * (optimal_total_thrust_coefficient / total_power_coefficient)

    log.info("------- Check output values -------")
    log.info(f"Optimal total thrust coefficient= {optimal_total_thrust_coefficient}")
    log.info("Total thrust coefficient computed")
    log.info(f"using the static pressure jump= {computed_total_thrust_coefficient}")
    log.info(f"Power coefficient distribution integral= {total_power_coefficient}")
    log.info(f"Thrust over Density= {thrust_density_ratio}")
    log.info(f"Efficiency eta= {eta}")
    log.info(f"Lagrangian moltiplicator/free_stream_velocity= {new_lagrange_moltiplicator}")

    log.info("SU2 file generated!")

    write_external_file(
        dCt_optimal, dCp, stations, radius, advanced_ratio, r, optimal_total_thrust_coefficient
    )

    return (
        optimal_total_thrust_coefficient,
        total_power_coefficient,
        thrust_density_ratio,
        eta,
        r,
        dCt_optimal,
        dCp,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl,
        correction_function,
    )
