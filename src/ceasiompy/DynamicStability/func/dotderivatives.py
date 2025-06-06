"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Unsteady-derivatives computations through PanelAero.
Notation used:
    1. Subscripts "_alpha", "_beta" represent derivative wrt to alpha or beta.
    2. fx, fy, fz represent drag, side, lift force.
    3. cx, cy, cz represent drag, side, lift coefficient.

| Author: Leon Deligny
| Creation: 2025-Feb-12

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math
import cmath

import numpy as np

from pandas import concat

from ceasiompy.utils.geometryfunctions import (
    wing_sections,
    elements_number,
    get_positionings,
)
from ceasiompy.DynamicStability.func.utils import (
    beta,
    alpha,
    complex_cross,
    complex_decomposition,
)

from panelaero import DLM
from numpy import ndarray
from pandas import DataFrame
from ambiance import Atmosphere
from ceasiompy.Database.func.storing import CeasiompyDb

from ceasiompy.DynamicStability.func.panelaeroconfig import (
    AeroModel,
    DetailedPlots,
)
from typing import (
    List,
    Dict,
    Tuple,
)

from ceasiompy import log
from ceasiompy.DynamicStability import MODULE_NAME
from ceasiompy.utils.commonxpaths import WINGS_XPATH

# =================================================================================================
#   METHODS
# =================================================================================================


def load_geometry(self) -> List:
    """
    Load geometry in PanelAero's format.

    Returns:
        (List): Wings in PanelAsero's format.

    """
    wing_cnt = elements_number(self.tixi, WINGS_XPATH, "wing")
    # used_wings = return_usedwings(self.tixi)

    wing_lists = []

    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"

        name_wing = self.tixi.getTextElement(wing_xpath + "/name")

        # if name_wing in used_wings.keys():
        log.info(f"Name of the wing: {name_wing}")

        # Wing Positionings
        _, pos_x_list, pos_y_list, pos_z_list = get_positionings(self.tixi, wing_xpath, "wing")

        # Wing Sections
        le_list = wing_sections(
            self.tixi,
            wing_xpath,
            pos_x_list,
            pos_y_list,
            pos_z_list,
            list_type="first_n_last",
        )
        first_le = le_list[0]
        last_le = le_list[1]

        x1, y1, z1, d12 = first_le[0], first_le[1], first_le[2], first_le[3]
        x4, y4, z4, d34 = last_le[0], last_le[1], last_le[2], last_le[3]

        wing_dict = {
            "EID": i_wing,  # str
            "CP": 0,  # int
            "n_span": self.nchordwise,  # int
            "n_chord": self.nspanwise,  # int
            "X1": np.array([x1, y1, z1]),
            "length12": d12,  # float
            "X4": np.array([x4, y4, z4]),
            "length43": d34,  # float
        }

        wing_lists.append(wing_dict)

    return wing_lists


def compute_velocity_attributes(
    atm: Atmosphere,
    mach: float,
    k_alpha_model: float,
    k_beta_model: float,
) -> Tuple[float, float, float]:
    """
    Compute arguments for PanelAero's model.

    Args:
        mach (float): Mach number.
        k_alpha_model (float): Reduced frequency for alpha oscillations.
        k_beta_model (float): Reduced frequency for beta oscillations.

    Returns:
        (Tuple[float, float, float]):
            - Angular frequency for alpha oscillations.
            - Angular frequency for beta oscillations.
            - Dynamic pressure.

    """

    # Velocity in m/s in atmospheric environment
    velocity = atm.speed_of_sound[0] * mach

    # Frequency
    omegaalpha = k_alpha_model * velocity  # 2 pi / T
    omegabeta = k_beta_model * velocity

    # Dynamic pressure
    q_dyn = atm.density[0] * (velocity**2) / 2.0

    return omegaalpha, omegabeta, q_dyn


def scale_coefficients(
    self,
    q_dyn: float,
    x_alpha: float,
    y_alpha: float,
    z_alpha: float,
    l_alpha: float,
    m_alpha: float,
    n_alpha: float,
    x_beta: float,
    y_beta: float,
    z_beta: float,
    l_beta: float,
    m_beta: float,
    n_beta: float,
    m_alphadot: float,
    z_alphadot: float,
    x_alphadot: float,
    y_betadot: float,
    l_betadot: float,
    n_betadot: float,
):
    """
    Scales coefficients accordingly.
    """

    log.info(
        f"Scaling using dyn pres.: {q_dyn}, surface: {self.s}, chord: {self.c}, span: {self.b}."
    )

    # Define variables
    qs = q_dyn * self.s
    qsb = qs * self.b
    qsc = qs * self.c

    # Compute coefficients
    cx_alpha = x_alpha / qs  # Force
    cy_alpha = y_alpha / qs  # Force
    cz_alpha = z_alpha / qs  # Force

    cl_alpha = l_alpha / qsb  # Moment
    cm_alpha = m_alpha / qsc  # Moment
    cn_alpha = n_alpha / qsb  # Moment

    cx_beta = x_beta / qs  # Force
    cy_beta = y_beta / qs  # Force
    cz_beta = z_beta / qs  # Force

    cl_beta = l_beta / qsb  # Moment
    cm_beta = m_beta / qsc  # Moment
    cn_beta = n_beta / qsb  # Moment

    # Compute dot coefficients
    cm_alphadot = m_alphadot / qsc  # Moment
    cz_alphadot = z_alphadot / qs  # Force
    cx_alphadot = x_alphadot / qs  # Force

    cy_betadot = y_betadot / qs  # Force
    cl_betadot = l_betadot / qsb  # Moment
    cn_betadot = n_betadot / qsb  # Moment

    return (
        cx_alpha,
        cy_alpha,
        cz_alpha,
        cl_alpha,
        cm_alpha,
        cn_alpha,
        cx_beta,
        cy_beta,
        cz_beta,
        cl_beta,
        cm_beta,
        cn_beta,
        cm_alphadot,
        cz_alphadot,
        cx_alphadot,
        cy_betadot,
        cl_betadot,
        cn_betadot,
    )


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def access_angle_derivatives(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> Tuple[float, float, float]:
    """
    Decomposition of real and imaginary part of f in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Initial angle.

    Returns:
        (Tuple[float, float, float]): x, y, z components of this decomposition.

    """

    cos_omega_t = np.cos(omega * t)
    sin_omega_t = np.sin(omega * t)

    x = ((f_real[0] * cos_omega_t) + (f_img[0] * sin_omega_t)) / angle_0
    y = ((f_real[1] * cos_omega_t) + (f_img[1] * sin_omega_t)) / angle_0
    z = ((f_real[2] * cos_omega_t) + (f_img[2] * sin_omega_t)) / angle_0

    return x, y, z


def access_angle_derivatives_np(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> ndarray:
    """
    Decomposition of real and imaginary part of f_derivative in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Initial angle.

    Returns:
        (Tuple[ndarray, ndarray, ndarray]): x, y, z components of this decomposition.

    """
    cos_omega_t = np.cos(omega * t)
    sin_omega_t = np.sin(omega * t)

    x = (f_real[0, :] * cos_omega_t + f_img[0, :] * sin_omega_t) / angle_0
    y = (f_real[1, :] * cos_omega_t + f_img[1, :] * sin_omega_t) / angle_0
    z = (f_real[2, :] * cos_omega_t + f_img[2, :] * sin_omega_t) / angle_0

    return np.array([x, y, z])


def access_angle_dot_derivatives(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> Tuple[float, float, float]:
    """
    Decomposition of real and imaginary part of f_dot in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Initial angle.

    Returns:
        (Tuple[float, float, float]): x, y, z components of this decomposition.

    """

    cos_omega_t = np.cos(omega * t)
    sin_omega_t = np.sin(omega * t)
    scale = angle_0 * omega

    x = (f_img[0] * cos_omega_t - f_real[0] * sin_omega_t) / scale
    y = (f_img[1] * cos_omega_t - f_real[1] * sin_omega_t) / scale
    z = (f_img[2] * cos_omega_t - f_real[2] * sin_omega_t) / scale

    return x, y, z


def access_angle_dot_derivatives_np(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> ndarray:
    """
    Decomposition of real and imaginary part of f in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Initial angle.

    Returns:
        (Tuple[ndarray, ndarray, ndarray]): x, y, z components of this decomposition.

    """
    cos_omega_t = np.cos(omega * t)
    sin_omega_t = np.sin(omega * t)
    scale = angle_0 * omega

    x = (f_img[0, :] * cos_omega_t - f_real[0, :] * sin_omega_t) / scale
    y = (f_img[1, :] * cos_omega_t - f_real[1, :] * sin_omega_t) / scale
    z = (f_img[2, :] * cos_omega_t - f_real[2, :] * sin_omega_t) / scale

    return np.array([x, y, z])


def compute_moments(aerogrid: Dict, forces: ndarray, x_hinge: float) -> ndarray:
    """
    Compute Moments using formula, M = sum_{j: panel} r_j cross f_j.

    Args:
        aerogrid (Dict): PanelAero model.
        forces (ndarray): Forces on each panel (aerogrid['n'], 3).
        x_hinge (float): x-th coordinate of center of gravity.

    Returns:
        moments (ndarray): Total moments (3, ).

    """

    # Moment computed at each panel (aerogrid['n'], 3)
    r = -aerogrid["offset_j"]
    r[:, 0] = r[:, 0] - x_hinge  # MODIFY x_ref, y_ref, z_ref if you uncomment

    if np.iscomplexobj(forces):
        m = complex_cross(r, forces.T)
    else:
        m = np.cross(r, forces.T)

    # Total moment (3, )
    moments = m.sum(axis=0)

    return moments


def get_main_wing_le(model: AeroModel) -> Tuple[float, float, float]:
    """
    Get leading edge of main wing.

    Args:
        model (AeroModel): PanelAero model.

    Returns:
        (Tuple[float, float, float]): x, y, z-th coordinate of leading edge.

    """

    wings_list = model.wings_list
    x1_values = [model.caerocards[i]["X1"][0] for i, _ in enumerate(wings_list)]
    min_x1_index = x1_values.index(min(x1_values))

    return (
        model.caerocards[min_x1_index]["X1"][0],
        model.caerocards[min_x1_index]["X1"][1],
        model.caerocards[min_x1_index]["X1"][2],
    )


def check_x_hinge(aerogrid: Dict, x_hinge: float) -> None:
    """
    Checks if x-th coordinate of hinge point in not in the aerogrid.

    Args:
        aerogrid (Dict): Aerogrid with coordinates of panels.
        x_hinge (float): x-th coordinate of hinge point.

    """

    # Make sure x_hinge \notin x
    if x_hinge in aerogrid["offset_j"][:, 0]:
        log.warning(
            "Error in PanelAero's Doublet Lattice Method."
            "Hinge point can not be equal to downwash control point."
        )


def compute_panel_forces(
    aerogrid: Dict,
    q_alpha_jj: ndarray,
    q_beta_jj: ndarray,
    omegaalpha: float,
    omegabeta: float,
    q_dyn: float,
    t: float,
    alpha_0: float,
    beta_0: float,
) -> Tuple[ndarray, ndarray]:
    """
    Compute alpha and beta forces on panels.

    Args:
        aerogrid (Dict): Aerogrid of geometry.
        q_alpha_jj (ndarray): PanelAero's DLM output for alpha oscillations.
        q_beta_jj (ndarray): PanelAero's DLM output.
        omegaalpha (float): Angular frequency of alpha.
        omegabeta (float): Angular frequency of beta.
        q_dyn (float): Dynamic pressure.
        t (float): Time [s].
        alpha_0 (float): Alpha amplitude.
        beta_0 (float): Beta amplitude.

    """

    # Define the angles in time
    alpha_angle = alpha(omegaalpha, t, alpha_0)
    beta_angle = beta(omegabeta, t, beta_0)

    c_a = cmath.cos(alpha_angle)
    s_a = cmath.sin(alpha_angle)

    # Rotations
    rotation_alpha = np.array(
        [  # -alpha(t) rotation
            [c_a, 0, s_a],
            [0, 1, 0],
            [-s_a, 0, c_a],
        ]
    )

    c_b = cmath.cos(beta_angle)
    s_b = cmath.sin(beta_angle)

    rotation_beta = np.array(
        [  # -beta(t) rotation
            [c_b, s_b, 0],
            [-s_b, c_b, 0],
            [0, 0, 1],
        ]
    )

    # Apply the rotation to the normals (3, aerogrid['n'])
    n_alpha = rotation_alpha.dot(aerogrid["N"].T)
    n_beta = rotation_beta.dot(aerogrid["N"].T)

    # Projection on x-axis
    vector = np.array([1, 0, 0])  # Velocity = (V_inf, 0, 0) at alpha = beta = 0
    n_alpha_x = vector.dot(n_alpha)
    n_beta_x = vector.dot(n_beta)

    # Induced downwash (aerogrid['n'], )
    w_alpha = n_alpha_x
    w_beta = n_beta_x

    # Complex pressure coefficients (aerogrid['n'], )
    cp_alpha = q_alpha_jj.dot(w_alpha)
    cp_beta = q_beta_jj.dot(w_beta)

    # Force on each panel (3, aerogrid['n'])
    alphaforces = -q_dyn * n_alpha * aerogrid["A"] * cp_alpha
    betaforces = -q_dyn * n_beta * aerogrid["A"] * cp_beta

    return alphaforces, betaforces


def get_mach_list(self, x_hinge: float) -> Tuple[List, List]:
    """
    Get list of machs where to compute the derivatives.
    """
    tol = 1e-5
    db = CeasiompyDb()
    db.connect_to_table(MODULE_NAME)
    data = db.get_data(
        table_name="derivatives_data",
        columns=["mach"],
        db_close=True,
        filters=[
            f"aircraft = '{self.aircraft_name}'",
            "method = 'DLM'",
            f"chord = {self.nchordwise}",
            f"span = {self.nspanwise}",
            f"x_ref BETWEEN {x_hinge - tol} AND {x_hinge + tol}",
            "y_ref = 0.0",
            "z_ref = 0.0",
        ],
    )

    mach_set = {row[0] for row in data}
    log.info(f"Already have {mach_set} in ceasiompy.db")

    return list(set(self.mach_list) - mach_set), ", ".join(str(mach) for mach in list(mach_set))


def compute_dot_derivatives(self, atm: Atmosphere) -> DataFrame:
    """
    Computes alpha and beta dot derivatives for SDSA.

    Source:
        https://www.overleaf.com/read/qjffvmtrzzhb#8fc920

    Returns:
        (DataFrame): Dot-derivatives per mach.

    """

    log.info("--- Loading Geometry into PanelAero ---")
    data = []

    # Load Geometry
    wings_list = load_geometry(self)
    model = AeroModel(wings_list)
    model.build_aerogrid()
    aerogrid = model.aerogrid

    # Plot grid before doing calculations
    if self.plot:
        log.info(f"Plotting PanelAero's aerogrid of aircraft {self.aircraft_name}.")
        plots = DetailedPlots(model)
        plots.plot_aerogrid()

    # Oscillation Parameters

    # k = 0 for Steady
    # 0 < k < 0.05 for Quasi-steady
    # 0.05 < k < 0.2 for Unsteady
    # 0.2 < k for Highly Unsteady
    # for reference: https://en.wikipedia.org/wiki/Reduced_frequency.

    k_nastran = 0.1  # = omega * length / (2 * velocity)

    # Amplitudes
    alpha_0 = beta_0 = 1e-6

    # Time (Value does not matter).
    # All computations are made in frequency domain.
    t = 0.0

    # Convert to radians
    alpha_0 = math.radians(alpha_0)
    beta_0 = math.radians(beta_0)

    # Use k from equation (2.1) in https://elib.dlr.de/136536/1/DLR-IB-AE-GO-2020-137_V1.05.pdf.
    k_alpha_model = 2 * k_nastran / self.c  # = omega / velocity
    k_beta_model = 2 * k_nastran / self.b  # = omega / velocity

    # Leading edge of airplane
    x_le, _, _ = get_main_wing_le(model)
    x_hinge = x_le + (self.c / 4)  # Hinge point on x-axis
    check_x_hinge(aerogrid, x_hinge)

    mach_list, non_mach_str = get_mach_list(self, x_hinge)

    log.info(f"--- Computing AIC Matrices for machs in {mach_list} ---")

    for mach in mach_list:
        log.info(f"--- Computing AIC Matrix for mach: {mach} ---")

        # AIC Matrix np.identity(model.aerogrid['n'])
        q_alpha_jj = DLM.calc_Qjj(aerogrid, Ma=mach, k=k_alpha_model)
        q_beta_jj = DLM.calc_Qjj(aerogrid, Ma=mach, k=k_beta_model)

        # Get angular frequencies
        omegaalpha, omegabeta, q_dyn = compute_velocity_attributes(
            atm, mach, k_alpha_model, k_beta_model
        )

        # Get forces on each panels at angle (alpha(t), beta(t))
        alphaforces, betaforces = compute_panel_forces(
            aerogrid,
            q_alpha_jj,
            q_beta_jj,
            omegaalpha,
            omegabeta,
            q_dyn,
            t,
            alpha_0,
            beta_0,
        )

        # Complex decomposition
        alphaforces_real, alphaforces_imag = complex_decomposition(alphaforces)
        betaforces_real, betaforces_imag = complex_decomposition(betaforces)

        # Total force, sum on each panels (3, )
        falpha = alphaforces.sum(axis=1)
        fbeta = betaforces.sum(axis=1)

        # Complex decomposition
        falpha_real, falpha_imag = complex_decomposition(falpha)
        fbeta_real, fbeta_imag = complex_decomposition(fbeta)

        ############################################################
        # Get derivatives at (angle, angle_dot) = (0, 0)
        ############################################################

        fx_alpha, fy_alpha, fz_alpha = access_angle_derivatives(
            falpha_real, falpha_imag, omegaalpha, t, alpha_0
        )
        fx_beta, fy_beta, fz_beta = access_angle_derivatives(
            fbeta_real, fbeta_imag, omegabeta, t, beta_0
        )

        m_alpha = compute_moments(
            aerogrid=aerogrid,
            forces=access_angle_derivatives_np(
                alphaforces_real, alphaforces_imag, omegaalpha, t, alpha_0
            ),
            x_hinge=x_hinge,
        )
        m_beta = compute_moments(
            aerogrid=aerogrid,
            forces=access_angle_derivatives_np(
                betaforces_real, betaforces_imag, omegabeta, t, beta_0
            ),
            x_hinge=x_hinge,
        )

        ############################################################
        # Get dot derivatives at (angle, angle_dot) = (0, 0)
        ############################################################

        fx_alphadot, _, fz_alphadot = access_angle_dot_derivatives(
            falpha_real, falpha_imag, omegaalpha, t, alpha_0
        )
        _, fy_betadot, _ = access_angle_dot_derivatives(
            fbeta_real, fbeta_imag, omegabeta, t, beta_0
        )

        m_alphadot = compute_moments(
            aerogrid=aerogrid,
            forces=access_angle_dot_derivatives_np(
                alphaforces_real, alphaforces_imag, omegaalpha, t, alpha_0
            ),
            x_hinge=x_hinge,
        )
        m_betadot = compute_moments(
            aerogrid=aerogrid,
            forces=access_angle_dot_derivatives_np(
                betaforces_real, betaforces_imag, omegabeta, t, beta_0
            ),
            x_hinge=x_hinge,
        )

        # Scale appropriately to access forces and moment coefficients
        (
            cx_alpha,
            cy_alpha,
            cz_alpha,
            cl_alpha,
            cm_alpha,
            cn_alpha,
            cx_beta,
            cy_beta,
            cz_beta,
            cl_beta,
            cm_beta,
            cn_beta,
            cm_alphaprim,
            cz_alphaprim,
            cx_alphaprim,
            cy_betaprim,
            cl_betaprim,
            cn_betaprim,
        ) = scale_coefficients(
            self,
            q_dyn,
            fx_alpha,
            fy_alpha,
            fz_alpha,
            m_alpha[0],
            m_alpha[1],
            m_alpha[2],
            fx_beta,
            fy_beta,
            fz_beta,
            m_beta[0],
            m_beta[1],
            m_beta[2],
            m_alphadot[1],
            fz_alphadot,
            fx_alphadot,
            fy_betadot,
            m_betadot[0],
            m_betadot[2],
        )

        # Append data
        data.append(
            {
                "mach": mach,
                "cx_alpha": cx_alpha,
                "cy_alpha": cy_alpha,
                "cz_alpha": cz_alpha,
                "cl_alpha": cl_alpha,
                "cm_alpha": cm_alpha,
                "cn_alpha": cn_alpha,
                "cx_beta": cx_beta,
                "cy_beta": cy_beta,
                "cz_beta": cz_beta,
                "cl_beta": cl_beta,
                "cm_beta": cm_beta,
                "cn_beta": cn_beta,
                "cm_alphaprim": cm_alphaprim,
                "cz_alphaprim": cz_alphaprim,
                "cx_alphaprim": cx_alphaprim,
                "cy_betaprim": cy_betaprim,
                "cl_betaprim": cl_betaprim,
                "cn_betaprim": cn_betaprim,
            }
        )

        log.info(f"Finished computing alpha-dot derivatives for mach: {mach}.")

    log.info("--- Finished computing alpha/beta-dot derivatives ---")

    # Convert the data list to a DataFrame
    df = DataFrame(data)

    self.model = model

    # Point where we compute moments
    df["x_ref"], df["y_ref"], df["z_ref"] = x_hinge, 0.0, 0.0

    # Save the DataFrame to a CSV file
    df.to_csv(self.dynamic_stability_dir / "alpha_beta_dot_derivatives.csv", index=False)

    return add_db_values(self, df, non_mach_str, x_hinge)


def add_db_values(self, df: DataFrame, non_mach_str: str, x_hinge: float) -> DataFrame:
    der_columns = [
        "mach",
        "x_ref",
        "y_ref",
        "z_ref",
        "cm_alphaprim",
        "cz_alphaprim",
        "cx_alphaprim",
        "cy_betaprim",
        "cl_betaprim",
        "cn_betaprim",
    ]
    db = CeasiompyDb()
    data = db.get_data(
        table_name="derivatives_data",
        columns=der_columns,
        db_close=True,
        filters=[
            f"mach IN ({non_mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            "method = 'DLM'",
            f"chord = {self.nchordwise}",
            f"span = {self.nspanwise}",
            f"x_ref = {x_hinge}",
            "y_ref = 0.0",
            "z_ref = 0.0",
        ],
    )
    
    if df.empty:
        df = DataFrame(columns=der_columns)

    return concat([df[der_columns], DataFrame(data, columns=der_columns)], ignore_index=True)
