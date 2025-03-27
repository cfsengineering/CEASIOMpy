"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to generate the actuator disk file for SU2.

Source: https://github.com/su2code/SU2/blob/master/TestCases/rans/actuatordisk_variable_load/ActuatorDisk.dat

Python version: >=3.8

| Author : Aidan Jungo and Giacomo Benedetti
| Creation: 2022-12-05
| Modified: Leon Deligny
| Date: 24-Feb-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math

import numpy as np

from ceasiompy.utils.ceasiompyutils import get_results_directory

from pathlib import Path
from numpy import ndarray
from markdownpy.markdownpy import MarkdownDoc

from typing import (
    Callable, 
    Tuple, 
    TextIO,
)

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_radial_stations(
    radius: float, 
    hub_radius: float, 
    number_of_stations: int = 40
) -> ndarray:
    """
    Non-dimensionalize the radius and remove values smaller than hub radius.

    Args:
        radius (float): Propeller radius [m].
        hub_radius (float): Hub radius [m].
        number_of_stations (int = 40): Number of radial station.

    Returns:
        radial_stations (ndarray): Non-dimensional radius along the blade.

    """

    if hub_radius >= radius:
        raise ValueError("hub radius should be smaller than radius.")

    radial_stations = np.linspace(0, 1, number_of_stations + 1)[1:]
    i_hub = (radial_stations >= hub_radius / radius).argmax()

    return radial_stations[i_hub:]


def get_advanced_ratio(
    free_stream_velocity: float, 
    rotational_velocity: float, 
    radius: float,
) -> float:
    """
    Calculate advanced ratio (ratio between velocity and rotational velocity), 
    taking in account of the diameter of the propeller.

    Args:
        free_stream_velocity (float): Free stream velocity [m/s].
        rotational_velocity (float): Propeller rotational velocity [1/s].
        radius (float): Propeller radius [m].

     Returns:
        (float): Advanced ratio.

    """

    if rotational_velocity <= 0:
        raise ValueError("Rotational velocity must be positive !")

    return free_stream_velocity / (rotational_velocity * (2 * radius))


def axial_interference_function(lag_mult: float, non_dim_radius: float) -> float:
    """
    Obtains the array with the different values of axial interference factor at every radius.
    This vector is used to estimate the losses due to a pre-rotation of the fluid.

    Args:
        lag_mult (float): Lagrangian multiplier, used to calculate interference factor.
        non_dim_radius (float): radius adimentionalization made using advanced ratio.

    Returns:
        axial_interference_factor (float): axial interference factor calculated at every radius.

    """

    axial_interference_factor = (lag_mult * non_dim_radius**2) / (
        non_dim_radius**2 + (1 + lag_mult) ** 2
    )
    return axial_interference_factor


def get_prandtl_correction_values(
    radial_stations: ndarray,
    prandtl_correction: bool,
    blades_number: int,
    omega: float,
    radius: float,
    free_stream_velocity: float,
) -> ndarray:
    """
    Correct the values of thrust and power coefficients near the tip, 
    based on Prandtl formulation.

    Args:
        radial_stations (ndarray): Non-dimensionalized radius along the blade.
        prandtl_correction (bool): Activate (True) or deactivate (False) the correction.
        blades_number (int): Number of blades of the propeller.
        omega (float): Rotational velocity multiplied for 2 and pi.
        radius (float): Radius of the propeller.
        free_stream_velocity (float): Free stream velocity.
    Returns:
        (ndarray): Prandtl correction values.

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


def get_error(radial_stations_spacing: float, dCt: ndarray, total_thrust_coefficient: float) -> float:
    """
    Computes error between calculated and input thrust coefficient.

    Args:
        radial_stations_spacing (float): spacing between r and r+dr
        dCt (ndarray): local thrust coefficient
        total_thrust_coefficient (float): integration of local thrust coefficient
    Returns:
        (float): Difference between calculated and input thrust coefficient.

    """

    # TODO: Why not return euclidean norm of error ?
    return np.sum(radial_stations_spacing * dCt) - total_thrust_coefficient


def get_corrected_axial_factor(
    vectorized_axial_interf_f: Callable[[ndarray, ndarray], ndarray],
    lag_mult: float,
    prandtl_correction_values: ndarray,
    non_dimensional_radius: ndarray,
) -> ndarray:
    """
    Correct axial interference factor at every radius with Prandtl correction.

    Args:
        vectorized_axial_interf_f (Callable[[float, float], float]): Function to calculate axial interference factor.
        lag_mult (float): Lagrangian multiplier.
        prandtl_correction_values (ndarray): Prandtl correction values.
        non_dimensional_radius (float): Non-dimensionalized radius made using advanced ratio.

    """

    return vectorized_axial_interf_f(
        lag_mult * prandtl_correction_values,
        non_dimensional_radius,
    )


def calculate_radial_thrust_coefs(
    radial_stations: ndarray,
    advanced_ratio: float,
    opt_axial_interf_factor: ndarray,
):
    """
    alculate thrust coefficient distribution along the radius.

    Args:
        radial_stations (ndarray): Non-dimensionalized radius along the blade.
        advanced_ratio (float): Ratio between velocity and rotational velocity multiplied by diameter.
        opt_axial_interf_factor (ndarray): Optimal axial interference factor.

    """

    return (
        np.pi
        * advanced_ratio**2
        * radial_stations
        * (1 + opt_axial_interf_factor)
        * opt_axial_interf_factor
    )


def check_input_output_values(
    radial_stations_spacing: float,
    radial_power_coefs: ndarray,
    radial_thrust_coefs: ndarray,
    free_stream_velocity: float,
    advanced_ratio: float,
    radial_stations: ndarray,
    radius: float,
    rotational_velocity: int,
) -> Tuple[float, float, float, float, float]:
    """
    Control input and output values, these values will be written in markdown file.

    Args:
        radial_stations_spacing (float): Spacing between r and r+dr.
        radial_thrust_coefs (ndarray): Radial distribution of thrust coefficient.
        radial_power_coefs (ndarray): Radial distribution of power coefficient.
        free_stream_velocity (float): Cruise velocity [m/s] get the real radius value.
        advanced_ratio (float): Ratio between velocity and rotational velocity multiplied by diameter.
        radial_stations (ndarray): Non-dimensionalized radius along the blade.
        radius (float): Blade radius [m].
        rotational_velocity (int): Blade velocity rotation [1/s].

    Returns:
        total_power_coefficient (float): Thrust coefficient at every radius [-].
        optimal_total_thrust_coefficient (float): Power coefficient at every radius [-].
        delta_pressure (float): Non-dimensionalized radius [-].
        thrust_density_ratio (float): Ratio between thrust and density [N m^3/kg].
        computed_total_thrust_coefficient (float): Thrust coefficient calculated in the program [-].
        eta (float): Efficiency of the propeller [-].

    """

    # Computation of the total power coefficient
    total_power_coefficient = np.sum(radial_stations_spacing * radial_power_coefs)
    optimal_total_thrust_coefficient = np.sum(radial_stations_spacing * radial_thrust_coefs)
    delta_pressure = (
        (radial_thrust_coefs)
        * (2 * free_stream_velocity**2)
        / (advanced_ratio**2 * math.pi * radial_stations)
    )

    # Computation of the thrust over density using the static pressure jump distribution
    thrust_density_ratio = np.sum(
        2 * math.pi * radial_stations * radius**2 * radial_stations_spacing * delta_pressure
    )

    # Computation of the thrust coefficient using thrust_density_ratio
    computed_total_thrust_coefficient = thrust_density_ratio / (
        rotational_velocity**2 * (2 * radius) ** 4
    )

    # Computation of the efficiency.
    eta = advanced_ratio * (optimal_total_thrust_coefficient / total_power_coefficient)

    return (
        total_power_coefficient,
        optimal_total_thrust_coefficient,
        thrust_density_ratio,
        computed_total_thrust_coefficient,
        eta,
    )


def thrust_calculator(
    radial_stations: ndarray,
    total_thrust_coefficient: float,
    radius: float,
    free_stream_velocity: float,
    prandtl_correction: bool,
    blades_number: int,
    rotational_velocity: int,
) -> Tuple[float, float, float, float, float, float]:
    """
    Performing of a calculation to obtain thrust and power coefficients distribution.

    Args:
        radial_stations (ndarray): Non-dimensionalized radius along the blade.
        total_thrust_coefficient (float): Total thrust coefficient [TODO: Find unit].
        radius (float): Blade radius [m].
        free_stream_velocity (float): Cruise velocity [m/s].
        prandtl_correction (bool): Correction for tip losses.
        blades_number (int): Blades propeller number.
        rotational_velocity (int): Blade velocity rotation [1/s].

    Returns:
        TODO: Documentate return of thrust_calculator.

    """
    # TODO: Improve this function...

    results_dir = get_results_directory("SU2Run")
    md = MarkdownDoc(Path(results_dir, "su2actuatordisk.md"))

    log.info("Start of thrust calculation distribution")

    EPSILON = 5e-20

    advanced_ratio = free_stream_velocity / (rotational_velocity * (radius * 2))
    omega = rotational_velocity * 2 * np.pi

    vectorized_axial_interf_f = np.vectorize(axial_interference_function)

    prandtl_correction_values = get_prandtl_correction_values(
        radial_stations, prandtl_correction, blades_number, omega, radius, free_stream_velocity
    )

    log.info(f"Prandtl correction= {prandtl_correction}")

    md.h2("Actuator disk calculation")
    md.h3("Input values")
    md.p(f"Selected total thrust coeff= {total_thrust_coefficient:.4f}")
    md.p(f"Radius= {radius:.4f} m")
    md.p(f"Number of radial station= {len(radial_stations)}")
    md.p(f"Advanced ratio= {advanced_ratio:.4f}")
    md.p(f"Free stream velocity= {free_stream_velocity:.4f} m/s")
    md.p(f"Prandtl correction= {prandtl_correction:.4f}")
    md.p(f"Number of blades= {blades_number}")

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

    first_lagrange_multiplier = np.sum(induced_velocity_distribution) / (
        free_stream_velocity * len(radial_stations)
    )

    # Computation of the first try axial interference factor distribution
    initial_axial_interference_factor = get_corrected_axial_factor(
        vectorized_axial_interf_f,
        first_lagrange_multiplier,
        prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_0 = calculate_radial_thrust_coefs(
        radial_stations, advanced_ratio, initial_axial_interference_factor
    )

    # Compute the error with respect to the thrust coefficient given in input
    initial_error = get_error(radial_stations_spacing, dCt_0, total_thrust_coefficient)
    log.info("Start of error calculation.")

    # Computation of the second try Lagrange multiplicator
    last_lagrange_multiplier = first_lagrange_multiplier + 0.1

    # Computation of the second try axial interference factor distribution
    old_axial_interference_factor = get_corrected_axial_factor(
        vectorized_axial_interf_f,
        last_lagrange_multiplier,
        prandtl_correction_values,
        non_dimensional_radius,
    )

    dCt_old = calculate_radial_thrust_coefs(
        radial_stations, advanced_ratio, old_axial_interference_factor
    )

    # Compute the error with respect to the thrust coefficient given in input
    old_error = get_error(radial_stations_spacing, dCt_old, total_thrust_coefficient)

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
        new_axial_interference_factor = get_corrected_axial_factor(
            vectorized_axial_interf_f,
            new_lagrange_multiplier,
            prandtl_correction_values,
            non_dimensional_radius,
        )

        dCt_new = calculate_radial_thrust_coefs(
            radial_stations, advanced_ratio, new_axial_interference_factor
        )

        new_total_thrust_coefficient = radial_stations_spacing * np.sum(dCt_new)

        new_error = new_total_thrust_coefficient - total_thrust_coefficient

        # Updating the stored values for the next iteration
        initial_error = old_error
        old_error = new_error

        first_lagrange_multiplier = last_lagrange_multiplier
        last_lagrange_multiplier = new_lagrange_multiplier

    log.info("Error has been estimated.")

    # Calculate radial Thrust coefficient at each stations
    optimal_axial_interference_factor = get_corrected_axial_factor(
        vectorized_axial_interf_f,
        new_lagrange_multiplier,
        prandtl_correction_values,
        non_dimensional_radius,
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
    # ???
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

    log.info("Finished estimating Radial thrust and power coefficients.")

    (
        total_power_coefficient,
        optimal_total_thrust_coefficient,
        thrust_density_ratio,
        computed_total_thrust_coefficient,
        eta,
        
    ) = check_input_output_values(
        radial_stations_spacing,
        radial_power_coefs,
        radial_thrust_coefs,
        free_stream_velocity,
        advanced_ratio,
        radial_stations,
        radius,
        rotational_velocity,
    )

    md.h3("Output values")
    md.p(f"Optimal total thrust coefficient= {optimal_total_thrust_coefficient:.4f}")
    md.p("Total thrust coefficient computed")
    md.p(f"using the static pressure jump= {computed_total_thrust_coefficient:.4f}")
    md.p(f"Power coefficient distribution integral= {total_power_coefficient:.4f}")
    md.p(f"Thrust over Density= {thrust_density_ratio:.4f} N m^3/kg")
    md.p(f"Efficiency= {eta:.4f}")

    return (
        radial_thrust_coefs,
        radial_power_coefs,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl_correction_values,
    )


def write_header(file: TextIO) -> TextIO:
    """Write the header of the actuator disk file.

    Args:
        file (file): Input file in which the header will be written.
    Returns:
        file (file): Output file in which the header is written.

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
    file: TextIO,
    inlet_marker: str,
    outlet_marker: str,
    center: Tuple,
    axis: Tuple,
    radius: float,
    advanced_ratio: float,
    radial_stations: ndarray,
    radial_thrust_coefs: ndarray,
    radial_power_coefs: ndarray,
) -> None:
    """
    Updates file with rotor or propeller definitions from CPACS file.

    Args:
        file (file): Input file to update.
        inlet_marker (str): Marker of the inlet of the actuator disk.
        outlet_marker (str): Marker of the outlet of the actuator disk.
        center (tuple): Center of the actuator disk (x,y,z).
        axis (tuple): Axis of the actuator disk (x,y,z).
        radius (float): Radius of the actuator disk.
        advanced_ratio (float): Advance ratio.
        radial_stations (ndarray): Non-dimensionalized radius along the blade.
        radial_thrust_coefs (ndarray): Thrust coefficient at each radial_stations.
        radial_power_coefs (ndarray): Power coefficient at each radial_stations.

    Returns:
        file (TextIO): Output file where the actuator disk file is written.

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

    log.info("ActuatorDisk.dat file generated.")

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
