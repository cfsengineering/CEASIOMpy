"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

Python version: >=3.7

| Author: Verdier Loïc
| Creation: 2019-10-24

TODO:
    * Modify the code where there are "TODO"
    * Not getting value from Incremental map (control surf) for now!
    * Should we also save results as report (text file)

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import matplotlib.pyplot as plt
from ambiance import Atmosphere
from ceasiompy.StabilityStatic.func.func_static import (
    extract_subelements,
    get_index,
    get_unic,
    interpolation,
    order_correctly,
    plot_multicurve,
    trim_condition,
    trim_derivative,
)
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.xpath import MASSBREAKDOWN_XPATH, STABILITY_STATIC_XPATH
from cpacspy.cpacsfunctions import add_float_vector, create_branch, get_value, get_value_or_default
from cpacspy.cpacspy import CPACS

log = get_logger(__file__.split(".")[0])

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def static_stability_analysis(cpacs_path, cpacs_out_path):
    """Function to analyse a full Aeromap

    Function 'static_stability_analysis' analyses longitudinal static static
    stability and directional static.

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file

    Returns:
        *   Advertisements certifying if the aircraft is stable or Not
        *   In case of longitudinal static UNstability or invalid test on data:
                -	Plot cms VS aoa for constant Alt, Mach and different aos
                -	Plot cms VS aoa for const alt and aos=0 and different mach
                -	plot cms VS aoa for constant mach, aos=0 and different altitudes
        *  In case of directional static UNstability or invalid test on data:
                -	Pcot cml VS aos for constant Alt, Mach and different aoa
                -	Plot cml VS aos for const alt and aoa and different mach
                -	plot cml VS aos for constant mach, AOA and different altitudes
        *  Plot one graph of  cruising angles of attack for different mach and altitudes

    Make the following tests:            (To put in the documentation)
        *   Check the CPACS path
        *   For longitudinal static stability analysis:
                -   If there is more than one angle of attack for a given altitude, mach, aos
                -   If cml values are only zeros for a given altitude, mach, aos
                -   If there one aoa value which is repeated for a given altitude, mach, aos
        *   For directional static stability analysis:
                -   If there is more than one angle of sideslip for a given altitude, mach, aoa
                -   If cms values are only zeros for a given altitude, mach, aoa
                -   If there one aos value which is repeated for a given altitude, mach, aoa
    """

    cpacs = CPACS(str(cpacs_path))

    # TODO: add as CPACS option
    plot_for_different_mach = False  # To check Mach influence
    plot_for_different_alt = False  # To check Altitude influence

    #  Get aeromap uid
    aeromap_uid = get_value(cpacs.tixi, STABILITY_STATIC_XPATH + "/aeroMapUid")
    log.info("The following aeroMap will be analysed: " + aeromap_uid)

    show_plots = get_value_or_default(cpacs.tixi, STABILITY_STATIC_XPATH + "/showPlots", False)
    save_plots = get_value_or_default(cpacs.tixi, STABILITY_STATIC_XPATH + "/savePlots", False)

    # Aircraft mass configuration
    selected_mass_config_xpath = STABILITY_STATIC_XPATH + "/massConfiguration"
    mass_config = get_value(cpacs.tixi, selected_mass_config_xpath)
    print("Mass configuration: " + mass_config)
    # TODO: use get value or default instead and deal with not mass config
    log.info("The aircraft mass configuration used for analysis is: " + mass_config)

    mass_config_xpath = MASSBREAKDOWN_XPATH + "/designMasses/" + mass_config + "/mass"
    if cpacs.tixi.checkElement(mass_config_xpath):
        m = get_value(cpacs.tixi, mass_config_xpath)  # aircraft mass [Kg]
    else:
        raise ValueError(
            f" !!! The mass configuration : {mass_config} is not defined in the CPACS file !!!"
        )

    # Wing plane AREA.
    s = cpacs.aircraft.ref_area  # Wing area : s  for non-dimonsionalisation of aero data.

    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    alt_list = aeromap.get("altitude")
    mach_list = aeromap.get("machNumber")
    aoa_list = aeromap.get("angleOfAttack")
    aos_list = aeromap.get("angleOfSideslip")
    cl_list = aeromap.get("cl")
    cd_list = aeromap.get("cd")
    cml_list = aeromap.get("cml")
    cms_list = aeromap.get("cms")
    cmd_list = aeromap.get("cmd")

    alt_unic = get_unic(alt_list)
    mach_unic = get_unic(mach_list)
    aos_unic = get_unic(aos_list)
    aoa_unic = get_unic(aoa_list)

    # TODO: get incremental map from CPACS
    # Incremental map elevator
    incrementalMap = False  # if increment map available
    # aeromap_xpath = cpacs.tixi.uIDGetXPath(aeromap_uid)
    # dcms_xpath = aeromap_xpath + '/aeroPerformanceMap/incrementMaps/incrementMap'  + ' ....to complete'

    # TODO from incremental map
    # dcms_list = [0.52649,0.53744,0.54827,0.55898,0.56955,0.58001,0.59033,0.6005,0.61053,0.62043,0.63018,0.63979,0.64926,0.65859,0.66777,0.67684,0.53495,0.54603,0.55699,0.56783,0.57854,0.58912,0.59957,0.60986,0.62002,0.63004,0.63991,0.64964,0.65923,0.66867,0.67798,0.68717,0.55,0.56131,0.5725,0.58357,0.59451,0.60531,0.61598,0.62649,0.63687,0.64709,0.65718,0.66712,0.67691,0.68658,0.69609,0.70548,0.57333,0.585,0.59655,0.60796,0.61925,0.63038,0.64138,0.65224,0.66294,0.67349,0.68389,0.69415,0.70427,0.71424,0.72408,0.7338,0.60814,0.62033,0.63239,0.6443,0.65607,0.6677,0.67918,0.6905,0.70168,0.7127,0.72357,0.7343,0.74488,0.75532,0.76563,0.77581,0.66057,0.6735,0.68628,0.69891,0.71139,0.72371,0.73588,0.74789,0.75974,0.77144,0.78298,0.79438,0.80562,0.81673,0.82772,0.83858,\
    # 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,\
    # -0.61653,-0.61254,-0.60842,-0.60419,-0.59988,-0.59549,-0.59105,-0.58658,-0.5821,-0.57762,-0.57318,-0.56879,-0.56447,-0.56025,-0.55616,-0.55221,-0.62605,-0.62194,-0.6177,-0.61336,-0.60894,-0.60444,-0.59988,-0.59531,-0.59072,-0.58614,-0.58159,-0.57711,-0.5727,-0.56841,-0.56423,-0.5602,-0.64293,-0.63862,-0.63418,-0.62963,-0.62499,-0.62029,-0.61554,-0.61076,-0.60598,-0.60123,-0.5965,-0.59185,-0.58728,-0.58282,-0.5785,-0.57433,-0.66906,-0.6644,-0.65963,-0.65475,-0.64978,-0.64476,-0.63971,-0.63461,-0.62954,-0.62449,-0.61949,-0.61456,-0.60973,-0.60503,-0.60048,-0.59609,-0.70787,-0.70268,-0.69739,-0.692,-0.68653,-0.68101,-0.67546,-0.66991,-0.66437,-0.65888,-0.65344,-0.6481,-0.64289,-0.63781,-0.6329,-0.62819,-0.76596,-0.75994,-0.75382,-0.74762,-0.74135,-0.73505,-0.72874,-0.72243,-0.71617,-0.70997,-0.70387,-0.69788,-0.69205,-0.68639,-0.68094,-0.67573]
    # dcms are given for a relative deflection of [-1,0,1] of the

    # # TODO get from CPACS
    # elevator_deflection = 15

    # Gather trim aoa conditions
    trim_alt_longi_list = []
    trim_mach_longi_list = []
    trim_aoa_longi_list = []
    trim_aos_longi_list = []
    trim_legend_longi_list = []
    trim_derivative_longi_list = []

    # Gather trim aos_list for different Alt & mach , for aoa = 0
    trim_alt_lat_list = []
    trim_mach_lat_list = []
    trim_aoa_lat_list = []
    trim_aos_lat_list = []
    trim_legend_lat_list = []
    trim_derivative_lat_list = []

    # Gather trim aos_list for different Alt & mach , for aoa = 0
    trim_alt_direc_list = []
    trim_mach_direc_list = []
    trim_aoa_direc_list = []
    trim_aos_direc_list = []
    trim_legend_direc_list = []
    trim_derivative_direc_list = []

    # To store in cpacs result
    longi_unstable_cases = []
    lat_unstable_cases = []
    direc_unstable_cases = []

    cpacs_stability_longi = "True"
    cpacs_stability_lat = "True"
    cpacs_stability_direc = "True"

    # Aero analyses for all given altitude, mach and aos_list, over different
    for alt in alt_unic:

        Atm = Atmosphere(alt)
        g = Atm.grav_accel[0]
        a = Atm.speed_of_sound[0]
        rho = Atm.density[0]

        # Find index of altitude which have the same value
        idx_alt = [i for i in range(len(alt_list)) if alt_list[i] == alt]

        # Prepar trim condition lists
        trim_alt_longi = []
        trim_mach_longi = []
        trim_aoa_longi = []
        trim_aos_longi = []
        trim_legend_longi = []
        trim_derivative_longi = []

        # Prepar trim condition lists
        trim_alt_lat = []
        trim_mach_lat = []
        trim_aoa_lat = []
        trim_aos_lat = []
        trim_legend_lat = []
        trim_derivative_lat = []

        # Prepar trim condition lists
        trim_alt_direc = []
        trim_mach_direc = []
        trim_aoa_direc = []
        trim_aos_direc = []
        trim_legend_direc = []
        trim_derivative_direc = []

        for mach in mach_unic:
            u0 = a * mach
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]

            # Longitudinal stability
            # Analyse in function of the angle of attack for given, alt, mach and aos_list
            # Prepare variables for plots
            plot_cms = []
            plot_aoa = []
            plot_legend = []
            plot_title = (
                r"Pitch moment coefficient $C_M$ vs $\alpha$ @ Atl = "
                + str(alt)
                + "m, and Mach = "
                + str(mach)
            )
            xlabel = r"$\alpha$ [°]"
            ylabel = r"$C_M$ [-]"
            # Init for determining if it's an unstable case
            longitudinaly_stable = True
            # by default, cms don't  cross 0 line
            crossed = False

            # Find index at which  aos= 0
            idx_aos = [j for j in range(len(aos_list)) if aos_list[j] == 0]
            find_idx = get_index(idx_alt, idx_mach, idx_aos)

            # If find_idx is empty an APM function would have corrected before
            # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
            if len(find_idx) == 1:
                log.info(
                    "Longitudinal : only one data, one aoa("
                    + str(aoa_list[find_idx[0]])
                    + "), for Altitude =  "
                    + str(alt)
                    + "[m] , Mach = "
                    + str(mach)
                    + "  and aos = 0 , no stability analyse will be performed"
                )
                cpacs_stability_longi = "NotCalculated"
            elif len(find_idx) > 1:  # if there is at least 2 values in find_idx :

                # Find all cms_list values for index corresponding to an altitude, a mach, an aos_list=0, and different aoa_list
                cms = []
                aoa = []
                cl = []
                cd = []
                for index in find_idx:
                    cms.append(cms_list[index])
                    aoa.append(aoa_list[index])
                    cl.append(cl_list[index])
                    cd.append(cd_list[index])

                # Save values which will be plot
                plot_cms.append(cms)
                plot_aoa.append(aoa)
                curve_legend = r"$\beta$ = 0°"
                plot_legend.append(curve_legend)

                # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                aoa_good = True
                for jj in range(len(aoa) - 1):
                    if aoa[jj] == aoa[jj + 1]:
                        aoa_good = False
                        log.error(
                            "Alt = {} , at least 2 aoa values are equal in aoa list: {} at Mach= {}, aos = 0".format(
                                alt, aoa, mach
                            )
                        )
                        break

                if aoa_good:
                    # Required lift for level flight
                    cl_required = (m * g) / (0.5 * rho * u0**2 * s)
                    (trim_aoa, idx_trim_before, idx_trim_after, ratio) = trim_condition(
                        alt, mach, cl_required, cl, aoa
                    )

                    if trim_aoa:
                        trim_cms = interpolation(cms, idx_trim_before, idx_trim_after, ratio)
                        pitch_moment_derivative_deg = (
                            cms[idx_trim_after] - cms[idx_trim_before]
                        ) / (aoa[idx_trim_after] - aoa[idx_trim_before])
                        # Find incremental cms
                        if incrementalMap:
                            for index, mach_number in enumerate(mach_unic, 0):
                                if mach_number == mach:
                                    mach_index = index
                            dcms_before = dcms_list[mach_index * len(aoa_unic) + idx_trim_before]
                            dcms_after = dcms_list[mach_index * len(aoa_unic) + idx_trim_after]
                            dcms = dcms_before + ratio * (dcms_after - dcms_before)
                            trim_elevator_relative_deflection = -trim_cms / dcms
                            trim_elevator = (
                                trim_elevator_relative_deflection * elevator_deflection
                            )  # Trim elevator deflection in [°]
                        else:
                            dcms = None
                            trim_elevator = None
                    else:
                        trim_cms = None
                        pitch_moment_derivative_deg = None
                        dcms = None
                        trim_elevator = None

                    fig = plt.figure(figsize=(9, 3))
                    plot_title___ = r"$C_L$ and $C_m$ vs $\alpha$ at Mach = {}".format(mach)
                    plt.title(plot_title___, fontdict=None, loc="center", pad=None)
                    plt.plot(aoa, cl, marker="o", markersize=4, linewidth=1)
                    plt.plot(aoa, cms, marker="+", markerfacecolor="orange", markersize=12)
                    plt.plot(
                        [aoa[0], aoa[-1]],
                        [cl_required, cl_required],
                        markerfacecolor="red",
                        markersize=12,
                    )
                    plt.legend([r"$C_L$", r"$C_M$", r"$C_{Lrequired}$"])
                    ax = plt.gca()
                    ax.annotate(
                        r"$\alpha$ [°]",
                        xy=(1, 0),
                        ha="right",
                        va="top",
                        xycoords="axes fraction",
                        fontsize=12,
                    )
                    # ax.annotate('Coefficient', xy=(0,1), ha='left', va='center', xycoords='axes fraction', fontsize=12)
                    plt.grid(True)

                    if show_plots:
                        plt.show()

                # Conclusion about stability, if the cms curve has crossed the 0 line and there is not 2 repeated aoa for the same alt, mach and aos.
                # if  idx_trim_before != idx_trim_after allow to know if the cm curve crosses the 0 line. '

                if idx_trim_before != idx_trim_after and aoa_good:
                    if pitch_moment_derivative_deg < 0:
                        log.info("Vehicle longitudinally statically stable.")
                        trim_alt_longi.append(alt)
                        trim_mach_longi.append(mach)
                        trim_aoa_longi.append(trim_aoa)
                        trim_aos_longi.append(0)
                        trim_derivative_longi.append(pitch_moment_derivative_deg)

                    elif pitch_moment_derivative_deg == 0:
                        longitudinaly_stable = False
                        log.error(
                            "Alt = "
                            + str(alt)
                            + "Vehicle longitudinally statically neutral stable."
                        )
                    else:  # pitch_moment_derivative_deg > 0
                        longitudinaly_stable = False
                        log.error(
                            "Alt = " + str(alt) + "Vehicle *NOT* longitudinally statically stable."
                        )

                # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                if not longitudinaly_stable:
                    longi_unstable_cases.append([alt, mach, 0])
                    # To write in the output CPACS that the aircraft is not longitudinaly stable
                    cpacs_stability_longi = "False"
            # PLot cms VS aoa for constant Alt, Mach and different aos
            if plot_cms:
                plot_multicurve(
                    plot_cms,
                    plot_aoa,
                    plot_legend,
                    plot_title,
                    xlabel,
                    ylabel,
                    show_plots,
                    save_plots,
                )

            ## LATERAL
            plot_cmd = []
            plot_aos = []
            plot_legend = []
            plot_title = (
                r"Roll moment coefficient $C_L$ vs $\beta$ @ Atl = "
                + str(alt)
                + "m, and Mach = "
                + str(mach)
            )
            xlabel = r"$\beta$ [°]"
            ylabel = r"$C_L$ [-]"
            # Init for determining if it is an unstability case
            laterally_stable = True
            # Find INDEX
            for aoa in aoa_unic:

                # by default, don't  cross 0 line
                crossed = False
                idx_aoa = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa]
                find_idx = get_index(idx_alt, idx_mach, idx_aoa)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                if len(find_idx) == 1:
                    log.info(
                        "Lateral-Directional : only one data, one aos ("
                        + str(aos_list[find_idx[0]])
                        + "), for Altitude = "
                        + str(alt)
                        + "[m], Mach = "
                        + str(mach)
                        + " and aoa = "
                        + str(aoa)
                        + " no stability analyse performed"
                    )
                    cpacs_stability_lat = "NotCalculated"

                elif len(find_idx) > 1:  # if there is at least 2 values in find_idx
                    cmd = []
                    aos = []
                    for index in find_idx:
                        cmd.append(
                            -cmd_list[index]
                        )  # menus sign because cmd sign convention on CEASIOMpy is the opposite as books convention
                        aos.append(aos_list[index])
                    aos, cmd = order_correctly(
                        aos, cmd
                    )  # To roder the lists with values for growing aos
                    #  If cmd Curve crosses th 0 line more than once na stability analysis can be performed
                    curve_legend = r"$\alpha$ = " + str(aoa) + r" °"

                    # Save values which will be plotted
                    plot_cmd.append(cmd)
                    plot_aos.append(aos)
                    plot_legend.append(curve_legend)

                    aos_good = True
                    for jj in range(len(aos) - 1):
                        if aos[jj] == aos[jj + 1]:
                            aos_good = False
                            log.error(
                                "Alt = {} , at least 2 aos values are equal in aos list: {} , Mach= {}, aos = {}".format(
                                    alt, aoa, mach, aos
                                )
                            )
                            break

                    if aos_good:
                        (
                            cruise_aos,
                            roll_moment_derivative,
                            idx_trim_before,
                            idx_trim_after,
                            ratio,
                        ) = trim_derivative(alt, mach, cmd, aos)

                    if idx_trim_before != idx_trim_after and aos_good:
                        if roll_moment_derivative < 0:
                            log.info("Vehicle laterally statically stable.")
                            if aoa == 0:
                                trim_alt_lat.append(alt)
                                trim_mach_lat.append(mach)
                                trim_aoa_lat.append(cruise_aos)
                                trim_aos_lat.append(aoa)
                                trim_derivative_lat.append(roll_moment_derivative)
                        if roll_moment_derivative == 0:
                            laterally_stable = False
                            log.error(
                                "At alt = "
                                + str(alt)
                                + "Vehicle laterally statically neutral stable."
                            )
                        if roll_moment_derivative > 0:
                            laterally_stable = False
                            log.error(
                                "Alt = " + str(alt) + "Vehicle *NOT* laterally statically stable."
                            )

                    # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                    if not laterally_stable:
                        lat_unstable_cases.append([alt, mach, aoa])
                        # To write in the output CPACS that the aircraft is not longitudinaly stable
                        cpacs_stability_lat = "False"

            # PLot cmd VS aos for constant alt, mach and different aoa if not stable
            if plot_cmd:
                plot_multicurve(
                    plot_cmd,
                    plot_aos,
                    plot_legend,
                    plot_title,
                    xlabel,
                    ylabel,
                    show_plots,
                    save_plots,
                )

            ## Directional
            plot_cml = []
            plot_aos = []
            plot_legend = []
            plot_title = (
                r"Yaw moment coefficient $C_N$ vs $\beta$ @ Atl = "
                + str(alt)
                + "m, and Mach = "
                + str(mach)
            )
            xlabel = r"$\beta$ [°]"
            ylabel = r"$C_N$ [-]"
            # Init for determining if it is an unstability case
            dirrectionaly_stable = True
            # Find INDEX
            for aoa in aoa_unic:
                # by default, don't  cross 0 line
                crossed = False
                idx_aoa = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa]
                find_idx = get_index(idx_alt, idx_mach, idx_aoa)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list,
                # no analyse can be performed
                if len(find_idx) == 1:
                    log.info(
                        "Laterral-Directional : only one data, one aos ("
                        + str(aos_list[find_idx[0]])
                        + "), for Altitude = "
                        + str(alt)
                        + "[m], Mach = "
                        + str(mach)
                        + " and aoa = "
                        + str(aoa)
                        + " no stability analyse performed"
                    )
                    cpacs_stability_direc = "NotCalculated"

                elif len(find_idx) > 1:  # if there is at least 2 values in find_idx
                    cml = []
                    aos = []
                    for index in find_idx:
                        cml.append(-cml_list[index])
                        # neg because cml convention on CEASIOMpy is the opposite as books convention
                        aos.append(aos_list[index])
                    aos, cml = order_correctly(aos, cml)  # To order values with growing aos
                    # If cml curve crosses the 0 line more than once na stability analysis can
                    # be performed
                    curve_legend = r"$\alpha$ = " + str(aoa) + r" °"

                    # Save values which will be plot
                    plot_cml.append(cml)
                    plot_aos.append(aos)
                    plot_legend.append(curve_legend)

                    aos_good = True
                    for jj in range(len(aos) - 1):
                        if aos[jj] == aos[jj + 1]:
                            aos_good = False
                            log.error(
                                f"Alt = {alt}, at least 2 aos values are equal in aos list: {aoa},"
                                f"Mach= {mach}, aos = {aos}"
                            )
                            break

                    if aos_good:
                        (
                            cruise_aos,
                            side_moment_derivative,
                            idx_trim_before,
                            idx_trim_after,
                            ratio,
                        ) = trim_derivative(alt, mach, cml, aos)

                    if idx_trim_before != idx_trim_after and aos_good:
                        if side_moment_derivative > 0:
                            log.info("Vehicle directionally statically stable.")
                            if aoa == 0:
                                trim_alt_direc.append(alt)
                                trim_mach_direc.append(mach)
                                trim_aoa_direc.append(cruise_aos)
                                trim_aos_direc.append(aoa)
                                trim_derivative_direc.append(side_moment_derivative)
                        if side_moment_derivative == 0:
                            dirrectionaly_stable = False
                            log.error(
                                "At alt = "
                                + str(alt)
                                + "Vehicle directionally statically neutral stable."
                            )
                        if side_moment_derivative < 0:
                            dirrectionaly_stable = False
                            log.error(
                                "Alt = "
                                + str(alt)
                                + "Vehicle *NOT* directionally statically stable."
                            )

                    # If not stable store the [alt, mach, aos] at which the aircraft is unstable.
                    if not dirrectionaly_stable:
                        direc_unstable_cases.append([alt, mach, aoa])
                        # To write in CPACS output that the aircraft is not longitudinaly stable
                        cpacs_stability_direc = "False"

            # PLot cml VS aos for constant alt, mach and different aoa if not stable
            if plot_cml:
                plot_multicurve(
                    plot_cml,
                    plot_aos,
                    plot_legend,
                    plot_title,
                    xlabel,
                    ylabel,
                    show_plots,
                    save_plots,
                )

        # Add trim conditions for the given altitude (longi analysis)
        if trim_aoa_longi:
            trim_aoa_longi_list.append(trim_aoa_longi)
            trim_mach_longi_list.append(trim_mach_longi)
            trim_legend_longi_list.append("Altitude = " + str(alt) + "[m]")
            trim_alt_longi_list.append(trim_alt_longi)
            trim_aos_longi_list.append(trim_aos_longi)
            trim_derivative_longi_list.append(trim_derivative_longi)

        if trim_aos_lat:
            trim_aos_lat_list.append(trim_aos_lat)
            trim_mach_lat_list.append(trim_mach_lat)
            trim_legend_lat_list.append("Alt = " + str(alt) + "[m]")
            trim_alt_lat_list.append(trim_alt_lat)
            trim_aoa_lat_list.append(trim_aoa_lat)
            trim_derivative_lat_list.append(trim_derivative_lat)

        # Add trim conditions for the given altitude (direcanalysis)
        if trim_aos_direc:
            trim_aos_direc_list.append(trim_aos_direc)
            trim_mach_direc_list.append(trim_mach_direc)
            trim_legend_direc_list.append("Alt = " + str(alt) + "[m]")
            trim_alt_direc_list.append(trim_alt_direc)
            trim_aoa_direc_list.append(trim_aoa_direc)
            trim_derivative_direc_list.append(trim_derivative_direc)

        # MACH PLOTS
        if plot_for_different_mach:  # To check Altitude Mach
            ## LONGI
            # Plot cms vs aoa for const alt and aos = 0 and different mach
            idx_aos = [k for k in range(len(aos_list)) if aos_list[k] == 0]
            plot_cms = []
            plot_aoa = []
            plot_legend = []
            plot_title = (
                r"Pitch moment coefficient $C_M$ vs $\alpha$ @ Atl = "
                + str(alt)
                + r"m, and $\beta$ = 0 °"
            )
            xlabel = r"$\alpha$ [°]"
            ylabel = r"$C_M$ [-]"
            # Init for determining if it is an unstability case
            longitudinaly_stable = True

            for mach in mach_unic:
                idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
                find_idx = get_index(idx_alt, idx_aos, idx_mach)

                # If there is only one value in Find_idx
                # An error message has been already printed through the first part of the code
                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases:
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos:
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cms_list values for index corresponding to an altitude, a mach,
                    # an aos_list=0, and different aoa_list
                    cms = []
                    aoa = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])
                    # Save values which will be plot
                    plot_cms.append(cms)
                    plot_aoa.append(aoa)
                    curve_legend = "Mach = " + str(mach)
                    plot_legend.append(curve_legend)
            # PLot cms VS aoa for constant Alt, aoa and different mach
            if plot_cms:
                plot_multicurve(
                    plot_cms,
                    plot_aoa,
                    plot_legend,
                    plot_title,
                    xlabel,
                    ylabel,
                    show_plots,
                    save_plots,
                )

            ## LATERAL
            # Plot cmd vs aos for const alt and aoa and different mach
            for aoa in aoa_unic:
                idx_aoa = [k for k in range(len(aoa_list)) if aoa_list[k] == aoa]
                plot_cmd = []
                plot_aos = []
                plot_legend = []
                plot_title = (
                    r"Roll moment coefficient $C_L$ vs $\beta$ @ Atl = "
                    + str(alt)
                    + r"m, and $\alpha$= "
                    + str(aoa)
                    + r" °"
                )
                xlabel = r"$\beta$ [°]"
                ylabel = r"$C_L$ [-]"

                # Init for determining if it is an unstability case
                laterally_stable = True

                for mach in mach_unic:
                    idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
                    find_idx = get_index(idx_alt, idx_aoa, idx_mach)

                    # If there is only one value in find_idx
                    # An error message has been already printed through the first part of the code

                    # Check if it is an unstability case detected previously
                    for combination in lat_unstable_cases:
                        if (
                            combination[0] == alt
                            and combination[1] == mach
                            and combination[2] == aoa
                        ):
                            laterally_stable = False

                    # If there is at list 2 values in find_idx :
                    if len(find_idx) > 1:
                        # Find all cmd_list values for index corresponding to an altitude, a mach,
                        # an aos_list=0, and different aoa_list
                        cmd = []
                        aos = []
                        for index in find_idx:
                            cmd.append(-cmd_list[index])
                            aos.append(aos_list[index])
                        aos, cmd = order_correctly(aos, cmd)  # To order values with growing aos

                        # Save values which will be plot
                        plot_cmd.append(cmd)
                        plot_aos.append(aos)
                        curve_legend = "Mach = " + str(mach)
                        plot_legend.append(curve_legend)

                if plot_cmd:
                    # Plot cmd VS aos for constant Alt, aoa and different mach
                    plot_multicurve(
                        plot_cmd,
                        plot_aos,
                        plot_legend,
                        plot_title,
                        xlabel,
                        ylabel,
                        show_plots,
                        save_plots,
                    )

            ## Directional
            # Plot cml vs aos for const alt and aoa and different mach
            for aoa in aoa_unic:
                idx_aoa = [k for k in range(len(aoa_list)) if aoa_list[k] == aoa]
                plot_cml = []
                plot_aos = []
                plot_legend = []
                plot_title = (
                    r"Yaw moment coefficient $C_N$ vs $\beta$ @ Atl = "
                    + str(alt)
                    + r"m, and $\alpha$= "
                    + str(aoa)
                    + r" °"
                )
                xlabel = r"$\beta$ [°]"
                ylabel = r"$C_N$ [-]"

                # Init for determining if it is an unstability case
                dirrectionaly_stable = True

                for mach in mach_unic:
                    idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
                    find_idx = get_index(idx_alt, idx_aoa, idx_mach)
                    # If there is only one value in find_idx
                    # An error message has been already printed through the first part of the code

                    # Check if it is an unstability case detected previously
                    for combination in direc_unstable_cases:
                        if (
                            combination[0] == alt
                            and combination[1] == mach
                            and combination[2] == aoa
                        ):
                            dirrectionaly_stable = False

                    # If there is at list 2 values in find_idx :
                    if len(find_idx) > 1:
                        # Find all cml_list values for index corresponding to an altitude, a mach,
                        # an aos_list=0, and different aoa_list
                        cml = []
                        aos = []
                        for index in find_idx:
                            cml.append(-cml_list[index])
                            aos.append(aos_list[index])
                        aos, cml = order_correctly(aos, cml)  # To order values with growing aos

                        # Save values which will be plot
                        plot_cml.append(cml)
                        plot_aos.append(aos)
                        curve_legend = "Mach = " + str(mach)
                        plot_legend.append(curve_legend)

                if plot_cml:
                    # Plot cml VS aos for constant Alt, aoa and different mach
                    plot_multicurve(
                        plot_cml,
                        plot_aos,
                        plot_legend,
                        plot_title,
                        xlabel,
                        ylabel,
                        show_plots,
                        save_plots,
                    )
            ############ MACH  PLOTS END ##########

    # TRIM CONDITIONS PLOTS
    # Plot trim_aoa VS mach for different alt
    # If there is at least 1 element in list of trim conditions then, plot them
    if trim_derivative_longi_list:
        log.info("graph : trim aoa vs mach genrated")
        plot_multicurve(
            trim_aoa_longi_list,
            trim_mach_longi_list,
            trim_legend_longi_list,
            r"$\alpha_{trim}$ vs Mach",
            "Mach",
            r"$\alpha_{trim}$ [°]",
            show_plots,
            save_plots,
        )
        log.info("graph : pitch moment derivative at trim vs mach genrated")
        plot_multicurve(
            trim_derivative_longi_list,
            trim_mach_longi_list,
            trim_legend_longi_list,
            r"$C_{M_{\alpha trim}}$ vs Mach",
            "Mach",
            r"$C_{M_{\alpha trim}}$ [1/°]",
            show_plots,
            save_plots,
        )

    if trim_derivative_lat_list:
        log.info("graph : roll moment derivative at trim vs mach genrated")
        plot_multicurve(
            trim_derivative_lat_list,
            trim_mach_lat_list,
            trim_legend_lat_list,
            r"$C_{L_{\beta trim}}$vs Mach",
            "Mach",
            r"$C_{L_{\beta trim}}$ [1/°]",
            show_plots,
            save_plots,
        )

    if trim_derivative_direc_list:
        log.info("graph : yaw moment at trim vs mach genrated")
        plot_multicurve(
            trim_derivative_direc_list,
            trim_mach_direc_list,
            trim_legend_direc_list,
            r"$C_{N_{\beta trim}}$ vs Mach",
            "Mach",
            r"$C_{N_{\beta trim}}$ [1/°]",
            show_plots,
            save_plots,
        )

    # ALTITUDE PLOTS
    if plot_for_different_alt:  # To check Altitude Influence
        # plot cms VS aoa for constant mach, aos= 0 and different altitudes:
        # Find index of altitude which have the same value
        idx_aos = [i for i in range(len(aos_list)) if aos_list[i] == 0]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
            # Prepare variables for plots
            plot_cms = []
            plot_aoa = []
            plot_legend = []
            plot_title = (
                r"Pitch moment coefficient $C_M$ vs $\alpha$ @ Mach = "
                + str(mach)
                + r" and $\beta$ = 0°"
            )
            xlabel = r"$\alpha$ [°]"
            ylabel = r"$C_M$ [-]"

            longitudinaly_stable = True

            # Find index of slip angle which have the same value
            for alt in alt_unic:
                idx_alt = [j for j in range(len(alt_list)) if alt_list[j] == alt]
                find_idx = get_index(idx_aos, idx_mach, idx_alt)

                # If find_idx is empty an APM function would have corrected before
                # If there is only one value  in  find_idx for a given Alt, Mach, aos_list,
                # no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases:
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos:
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cms_list values for index corresponding to an altitude, a mach,
                    # an aos_list=0, and different aoa_list
                    cms = []
                    aoa = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])

                    # Save values which will be plot
                    plot_cms.append(cms)
                    plot_aoa.append(aoa)
                    curve_legend = "Altitude = " + str(alt) + " m"
                    plot_legend.append(curve_legend)

            if plot_cms:
                # PLot cms VS aoa for constant  Mach, aos and different Alt
                plot_multicurve(
                    plot_cms,
                    plot_aoa,
                    plot_legend,
                    plot_title,
                    xlabel,
                    ylabel,
                    show_plots,
                    save_plots,
                )

        ## Lateral
        # plot cmd VS aos for constant mach, aoa_list and different altitudes:
        for aoa in aoa_unic:
            # Find index of altitude which have the same value
            idx_aoa = [i for i in range(len(aoa_list)) if aoa_list[i] == aoa]
            for mach in mach_unic:
                # Find index of mach which have the same value
                idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
                # Prepare variables for plots
                plot_cmd = []
                plot_aos = []
                plot_legend = []
                plot_title = (
                    r"Roll moment coefficient $C_L$ vs $\beta$ @ Mach = "
                    + str(mach)
                    + r" and $\alpha$= "
                    + str(aoa)
                    + r" °"
                )
                xlabel = r"$\beta$ [°]"
                ylabel = r"$C_L$ [-]"

                laterally_stable = True

                # Find index of slip angle which have the same value
                for alt in alt_unic:
                    idx_alt = [j for j in range(len(alt_list)) if alt_list[j] == alt]
                    find_idx = get_index(idx_aoa, idx_mach, idx_alt)
                    # If find_idx is empty an APM function would have corrected before
                    # If there there is only one value  in  find_idx for a given Alt, Mach,
                    # aos_list, no analyse can be performed
                    # An error message has been already printed through the first part of the code

                    # Check if it is an unstability case detected previously
                    for combination in lat_unstable_cases:
                        if (
                            combination[0] == alt
                            and combination[1] == mach
                            and combination[2] == aoa
                        ):
                            laterally_stable = False

                    # If there is at list 2 values in find_idx :
                    if len(find_idx) > 1:
                        # Find all cmd_list values for index corresponding to an altitude, a mach,
                        # an aos_list=0, and different aoa_list
                        cmd = []
                        aos = []
                        for index in find_idx:
                            cmd.append(-cmd_list[index])
                            aos.append(aos_list[index])

                        # Save values which will be plot
                        plot_cmd.append(cmd)
                        plot_aos.append(aos)
                        curve_legend = "Altitude = " + str(alt) + " m"
                        plot_legend.append(curve_legend)

                if plot_cmd:
                    # PLot cmd VS aos for constant  Mach, aoa and different alt
                    plot_multicurve(
                        plot_cmd,
                        plot_aos,
                        plot_legend,
                        plot_title,
                        xlabel,
                        ylabel,
                        show_plots,
                        save_plots,
                    )

        ## DIRECTIONAL
        # plot cml VS aos for constant mach, aoa_list and different altitudes:
        for aoa in aoa_unic:
            # Find index of altitude which have the same value
            idx_aoa = [i for i in range(len(aoa_list)) if aoa_list[i] == aoa]
            for mach in mach_unic:
                # Find index of mach which have the same value
                idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
                # Prepare variables for plots
                plot_cml = []
                plot_aos = []
                plot_legend = []
                plot_title = (
                    r"Yaw moment coefficient $C_N$ vs $\beta$ @ Mach = "
                    + str(mach)
                    + r" and $\alpha$= "
                    + str(aoa)
                    + r" °"
                )
                xlabel = r"$\beta$ [°]"
                ylabel = r"$C_N$ [-]"

                dirrectionaly_stable = True

                # Find index of slip angle which have the same value
                for alt in alt_unic:
                    idx_alt = [j for j in range(len(alt_list)) if alt_list[j] == alt]
                    find_idx = get_index(idx_aoa, idx_mach, idx_alt)

                    # Check if it is an unstability case detected previously
                    for combination in direc_unstable_cases:
                        if (
                            combination[0] == alt
                            and combination[1] == mach
                            and combination[2] == aoa
                        ):
                            dirrectionaly_stable = False

                    # If there is at list 2 values in find_idx :
                    if len(find_idx) > 1:
                        # Find all cml_list values for index corresponding to an altitude, a mach,
                        # an aos_list=0, and different aoa_list
                        cml = []
                        aos = []
                        for index in find_idx:
                            cml.append(-cml_list[index])
                            aos.append(aos_list[index])

                        # Save values which will be plot
                        plot_cml.append(cml)
                        plot_aos.append(aos)
                        curve_legend = "Altitude = " + str(alt) + " m"
                        plot_legend.append(curve_legend)

                if plot_cml:
                    # PLot cml VS aos for constant  Mach, aoa and different alt
                    plot_multicurve(
                        plot_cml,
                        plot_aos,
                        plot_legend,
                        plot_title,
                        xlabel,
                        ylabel,
                        show_plots,
                        save_plots,
                    )

    # Save in the CPACS file stability results:
    trim_alt_longi_list = extract_subelements(trim_alt_longi_list)
    trim_mach_longi_list = extract_subelements(trim_mach_longi_list)
    trim_aoa_longi_list = extract_subelements(trim_aoa_longi_list)
    trim_aos_longi_list = extract_subelements(trim_aos_longi_list)
    trim_derivative_longi_list = extract_subelements(trim_derivative_longi_list)

    trim_alt_lat_list = extract_subelements(trim_alt_lat_list)
    trim_mach_lat_list = extract_subelements(trim_mach_lat_list)
    trim_aoa_lat_list = extract_subelements(trim_aoa_lat_list)
    trim_aos_lat_list = extract_subelements(trim_aos_lat_list)
    trim_derivative_lat_list = extract_subelements(trim_derivative_lat_list)

    trim_alt_direc_list = extract_subelements(trim_alt_direc_list)
    trim_mach_direc_list = extract_subelements(trim_mach_direc_list)
    trim_aoa_direc_list = extract_subelements(trim_aoa_direc_list)
    trim_aos_direc_list = extract_subelements(trim_aos_direc_list)
    trim_derivative_direc_list = extract_subelements(trim_derivative_direc_list)

    # xpath definition
    # TODO: add uid of the coresponding aeropm for results
    longi_xpath = STABILITY_STATIC_XPATH + "/results/longitudinalStaticStable"
    lat_xpath = STABILITY_STATIC_XPATH + "/results/lateralStaticStable"
    direc_xpath = STABILITY_STATIC_XPATH + "/results/directionnalStaticStable"
    longi_trim_xpath = STABILITY_STATIC_XPATH + "/trimConditions/longitudinal"
    lat_trim_xpath = STABILITY_STATIC_XPATH + "/trimConditions/lateral"
    direc_trim_xpath = STABILITY_STATIC_XPATH + "/trimConditions/directional"

    create_branch(cpacs.tixi, longi_xpath)
    create_branch(cpacs.tixi, lat_xpath)
    create_branch(cpacs.tixi, direc_xpath)

    # Store in the CPACS the stability results
    cpacs.tixi.updateTextElement(longi_xpath, str(cpacs_stability_longi))
    cpacs.tixi.updateTextElement(lat_xpath, str(cpacs_stability_lat))
    cpacs.tixi.updateTextElement(direc_xpath, str(cpacs_stability_direc))

    create_branch(cpacs.tixi, longi_trim_xpath)
    create_branch(cpacs.tixi, lat_trim_xpath)
    create_branch(cpacs.tixi, direc_trim_xpath)

    if trim_alt_longi_list:
        add_float_vector(cpacs.tixi, longi_trim_xpath + "/altitude", trim_alt_longi_list)
        add_float_vector(cpacs.tixi, longi_trim_xpath + "/machNumber", trim_mach_longi_list)
        add_float_vector(cpacs.tixi, longi_trim_xpath + "/angleOfAttack", trim_aoa_longi_list)
        add_float_vector(cpacs.tixi, longi_trim_xpath + "/angleOfSideslip", trim_aos_longi_list)
    if trim_alt_lat_list:
        add_float_vector(cpacs.tixi, lat_trim_xpath + "/altitude", trim_alt_lat_list)
        add_float_vector(cpacs.tixi, lat_trim_xpath + "/machNumber", trim_mach_lat_list)
        add_float_vector(cpacs.tixi, lat_trim_xpath + "/angleOfAttack", trim_aoa_lat_list)
        add_float_vector(cpacs.tixi, lat_trim_xpath + "/angleOfSideslip", trim_aos_lat_list)
    if trim_alt_direc_list:
        add_float_vector(cpacs.tixi, direc_trim_xpath + "/altitude", trim_alt_direc_list)
        add_float_vector(cpacs.tixi, direc_trim_xpath + "/machNumber", trim_mach_direc_list)
        add_float_vector(cpacs.tixi, direc_trim_xpath + "/angleOfAttack", trim_aoa_direc_list)
        add_float_vector(cpacs.tixi, direc_trim_xpath + "/angleOfSideslip", trim_aos_direc_list)

    cpacs.tixi.save(str(cpacs_out_path))


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)

    static_stability_analysis(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
