from math import pi, sqrt, acos, exp, fabs
import numpy as np
import pylab as pl

##########################
###     Functions      ###
##########################


def optimal_prop(
    stations,
    total_thrust_coefficient,
    radius,
    hub_radius,
    advanced_ratio,
    free_stream_velocity,
    prandtl,
    blades_number,
):
    def axial_interference_factor_distribution(w0, non_dimensional_radius):

        # Function used to compute the value of the axial interference factor using the inviscid theory of the optimal propeller

        axial_interference_factor = (w0 * non_dimensional_radius**2) / (
            non_dimensional_radius**2 + (1 + (w0)) ** 2
        )
        return axial_interference_factor

    def print_external_file(CTrs, CPrs):

        # Function used to write the actuator disk input data file
        file = open("ActuatorDisk.dat", "w")
        file.write(
            "# Automatic generated actuator disk input data file using the Optimal Propeller code.\n"
        )
        file.write("# Data file needed for the actuator disk VARIABLE_LOAD type.\n")
        file.write(
            "# The load distribution is obtained using the inviscid theory of the optimal propeller\n"
        )
        file.write("# using global data.\n")
        file.write("#\n")
        file.write("# The first three lines must be filled.\n")
        file.write("# An example of this file can be found in the TestCases directory.\n")
        file.write("#\n")
        file.write("# Author: Ettore Saetta, Lorenzo Russo, Renato Tognaccini.\n")
        file.write("# Theoretical and Applied Aerodynamic Research Group (TAARG),\n")
        file.write("# University of Naples Federico II\n")
        file.write(
            "# -------------------------------------------------------------------------------------\n"
        )
        file.write("#\n")
        file.write("MARKER_ACTDISK= \n")
        file.write("CENTER= \n")
        file.write("AXIS= \n")
        file.write("RADIUS= " + str(radius) + "\n")
        file.write("ADV_RATIO= " + str(advanced_ratio) + "\n")
        file.write("NROW= " + str(stations) + "\n")
        file.write("# rs=r/R        dCT/drs       dCP/drs       dCR/drs\n")

        for i in range(0, stations):
            file.write(f"  {r[i]:.7f}     {CTrs[i]:.7f}     {CPrs[i]:.7f}     0.0\n")

        file.close()

    ##########################
    ###        Main        ###
    ##########################
    # Screen output
    print("------------------ Optimal Propeller vsn 7.0.6 ------------------")
    print("| Computation of the optimal dCT/dr and dCP/dr distributions.   |")
    print("| Based on the inviscid theory of the optimal propeller.        |")
    print("|                                                               |")
    print("| This code is used to generate the actuator disk input data    |")
    print("| file needed for the VARIABLE_LOAD actuator disk type          |")
    print("| implemented in SU2 7.0.6.                                     |")
    print("|                                                               |")
    print("| Author: Ettore Saetta, Lorenzo Russo, Renato Tognaccini.      |")
    print("| Theoretical and Applied Aerodynamic Research Group (TAARG),   |")
    print("| University of Naples Federico II.                             |")
    print("-----------------------------------------------------------------")

    print("")
    print("Warning: present version requires input in SI units.")
    print("")

    dstations = float(stations)

    # Resize the vectors using the number of radial stations.
    r = np.empty(stations)
    non_dimensional_radius = np.empty(stations)
    dCp = np.empty(stations)
    induced_velocity_distribution = np.empty(stations)
    new_axial_interference_factor = np.empty(stations)
    old_axial_interference_factor = np.empty(stations)
    initial_axial_interference_factor = np.empty(stations)
    ap_old = np.empty(stations)
    dCt_new = np.empty(stations)
    dCt_old = np.empty(stations)
    dCt_0 = np.empty(stations)
    delta_pressure = np.empty(stations)
    correction_function = np.empty(stations)
    optimal_axial_interference_factor = np.empty(stations)
    optimal_rotational_interference_factor = np.empty(stations)
    dCt_optimal = np.empty(stations)

    if prandtl == True:
        corr = True

    else:
        corr = False

    # Computation of the non-dimensional hub radius.
    rs_hub = hub_radius / radius

    # Computation of the non-dimensional radial stations.
    for i in range(1, stations + 1):
        r[i - 1] = i / dstations
        if r[i - 1] <= rs_hub:
            i_hub = i - 1

    # Computation of the propeller diameter.
    diameter = 2 * radius
    # Computation of the propeller angular velocity (Rounds/s).
    n = free_stream_velocity / (diameter * advanced_ratio)
    # Computation of the propeller angular velocity (Rad/s).
    omega = n * 2 * pi

    # Computation of the tip loss Prandtl correction function F.
    if corr == True:
        for i in range(0, stations):
            correction_function[i] = (2 / pi) * acos(
                exp(
                    -0.5
                    * blades_number
                    * (1 - r[i])
                    * sqrt(1 + (omega * radius / free_stream_velocity) ** 2)
                )
            )

    else:
        for i in range(0, stations):
            correction_function[i] = 1.0

    # Computation of the non-dimensional radius chi=Omega*r/free_stream_velocity.
    for i in range(0, stations):
        non_dimensional_radius[i] = omega * r[i] * radius / free_stream_velocity

    eps = 5e-20
    # Computation of the propeller radial stations spacing.
    radial_stations_spacing = 1.0 / stations

    # Computation of the first try induced velocity distribution.
    for i in range(0, stations):
        induced_velocity_distribution[i] = (2 / free_stream_velocity**2) * (
            (-1 / free_stream_velocity)
            + sqrt(
                1
                + (
                    (diameter**4 * (total_thrust_coefficient) * n**2)
                    / (free_stream_velocity**2 * pi * r[i])
                )
            )
        )

    # Computation of the first try Lagrange moltiplicator.
    first_lagrange_moltiplicator = 0.0
    for i in range(0, stations):
        first_lagrange_moltiplicator += induced_velocity_distribution[i]

    first_lagrange_moltiplicator = first_lagrange_moltiplicator / (free_stream_velocity * stations)

    # Computation of the first try axial interference factor distribution.
    for i in range(0, stations):
        initial_axial_interference_factor[i] = axial_interference_factor_distribution(
            first_lagrange_moltiplicator * correction_function[i],
            non_dimensional_radius[i],
        )

    # Computation of the thrust coefficient distribution
    for i in range(0, stations):
        dCt_0[i] = (
            pi
            * advanced_ratio**2
            * r[i]
            * (1 + initial_axial_interference_factor[i])
            * initial_axial_interference_factor[i]
        )

    # Computation of the total thrust coefficient.
    initial_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        initial_total_thrust_coefficient += radial_stations_spacing * dCt_0[i]

    # Compute the error with respect to the thrust coefficient given in input.
    inital_error = initial_total_thrust_coefficient - total_thrust_coefficient
    print("CONVERGENCE HISTORY:")
    print(inital_error)

    # Computation of the second try Lagrange moltiplicator.
    last_lagrange_moltiplicator = first_lagrange_moltiplicator + 0.1

    # Computation of the second try axial interference factor distribution.
    for i in range(0, stations):
        old_axial_interference_factor[i] = axial_interference_factor_distribution(
            last_lagrange_moltiplicator * correction_function[i],
            non_dimensional_radius[i],
        )

    # Computation of the thrust coefficient distribution
    for i in range(0, stations):
        dCt_old[i] = (
            pi
            * advanced_ratio**2
            * r[i]
            * (1 + old_axial_interference_factor[i])
            * old_axial_interference_factor[i]
        )

    # Computation of the total thrust coefficient.
    old_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        old_total_thrust_coefficient += radial_stations_spacing * dCt_old[i]

    # Compute the error with respect to the thrust coefficient given in input.
    old_error = old_total_thrust_coefficient - total_thrust_coefficient
    print(old_error)

    ##########################
    ###     Iterations     ###
    ##########################
    # Iterate using the false position methods.
    # Based on the error from the thrust coefficient given in input.
    iteration = 2
    new_error = old_error
    while fabs(new_error) >= eps and inital_error != old_error:

        iteration += 1

        # Computation of the new Lagrange moltiplicator value based on the false position method.
        new_lagrange_moltiplicator = (
            last_lagrange_moltiplicator * inital_error - first_lagrange_moltiplicator * old_error
        ) / (inital_error - old_error)

        # Computation of the new axial interference factor distribution.
        for i in range(0, stations):
            new_axial_interference_factor[i] = axial_interference_factor_distribution(
                new_lagrange_moltiplicator * correction_function[i],
                non_dimensional_radius[i],
            )

        # Computation of the new thrust coefficient distribution.
        for i in range(0, stations):
            dCt_new[i] = (
                pi
                * advanced_ratio**2
                * r[i]
                * (1 + new_axial_interference_factor[i])
                * new_axial_interference_factor[i]
            )

        # Computation of the new total thrust coefficient.
        new_total_thrust_coefficient = 0.0
        for i in range(i_hub, stations):
            new_total_thrust_coefficient += radial_stations_spacing * dCt_new[i]

        # Computation of the total thrust coefficient error with respect to the input value.
        new_error = new_total_thrust_coefficient - total_thrust_coefficient

        print(new_error)

        # Updating the stored values for the next iteration.
        inital_error = old_error
        old_error = new_error

        first_lagrange_moltiplicator = last_lagrange_moltiplicator
        last_lagrange_moltiplicator = new_lagrange_moltiplicator

    # Computation of the correct axial and rotational interference factors (a and ap).
    for i in range(0, stations):
        optimal_axial_interference_factor[i] = axial_interference_factor_distribution(
            new_lagrange_moltiplicator * correction_function[i],
            non_dimensional_radius[i],
        )
        optimal_rotational_interference_factor[i] = (
            new_lagrange_moltiplicator * correction_function[i]
        ) * (
            (1 + new_lagrange_moltiplicator * correction_function[i])
            / (
                non_dimensional_radius[i] * non_dimensional_radius[i]
                + (1 + new_lagrange_moltiplicator * correction_function[i]) ** 2
            )
        )

    # Computation of the correct thrust coefficient distribution.
    for i in range(0, stations):
        dCt_optimal[i] = (
            pi
            * advanced_ratio**2
            * r[i]
            * (1 + optimal_axial_interference_factor[i])
            * optimal_axial_interference_factor[i]
        )

    # Computation of the correct power coefficient distribution.
    for i in range(0, stations):
        dCp[i] = (radius * 4 * pi / (n**3 * diameter**5)) * (
            free_stream_velocity**3
            * (1 + optimal_axial_interference_factor[i]) ** 2
            * optimal_axial_interference_factor[i]
            * r[i]
            * radius
            + omega**2
            * free_stream_velocity
            * (1 + optimal_axial_interference_factor[i])
            * optimal_rotational_interference_factor[i] ** 2
            * (r[i] * radius) ** 3
        )

    ##########################
    ###   Check Results    ###
    ##########################
    # Computation of the total power coefficient.
    total_power_coefficient = 0.0
    for i in range(i_hub, stations):
        total_power_coefficient += radial_stations_spacing * dCp[i]

    # Computation of the total thrust coefficient.
    optimal_total_thrust_coefficient = 0.0
    for i in range(i_hub, stations):
        optimal_total_thrust_coefficient += radial_stations_spacing * dCt_optimal[i]

    # Computation of the static pressure jump distribution.
    for i in range(0, stations):
        delta_pressure[i] = (
            (dCt_optimal[i]) * (2 * free_stream_velocity**2) / (advanced_ratio**2 * pi * r[i])
        )

    # Computation of the thrust over density using the static pressure jump distribution.
    thrust_density_ratio = 0.0
    for i in range(i_hub, stations):
        thrust_density_ratio += (
            2 * pi * r[i] * radius**2 * radial_stations_spacing * delta_pressure[i]
        )

    # Computation of the thrust coefficient using thrust_density_ratio.
    computed_total_thrust_coefficient = thrust_density_ratio / (n**2 * diameter**4)

    # Computation of the efficiency.
    eta = advanced_ratio * (optimal_total_thrust_coefficient / total_power_coefficient)

    # Screen output used to check that everything worked correcty.
    print("%%%%%%%%%%%%%%%%%%%%%%%%% CHECK OUTPUT VALUES %%%%%%%%%%%%%%%%%%%%%%%%%")
    print(f"       dCT distribution integral: {optimal_total_thrust_coefficient:.4f}")
    print(
        f"       dCT computed using the static pressure jump: {computed_total_thrust_coefficient:.4f}"
    )
    print(f"       dCP distribution integral: {total_power_coefficient:.4f}")
    print(f"       Thrust over Density (T/rho): {thrust_density_ratio:.4f} [N*m^3/kg]")
    print(f"       Efficiency eta: {eta:.4f}")
    print(f"       w0/free_stream_velocity: {new_lagrange_moltiplicator:.4f}")
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    ##########################
    ###    File Writing    ###
    ##########################
    # Write the actuator disk configuration file
    file = open("ActuatorDisk.cfg", "w")

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

    print("SU2 file generated!")

    # Write the actuator disk data file.
    # This is the actuator disk input data file.
    print_external_file(dCt_optimal, dCp)

    ##########################
    ###        Plots       ###
    ##########################
    # Automatically plot the computed propeller performance.

    f1 = pl.figure(1)
    pl.plot(r, dCt_optimal, "r", markersize=4, label="$\\frac{dCT}{d\overline{r}}$")
    pl.plot(r, dCp, "k", markersize=4, label="$\\frac{dCP}{d\overline{r}}$")
    pl.grid(True)
    pl.legend(numpoints=3)
    pl.xlabel("$\overline{r}$")
    pl.ylabel("")
    pl.title("Load Distribution")

    f1 = pl.figure(2)
    pl.plot(
        non_dimensional_radius,
        optimal_axial_interference_factor,
        "r",
        markersize=4,
        label="$a$",
    )
    pl.plot(
        non_dimensional_radius,
        optimal_rotational_interference_factor,
        "k",
        markersize=4,
        label="$a^1$",
    )
    pl.grid(True)
    pl.legend(numpoints=3)
    pl.xlabel("$\chi$")
    pl.ylabel("")
    pl.title("Interference Factors")

    if corr == True:
        f1 = pl.figure(3)
        pl.plot(r, correction_function, "k", markersize=4)
        pl.grid(True)
        pl.xlabel("$\overline{r}$")
        pl.ylabel("$F(\overline{r})$")
        pl.title("Tip Loss Prandtl Correction Function")

    pl.show()

    return
