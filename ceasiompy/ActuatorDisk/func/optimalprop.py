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


from math import pi, sqrt, acos, exp, fabs
import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from pathlib import Path

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def axial_interference_function(lagrangian_moltiplicator, non_dimensional_radius):

    """
    Function to calculate the axial intereference factor useful to calculate properly the thrust
    coefficient distribution

    Args:
        lagrangian_moltiplicator (float): Lagrangian moltiplicator [-]
        non_dimensional_radius (float): Non dimensional radius [-]

    Returns:
        axial_interference_factor (float):  Axial interference factor[-]
    """

    axial_interference_factor = (lagrangian_moltiplicator * non_dimensional_radius**2) / (
        non_dimensional_radius**2 + (1 + lagrangian_moltiplicator) ** 2
    )
    return axial_interference_factor


def write_external_file(CTrs, CPrs, stations, radius, advanced_ratio, r):

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
    file.write("# This output file is generated thanks to a script created by\n")
    file.write("# University of Naples Federico II and modified by CFS Engineering\n")
    file.write("# with the aim of integrating it in CEASIOMpy\n")
    file.write(
        "# ---------------------------------------------------------------------------------\n"
    )
    file.write("#\n")
    file.write("MARKER_ACTDISK= \n")
    file.write("CENTER= \n")
    file.write("AXIS= \n")
    file.write("RADIUS= " + str(radius) + "\n")
    file.write("ADV_RATIO= " + str(advanced_ratio) + "\n")
    file.write("NROW= " + str(stations) + "\n")
    file.write("# rs=r/R        dCT/drs       dCP/drs       dCR/drs\n")
    for r, ctrs, cprs in zip(r, CTrs, CPrs):
        file.write(f"  {r:.7f}     {ctrs:.7f}     {cprs:.7f}     0.0\n")

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
    correction_function = np.empty(stations)
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

    # Computation of the tip loss Prandtl correction function
    if prandtl:
        for i in range(stations):
            correction_function[i] = (2 / pi) * acos(
                exp(
                    -0.5
                    * blades_number
                    * (1 - r[i])
                    * sqrt(1 + (omega * radius / free_stream_velocity) ** 2)
                )
            )

    else:
        correction_function = np.ones(stations)

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

        first_lagrange_moltiplicator += induced_velocity_distribution[i]

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
    log.info(f"Optimal total thrust coefficient= {optimal_total_thrust_coefficient:.4f}")
    log.info(
        f"""Total thrust coefficient computed
        using the static pressure jump= {computed_total_thrust_coefficient:.4f}"""
    )
    log.info(f"Power coefficient distribution integral= {total_power_coefficient:.4f}")
    log.info(f"Thrust over Density= {thrust_density_ratio:.4f}")
    log.info(f"Efficiency eta= {eta:.4f}")
    log.info(f"Lagrangian moltiplicator/free_stream_velocity= {new_lagrange_moltiplicator:.4f}")

    log.info("SU2 file generated!")

    write_external_file(dCt_optimal, dCp, stations, radius, advanced_ratio, r)

    # Write the actuator disk configuration file

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_cfg_path = Path(results_dir, "ActuatorDisk.cfg")
    file = open(actuator_disk_cfg_path, "w")

    file.write("% Automatic generated actuator disk configuration file.\n")
    file.write("%\n")
    file.write("% The first two elements of MARKER_ACTDISK must be filled.\n")
    file.write("% An example of this file can be found in the TestCases directory.\n")
    file.write("%\n")
    file.write("% Author: Ettore Saetta, Lorenzo Russo, Renato Tognaccini.\n")
    file.write("% Theoretical and Applied Aerodynamic Research Group (TAARG),\n")
    file.write("% University of Naples Federico II\n")
    file.write("\n")
    file.write("ACTDISK_TYPE = VARIABLE_LOAD\n")
    file.write("ACTDISK_FILENAME = ActuatorDisk.dat\n")
    file.write("MARKER_ACTDISK = ( , , 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)\n")
    file.close()

    return optimal_total_thrust_coefficient, total_power_coefficient, thrust_density_ratio, eta
