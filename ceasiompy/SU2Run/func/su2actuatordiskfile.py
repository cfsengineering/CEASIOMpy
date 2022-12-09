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
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
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
        number_of_stations (int): Number of radial station, 40 by default

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


def get_advanced_ratio(free_stream_velocity, rotational_velocity, radius):
    """Function to calculate advanced ratio, that is the ratio between velocity
        and rotational velocity, taking in account of the diameter of the propeller

    Args:
        free_stream_velocity (float): Free stream velocity [m/s]
        rotational_velocity (float): Propeller rotational velocity [1/s]
        radius (float): Propeller radius [m]
    """

    if rotational_velocity <= 0:
        raise ValueError("Rotational velocity must be positive!")

    return free_stream_velocity / (rotational_velocity * (2 * radius))


def axial_interference_function(lagrangian_multiplier, non_dimensional_radius):
    """_summary_

    Args:
        lagrangian_multiplier (float): lagrangian multiplier, it is used to calculate
                                       interference factor
        non_dimensional_radius (float): radius adimentionalization made using advanced ration

    Returns:
        axial_interference_factor (np.array): axial interference factor calculated ad every radius,
                                              it is used to estimate the losses due to a
                                              pre-rotation of the fluid
    """

    axial_interference_factor = (lagrangian_multiplier * non_dimensional_radius**2) / (
        non_dimensional_radius**2 + (1 + lagrangian_multiplier) ** 2
    )
    return axial_interference_factor


def get_prandtl_correction_values(
    radial_stations, prandtl_correction, blades_number, omega, radius, free_stream_velocity
):
    """Function to correct the values of thrust and power coefficients near the tip, based on
        Prandtl formulation

    Args:
        prandtl (bool): bool value thanks to which is possible
                        to activate or deactivate the correction
        blades_number (int): number of blades of the propeller
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                    get the real radius value
        omega (float): rotational velocity multiplied for 2 and pi
        radius (float): radius of the propeller
        free_stream_velocity (float): free stream velocity

    Returns:
        correction function to correct thrust coefficient and power coefficient
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


def calculate_radial_thrust_coefs(radial_stations, advanced_ratio, opt_axial_interf_factor):
    """Function to calculate thrust coefficient distribution along the radius

    Args:
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                    get the real radius value
        advanced_ratio (float): ratio between velocity and rotational velocity
                                multiplied by diameter
        opt_axial_interf_factor (np.array): Optimal axial interference factor

    """

    return (
        np.pi
        * advanced_ratio**2
        * radial_stations
        * (1 + opt_axial_interf_factor)
        * opt_axial_interf_factor
    )


def save_plots(
    radial_stations,
    radial_thrust_coefs,
    radial_power_coefs,
    non_dimensional_radius,
    optimal_axial_interference_factor,
    optimal_rotational_interference_factor,
    prandtl_correction_values,
    case_dir_path,
    propeller_uid,
):
    """Function to save plot in result folder

    Args:
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                    get the real radius value
        radial_thrust_coefs (np.array): radial distribution of thrust coefficient
        radial_power_coefs (np.array): radial distribution of power coefficient
        non_dimensional_radius (float): radius adimentionalization made using advanced ratio
        optimal_axial_interference_factor (np.array): optimal axial interference factor
        optimal_rotational_interference_factor (np.array): optimal rotational interference factor
        prandtl_correction_values (np.array): values of Prandtl correction
        case_dir_path (Path): Path object of the case directory
        propeller_uid (str): Uid of the current propeller
    """

    current_dir = Path(case_dir_path, propeller_uid)
    current_dir.mkdir()
    interference_plot_path = Path(current_dir, "interference.png")
    ct_cp_distr_plot_path = Path(current_dir, "radial_thrust_and_power_coefficient.png")
    prandtl_correction_plot_path = Path(current_dir, "prandtl_correction.png")

    f1 = plt.figure(1)
    plt.plot(
        radial_stations,
        radial_thrust_coefs,
        "r",
        markersize=4,
        label="$\\frac{dCT}{d\overline{r}}$",
    )
    plt.plot(
        radial_stations,
        radial_power_coefs,
        "k",
        markersize=4,
        label="$\\frac{dCP}{d\overline{r}}$",
    )
    plt.grid(True)
    plt.legend()
    plt.xlabel("$\overline{r}$")
    plt.ylabel("$dC_t$,  $dC_p$")
    plt.title("Load Distribution")

    f1.savefig(ct_cp_distr_plot_path)
    plt.clf()

    f2 = plt.figure(2)
    plt.plot(
        non_dimensional_radius,
        optimal_axial_interference_factor,
        "r",
        markersize=4,
        label="$a$",
    )
    plt.plot(
        non_dimensional_radius,
        optimal_rotational_interference_factor,
        "k",
        markersize=4,
        label="$a^1$",
    )
    plt.grid(True)
    plt.legend(numpoints=3)
    plt.xlabel("$\\frac{2\pi*r}{J}$")
    plt.ylabel("$a$, $a^1$")
    plt.title("Interference Factors")

    f2.savefig(interference_plot_path)
    plt.clf()

    f3 = plt.figure(3)
    plt.plot(radial_stations, prandtl_correction_values, "k", markersize=4)
    plt.grid(True)
    plt.xlabel("$\overline{r}$")
    plt.ylabel("$F(\overline{r})$")
    plt.title("Tip Loss Prandtl Correction Function")
    f3.savefig(prandtl_correction_plot_path)
    plt.clf()

    log.info(f"A plot have been saved at {ct_cp_distr_plot_path}")
    log.info(f"A plot have been saved at {interference_plot_path}")
    log.info(f"A plot have been saved at {prandtl_correction_plot_path}")


def thrust_calculator(
    radial_stations,
    total_thrust_coefficient,
    radius,
    free_stream_velocity,
    prandtl_correction,
    blades_number,
    rotational_velocity,
):
    """Performing of a calculation to obtain thrust and power coefficients distribution

    Args:
        radial_stations (np.array): adimensional radius along the blade. Multiply by radius to
                                    get the real radius value
        total_thrust_coefficient (float): Total thrust coefficient[-]
        radius (float): Blade radius [m]
        free_stream_velocity (float): Cruise velocity [m/s]
        prandtl_correction (bool): Correction for tip losses
        blades_number (int): Blades propeller number[-]
        rotational_velocity (int): Blade velocity rotation [1/s]

    Returns:
        dCt_optimal (float): thrust coefficient at every radius [-]
        dCp (float): power coefficient at every radius [-]
        r (float): adimensional radius [-]
    """

    log.info("Start of thrust calculation distribution")

    EPSILON = 5e-20

    advanced_ratio = free_stream_velocity / (rotational_velocity * (radius * 2))
    omega = rotational_velocity * 2 * np.pi

    vectorized_axial_interf_f = np.vectorize(axial_interference_function)

    prandtl_correction_values = get_prandtl_correction_values(
        radial_stations, prandtl_correction, blades_number, omega, radius, free_stream_velocity
    )

    log.info(f"Prandtl correction= {prandtl_correction}")

    # TODO: put in the markdown file
    # log.info(f"Selected total thrust coeff= {total_thrust_coefficient}")
    # log.info(f"Radius= {radius}")
    # log.info(f"Number of radial station= {len(radial_stations)}")
    # log.info(f"Advanced ratio= {advanced_ratio}")
    # log.info(f"Free stream velocity= {free_stream_velocity}")
    # log.info(f"Prandtl correction= {prandtl_correction}")
    # log.info(f"Number of blades= {blades_number}")

    non_dimensional_radius = np.pi * radial_stations / advanced_ratio
    radial_stations_spacing = radial_stations[1] - radial_stations[0]

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

    # ###### TO SIMPLIFY ----------------------------------------------------------------

    first_lagrange_multiplier = np.sum(induced_velocity_distribution) / (
        free_stream_velocity * len(radial_stations)
    )

    # Computation of the first try axial interference factor distribution
    initial_axial_interference_factor = vectorized_axial_interf_f(
        first_lagrange_multiplier * prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_0 = calculate_radial_thrust_coefs(
        radial_stations, advanced_ratio, initial_axial_interference_factor
    )

    # Compute the error with respect to the thrust coefficient given in input
    initial_error = np.sum(radial_stations_spacing * dCt_0) - total_thrust_coefficient
    log.info("Start of error calculation")

    # Computation of the second try Lagrange multiplicator
    last_lagrange_multiplier = first_lagrange_multiplier + 0.1

    # Computation of the second try axial interference factor distribution
    old_axial_interference_factor = vectorized_axial_interf_f(
        last_lagrange_multiplier * prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_old = calculate_radial_thrust_coefs(
        radial_stations, advanced_ratio, old_axial_interference_factor
    )

    # Compute the error with respect to the thrust coefficient given in input
    old_error = np.sum(radial_stations_spacing * dCt_old) - total_thrust_coefficient

    # Iterate using the false position methods.
    # Based on the error from the thrust coefficient given in input
    iteration = 2
    new_error = old_error

    while math.fabs(new_error) >= EPSILON and initial_error != old_error:

        iteration += 1
        # Computation of the new Lagrange multiplicator value based on the false position method
        new_lagrange_multiplier = (
            last_lagrange_multiplier * initial_error - first_lagrange_multiplier * old_error
        ) / (initial_error - old_error)

        # Computation of the new axial interference factor distribution
        new_axial_interference_factor = vectorized_axial_interf_f(
            new_lagrange_multiplier * prandtl_correction_values,
            non_dimensional_radius,
        )

        dCt_new = calculate_radial_thrust_coefs(
            radial_stations, advanced_ratio, new_axial_interference_factor
        )

        new_total_thrust_coefficient = radial_stations_spacing * np.sum(dCt_new)

        new_error = new_total_thrust_coefficient - total_thrust_coefficient
        # log.info(f"new error= {new_error}")

        # Updating the stored values for the next iteration
        initial_error = old_error
        old_error = new_error

        first_lagrange_multiplier = last_lagrange_multiplier
        last_lagrange_multiplier = new_lagrange_multiplier

    # ###### TO SIMPLIFY----------------------------------------------------------------
    log.info("Error has been estimated")

    # Calculate radial Thrust coefficient at each stations
    optimal_axial_interference_factor = vectorized_axial_interf_f(
        new_lagrange_multiplier * prandtl_correction_values, non_dimensional_radius
    )

    radial_thrust_coefs = calculate_radial_thrust_coefs(
        radial_stations, advanced_ratio, optimal_axial_interference_factor
    )

    # Calculate radial Power coefficient at each stations
    optimal_rotational_interference_factor = (
        new_lagrange_multiplier * prandtl_correction_values
    ) * (
        (1 + new_lagrange_multiplier * prandtl_correction_values)
        / (
            non_dimensional_radius * non_dimensional_radius
            + (1 + new_lagrange_multiplier * prandtl_correction_values) ** 2
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

    log.info("Radial thrust and power coefficients have been estimated")

    # # Computation of the total power coefficient
    # total_power_coefficient = np.sum(radial_stations_spacing * dCp)
    # optimal_total_thrust_coefficient = np.sum(radial_stations_spacing * dCt_optimal)
    # delta_pressure = (
    #    (dCt_optimal) * (2 * free_stream_velocity**2) / (advanced_ratio**2 * pi * radial_stations)
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
    # TODO: Add markdown results file

    # log.info("------- Check output values -------")
    # log.info(f"Optimal total thrust coefficient= {optimal_total_thrust_coefficient}")
    # log.info("Total thrust coefficient computed")
    # log.info(f"using the static pressure jump= {computed_total_thrust_coefficient}")
    # log.info(f"Power coefficient distribution integral= {total_power_coefficient}")
    # log.info(f"Thrust over Density= {thrust_density_ratio}")
    # log.info(f"Efficiency eta= {eta}")
    # log.info(f"Lagrangian multiplicator/free_stream_velocity= {new_lagrange_multiplicator}")

    return (
        radial_thrust_coefs,
        radial_power_coefs,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl_correction_values,
    )


def write_header(file):
    """Write the header of the actuator disk file.

    Args:
        file (file): File in which the header will be written.

    """

    header_lines = [
        "# Automatic generated actuator disk input data file using\n",
        "# the Optimal Propeller code.\n",
        "# Data file needed for the actuator disk VARIABLE_LOAD type.\n",
        "# The load distribution is obtained using\n",
        "# the inviscid theory of the optimal propeller using global data.\n",
        "#\n",
        "# ADV_RATIO defined as Vinf/(nD) where: \n",
        "#    n: propeller rounds per second,\n",
        "#    D: propeller diameter.\n",
        "# 'Renard' definition of propeller coefficients:\n",
        "# reference force = rho*n^2*D^4, reference power = rho*n^3*D^5.\n",
        "# Propeller center in grid coordinates.\n",
        "# Propeller axis versor pointing backward.\n",
        "# This output file is generated thanks to a script created by\n",
        "# University of Naples Federico II and modified by CFS Engineering\n",
        "# -----------------------------------------------------------------------------\n",
    ]

    file.writelines(header_lines)

    log.info("ActuatorDisk.dat header has been written")

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

    log.info("ActuatorDisk.dat file generated!")

    return file


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
