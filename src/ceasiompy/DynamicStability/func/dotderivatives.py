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
import copy
import cmath
import numpy as np

from pandas import concat
from ceasiompy.utils.ceasiompyutils import get_value
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

from panelaero import VLM, DLM
from numpy import ndarray
from pandas import DataFrame
from ambiance import Atmosphere
from ceasiompy.Database.func.storing import CeasiompyDb

from ceasiompy.DynamicStability.func.panelaeroconfig import (
    AeroModel,
    DetailedPlots,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import WINGS_XPATH
from ceasiompy.DynamicStability.func import (
    BETA_CSV_NAME,
    ALPHA_CSV_NAME,
)
from ceasiompy.DynamicStability import (
    MODULE_NAME,
    DYNAMICSTABILITY_XREF_XPATH,
    DYNAMICSTABILITY_YREF_XPATH,
    DYNAMICSTABILITY_ZREF_XPATH,
    DYNAMICSTABILITY_DEFAULTREF_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def load_geometry(self) -> list:
    """
    Load geometry in PanelAero's format.

    Returns:
        (list): Wings in PanelAsero's format.

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


def scale_alpha_coefficients(
    self,
    q_dyn: float,
    x_alpha: float, y_alpha: float, z_alpha: float,
    l_alpha: float, m_alpha: float, n_alpha: float,
    m_alphadot: float, z_alphadot: float, x_alphadot: float,
) -> tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]:
    """
    Scale alpha(t)-dependent aero coefficients accordingly.
    """

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

    # Compute dot coefficients
    cm_alphadot = m_alphadot / qsc  # Moment
    cz_alphadot = z_alphadot / qs  # Force
    cx_alphadot = x_alphadot / qs  # Force

    return (
        cx_alpha, cy_alpha, cz_alpha,
        cl_alpha, cm_alpha, cn_alpha,
        cm_alphadot, cz_alphadot, cx_alphadot,
    )


def scale_beta_coefficients(
    self,
    q_dyn: float,
    x_beta: float,
    y_beta: float,
    z_beta: float,
    l_beta: float,
    m_beta: float,
    n_beta: float,
    y_betadot: float,
    l_betadot: float,
    n_betadot: float,
) -> tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]:
    """
    Scale beta(t)-coefficients accordingly.
    """

    # Define variables
    qs = q_dyn * self.s
    qsb = qs * self.b
    qsc = qs * self.c

    cx_beta = x_beta / qs  # Force
    cy_beta = y_beta / qs  # Force
    cz_beta = z_beta / qs  # Force

    cl_beta = l_beta / qsb  # Moment
    cm_beta = m_beta / qsc  # Moment
    cn_beta = n_beta / qsb  # Moment

    cy_betadot = y_betadot / qs  # Force
    cl_betadot = l_betadot / qsb  # Moment
    cn_betadot = n_betadot / qsb  # Moment

    return (
        cx_beta, cy_beta, cz_beta,
        cl_beta, cm_beta, cn_beta,
        cy_betadot, cl_betadot, cn_betadot,
    )


def access_angle_derivatives(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> tuple[float, float, float]:
    """
    Decomposition of real and imaginary part of f in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Amplitude.

    Returns:
        (tuple[float, float, float]): x, y, z components of this decomposition.

    """
    omega_t = omega * t
    cos_omega_t, sin_omega_t = np.cos(omega_t), np.sin(omega_t)

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
        (tuple[ndarray, ndarray, ndarray]): x, y, z components of this decomposition.

    """
    omega_t = omega * t
    cos_omega_t, sin_omega_t = np.cos(omega_t), np.sin(omega_t)

    x = (f_real[0, :] * cos_omega_t + f_img[0, :] * sin_omega_t) / angle_0
    y = (f_real[1, :] * cos_omega_t + f_img[1, :] * sin_omega_t) / angle_0
    z = (f_real[2, :] * cos_omega_t + f_img[2, :] * sin_omega_t) / angle_0

    return np.array([x, y, z])


def access_angle_dot_derivatives(
    f_real: ndarray, f_img: ndarray, omega: float, t: float, angle_0: float
) -> tuple[float, float, float]:
    """
    Decomposition of real and imaginary part of f_dot in (cos, sin) basis.

    Args:
        f_real (ndarray): Real part of f.
        f_img (ndarray): Imaginary part of f.
        omega (float): Angular frequency.
        t (float): Time.
        angle_0 (float): Initial angle.

    Returns:
        (tuple[float, float, float]): x, y, z components of this decomposition.

    """
    omega_t = omega * t
    scale = angle_0 * omega
    cos_omega_t, sin_omega_t = np.cos(omega_t), np.sin(omega_t)

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
        angle_0 (float): Amplitude.

    Returns:
        (tuple[ndarray, ndarray, ndarray]): x, y, z components of this decomposition.
    """
    scale = angle_0 * omega
    cos_omega_t, sin_omega_t = np.cos(omega * t), np.sin(omega * t)

    x = (f_img[0, :] * cos_omega_t - f_real[0, :] * sin_omega_t) / scale
    y = (f_img[1, :] * cos_omega_t - f_real[1, :] * sin_omega_t) / scale
    z = (f_img[2, :] * cos_omega_t - f_real[2, :] * sin_omega_t) / scale

    return np.array([x, y, z])


def compute_moments(
    aerogrid: dict,
    forces: ndarray,
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> ndarray:
    """
    Compute Moments using formula, M = sum_{j: panel} r_j cross f_j.

    Args:
        aerogrid (dict): PanelAero model.
        forces (ndarray): Forces on each panel (aerogrid['n'], 3).
        x_hinge (float): x-th coordinate of center of gravity.

    Returns:
        moments (ndarray): Total moments (3, ).
    """

    # Moment computed at each panel (aerogrid['n'], 3)
    r = -aerogrid["offset_j"]
    r[:, 0] -= x_hinge
    r[:, 1] -= y_hinge
    r[:, 2] -= z_hinge

    if np.iscomplexobj(forces):
        m = complex_cross(r, forces.T)
    else:
        m = np.cross(r, forces.T)

    # Total moment (3, )
    moments = m.sum(axis=0)

    return moments


def get_main_wing_le(model: AeroModel) -> tuple[float, float, float]:
    """
    Get leading edge of main wing.

    Args:
        model (AeroModel): PanelAero model.

    Returns:
        (tuple[float, float, float]): x, y, z-th coordinate of leading edge.

    """

    wings_list = model.wings_list
    x1_values = [model.caerocards[i]["X1"][0] for i, _ in enumerate(wings_list)]
    min_x1_index = x1_values.index(min(x1_values))

    return (
        model.caerocards[min_x1_index]["X1"][0],
        model.caerocards[min_x1_index]["X1"][1],
        model.caerocards[min_x1_index]["X1"][2],
    )


def check_x_hinge(aerogrid: dict, x_hinge: float) -> None:
    """
    Checks if x-th coordinate of hinge point in not in the aerogrid.

    Args:
        aerogrid (dict): Aerogrid with coordinates of panels.
        x_hinge (float): x-th coordinate of hinge point.

    """

    # Make sure x_hinge \notin x
    if x_hinge in aerogrid["offset_j"][:, 0]:
        log.warning(
            "Error in PanelAero's Doublet Lattice Method."
            "Hinge point can not be equal to downwash control point."
        )


def compute_alpha_panel_forces(
    aerogrid: dict,
    q_alpha_jj: ndarray,
    omegaalpha: float,
    q_dyn: float,
    t: float,
    alpha_0: float,
    aoa: float,
) -> ndarray:
    # Define the angles in time
    alpha_angle = alpha(omegaalpha, t, alpha_0, aoa)  # alpha(t)

    # -alpha(t) rotation
    c_a, s_a = cmath.cos(alpha_angle), cmath.sin(alpha_angle)
    rotation_alpha = np.array([
        [c_a, 0, s_a],
        [0, 1, 0],
        [-s_a, 0, c_a],
    ])

    # Apply the rotation to the normals (3, aerogrid['n'])
    n_alpha = rotation_alpha.dot(aerogrid["N"].T)
    # n_alpha = aerogrid["N"].T

    # Compute induced downwash
    # w_alpha = np.ones(aerogrid["n"]) * cmath.sin(alpha_angle)  # (aerogrid['n'], )
    normalized_v_inf = np.array([1, 0, 0])  # V_inf comes from x direction

    w_alpha = normalized_v_inf.dot(n_alpha)

    # Complex pressure coefficients (aerogrid['n'], )
    cp_alpha = q_alpha_jj.dot(w_alpha)

    # Force on each panel (3, aerogrid['n'])
    return -q_dyn * n_alpha * aerogrid["A"] * cp_alpha


def compute_beta_panel_forces(
    aerogrid: dict,
    q_beta_jj: ndarray,
    omegabeta: float,
    q_dyn: float,
    t: float,
    beta_0: float,
    aos: float,
) -> ndarray:
    # Define the angles in time
    beta_angle = beta(omegabeta, t, beta_0, aos)

    # -beta(t) rotation
    c_b, s_b = cmath.cos(beta_angle), cmath.sin(beta_angle)
    rotation_beta = np.array([
        [c_b, s_b, 0],
        [-s_b, c_b, 0],
        [0, 0, 1],
    ])

    # Apply the rotation to the normals (3, aerogrid['n'])
    n_beta = rotation_beta.dot(aerogrid["N"].T)

    # Compute induced downwash
    # w_beta = np.ones(aerogrid["n"]) * np.sin(aos)  # (aerogrid['n'], )
    normalized_v_inf = np.array([1, 0, 0])  # V_inf comes from x direction

    w_beta = normalized_v_inf.dot(n_beta)

    # Complex pressure coefficients (aerogrid['n'], )
    cp_beta = q_beta_jj.dot(w_beta)

    # Force on each panel (3, aerogrid['n'])
    return -q_dyn * n_beta * aerogrid["A"] * cp_beta


def get_alpha_aero_lists(
    self,
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> tuple[list, list, list, list, list[tuple[float, float, float, float]]]:
    """
    Get list of machs where to compute the derivatives.
    """
    tol = 1e-5
    db = CeasiompyDb()
    db.connect_to_table(MODULE_NAME + "_alpha")
    data = db.get_data(
        table_name="alpha_derivatives",
        columns=["alt", "mach", "aoa", "aos"],
        db_close=True,
        filters=[
            f"aircraft = '{self.aircraft_name}'",
            "method = 'DLM'",
            f"chord = {self.nchordwise}",
            f"span = {self.nspanwise}",
            f"x_ref BETWEEN {x_hinge - tol} AND {x_hinge + tol}",
            f"y_ref BETWEEN {y_hinge - tol} AND {y_hinge + tol}",
            f"z_ref BETWEEN {z_hinge - tol} AND {z_hinge + tol}",
        ],
    )

    # Build a set of tuples for fast lookup
    db_tuples = set((row[0], row[1], row[2], row[3]) for row in data)

    # Filter the input lists
    filtered = [
        (alt, mach, aoa, aos)
        for alt, mach, aoa, aos in zip(
            self.alt_list, self.mach_list, self.aoa_list, self.aos_list
        )
        if (alt, mach, aoa, aos) not in db_tuples
    ]

    # Unzip the filtered tuples back into separate lists
    if filtered:
        alt_out, mach_out, aoa_out, aos_out = zip(*filtered)
        return list(alt_out), list(mach_out), list(aoa_out), list(aos_out), list(db_tuples)
    else:
        return [], [], [], [], list(db_tuples)


def get_beta_aero_lists(
    self,
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> tuple[list, list, list, list, list[tuple[float, float, float, float]]]:
    """
    Get list of machs where to compute the derivatives.
    """
    tol = 1e-5
    db = CeasiompyDb()
    db.connect_to_table(MODULE_NAME + "_beta")
    data = db.get_data(
        table_name="beta_derivatives",
        columns=["alt", "mach", "aoa", "aos"],
        db_close=True,
        filters=[
            f"aircraft = '{self.aircraft_name}'",
            "method = 'DLM'",
            f"chord = {self.nchordwise}",
            f"span = {self.nspanwise}",
            f"x_ref BETWEEN {x_hinge - tol} AND {x_hinge + tol}",
            f"y_ref BETWEEN {y_hinge - tol} AND {y_hinge + tol}",
            f"z_ref BETWEEN {z_hinge - tol} AND {z_hinge + tol}",
        ],
    )

    # Build a set of tuples for fast lookup
    db_tuples = set((row[0], row[1], row[2], row[3]) for row in data)

    # Filter the input lists
    filtered = [
        (alt, mach, aoa, aos)
        for alt, mach, aoa, aos in zip(
            self.alt_list, self.mach_list, self.aoa_list, self.aos_list
        )
        if (alt, mach, aoa, aos) not in db_tuples
    ]

    # Unzip the filtered tuples back into separate lists
    if filtered:
        alt_out, mach_out, aoa_out, aos_out = zip(*filtered)
        return list(alt_out), list(mach_out), list(aoa_out), list(aos_out), list(db_tuples)
    else:
        return [], [], [], [], list(db_tuples)


def get_alpha_dot_derivatives(self) -> DataFrame:
    """
    Computes alpha dot derivatives for SDSA.

    Source:
        https://www.overleaf.com/read/qjffvmtrzzhb#8fc920

    Returns:
        (DataFrame): Dot-derivatives per mach.

    """

    log.info("--- Loading Geometry into PanelAero ---")
    alpha_data = []

    # Load Geometry
    wings_list = load_geometry(self)
    model = AeroModel(wings_list)
    model.build_aerogrid()
    aerogrid = model.aerogrid
    self.model = model

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
    # for reference: https://en.wikipedia.org/wiki/Reduced_frequency
    k_nastran = 0.1  # = omega * length / (2 * velocity)

    # Amplitudes
    alpha_0 = 1e-6

    # Time (Value does not matter).
    # All computations are made in frequency domain.
    t = 0.0

    # Convert to radians
    alpha_0 = math.radians(alpha_0)

    # Use k from equation (2.1) in https://elib.dlr.de/136536/1/DLR-IB-AE-GO-2020-137_V1.05.pdf
    # NOT nastran reduced frequency
    k_alpha_model = 2 * k_nastran / self.c  # = omega / velocity

    if get_value(self.tixi, DYNAMICSTABILITY_DEFAULTREF_XPATH):
        # Leading edge of airplane
        x_le, _, _ = get_main_wing_le(model)

        x_hinge: float = x_le + (self.c / 4)  # Hinge point on x-axis
        y_hinge: float = 0.0
        z_hinge: float = 0.0
    else:
        x_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_XREF_XPATH))
        y_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_YREF_XPATH))
        z_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_ZREF_XPATH))

    check_x_hinge(aerogrid, x_hinge)

    log.info("--- Computing AIC Matrices ---")

    # If you compute alpha derivatives
    alt_out, mach_out, aoa_out, _, in_db_list = get_alpha_aero_lists(
        self, x_hinge, y_hinge, z_hinge,
    )

    # Iterate through cases
    for i_case, alt in enumerate(alt_out):
        mach = mach_out[i_case]
        aoa = aoa_out[i_case]

        (
            cx_alpha, cy_alpha, cz_alpha,
            cl_alpha, cm_alpha, cn_alpha,
            cm_alphadot, cz_alphadot, cx_alphadot,
        ) = compute_alpha_dot_derivatives(
            self,
            alt, mach, aoa,
            aerogrid, k_alpha_model,
            t, alpha_0,
            x_hinge, y_hinge, z_hinge,
        )
        alpha_data.append({
            "alt": alt, "mach": mach, "aoa": aoa, "aos": 0.0,
            "cx_alpha": cx_alpha, "cy_alpha": cy_alpha, "cz_alpha": cz_alpha,
            "cl_alpha": cl_alpha, "cm_alpha": cm_alpha, "cn_alpha": cn_alpha,
            "cm_alphaprim": cm_alphadot,
            "cz_alphaprim": cz_alphadot,
            "cx_alphaprim": cx_alphadot,
        })

    log.info("--- Finished computing alpha-dot-derivatives ---")

    df_alpha = DataFrame(alpha_data)
    df_alpha["x_ref"], df_alpha["y_ref"], df_alpha["z_ref"] = x_hinge, y_hinge, z_hinge
    df_alpha.to_csv(self.dynamic_stability_dir / ALPHA_CSV_NAME, index=False)

    return add_alpha_db_values(
        self, df_alpha, in_db_list, x_hinge, y_hinge, z_hinge
    )


def get_beta_dot_derivatives(self) -> DataFrame:
    """
    Computes beta dot derivatives for SDSA.

    Source:
        https://www.overleaf.com/read/qjffvmtrzzhb#8fc920

    Returns:
        (DataFrame): Dot-derivatives per mach.

    """

    log.info("--- Loading Geometry into PanelAero ---")
    beta_data = []

    # Load Geometry
    wings_list = load_geometry(self)
    model = AeroModel(wings_list)
    model.build_aerogrid()
    aerogrid = model.aerogrid
    self.model = model

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
    # for reference: https://en.wikipedia.org/wiki/Reduced_frequency
    k_nastran = 0.1  # = omega * length / (2 * velocity)

    # Amplitudes
    beta_0 = 1e-6

    # Time (Value does not matter).
    # All computations are made in frequency domain.
    t = 0.0

    # Convert to radians
    beta_0 = math.radians(beta_0)

    # Use k from equation (2.1) in https://elib.dlr.de/136536/1/DLR-IB-AE-GO-2020-137_V1.05.pdf
    # NOT nastran reduced frequency
    k_beta_model = 2 * k_nastran / self.b  # = omega / velocity

    if get_value(self.tixi, DYNAMICSTABILITY_DEFAULTREF_XPATH):
        # Leading edge of airplane
        x_le, _, _ = get_main_wing_le(model)

        x_hinge: float = x_le + (self.c / 4)  # Hinge point on x-axis
        y_hinge: float = 0.0
        z_hinge: float = 0.0
    else:
        x_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_XREF_XPATH))
        y_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_YREF_XPATH))
        z_hinge = float(get_value(self.tixi, DYNAMICSTABILITY_ZREF_XPATH))

    check_x_hinge(aerogrid, x_hinge)

    log.info("--- Computing AIC Matrices ---")

    alt_out, mach_out, _, aos_out, in_db_list = get_beta_aero_lists(
        self, x_hinge, y_hinge, z_hinge,
    )

    # Iterate through cases
    for i_case, alt in enumerate(alt_out):
        mach = mach_out[i_case]
        aos = aos_out[i_case]

        (
            cx_beta, cy_beta, cz_beta,
            cl_beta, cm_beta, cn_beta,
            cy_betadot, cl_betadot, cn_betadot,
        ) = compute_beta_dot_derivatives(
            self,
            alt, mach, aos,
            aerogrid, k_beta_model,
            t, beta_0,
            x_hinge, y_hinge, z_hinge,
        )
        beta_data.append({
            "alt": alt, "mach": mach, "aoa": 0.0, "aos": aos,
            "cx_beta": cx_beta, "cy_beta": cy_beta, "cz_beta": cz_beta,
            "cl_beta": cl_beta, "cm_beta": cm_beta, "cn_beta": cn_beta,
            "cy_betaprim": cy_betadot,
            "cl_betaprim": cl_betadot,
            "cn_betaprim": cn_betadot,
        })

    log.info("--- Finished computing beta-dot-derivatives ---")

    df_beta = DataFrame(beta_data)
    df_beta["x_ref"], df_beta["y_ref"], df_beta["z_ref"] = x_hinge, y_hinge, z_hinge
    df_beta.to_csv(self.dynamic_stability_dir / BETA_CSV_NAME, index=False)

    return add_beta_db_values(
        self, df_beta, in_db_list, x_hinge, y_hinge, z_hinge
    )


def add_alpha_db_values(
    self,
    df: DataFrame,
    in_db_list: list[tuple[float, float, float, float]],
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> DataFrame:
    alpha_datas = []
    alpha_columns = [
        "alt", "mach", "aoa", "aos",
        "x_ref", "y_ref", "z_ref",
        "cm_alphaprim", "cz_alphaprim", "cx_alphaprim",
    ]
    tol = 1e-4
    db = CeasiompyDb()
    for alt, mach, aoa, aos in in_db_list:
        alpha_data = db.get_data(
            table_name="alpha_derivatives",
            columns=alpha_columns,
            db_close=False,
            filters=[
                f"alt = {alt}",
                f"mach = {mach}",
                f"aoa = {aoa}",
                f"aos = {aos}",
                f"aircraft = '{self.aircraft_name}'",
                "method = 'DLM'",
                f"chord = {self.nchordwise}",
                f"span = {self.nspanwise}",
                f"x_ref BETWEEN {x_hinge - tol} AND {x_hinge + tol}",
                f"y_ref BETWEEN {y_hinge - tol} AND {y_hinge + tol}",
                f"z_ref BETWEEN {z_hinge - tol} AND {z_hinge + tol}",
            ],
        )
        alpha_datas.append(alpha_data)

    db_df = DataFrame(alpha_datas, columns=alpha_columns)
    df_alpha = df[alpha_columns] if not df.empty else DataFrame(columns=alpha_columns)

    if df_alpha.empty and db_df.empty:
        return DataFrame(columns=alpha_columns)
    if df_alpha.empty:
        return db_df
    if db_df.empty:
        return df_alpha

    return concat([df_alpha, db_df], ignore_index=True)


def add_beta_db_values(
    self,
    df: DataFrame,
    in_db_list: list[tuple[float, float, float, float]],
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> DataFrame:
    beta_datas = []
    beta_columns = [
        "alt", "mach", "aoa", "aos",
        "x_ref", "y_ref", "z_ref",
        "cy_betaprim", "cl_betaprim", "cn_betaprim",
    ]
    tol = 1e-4
    db = CeasiompyDb()
    for alt, mach, aoa, aos in in_db_list:
        beta_data = db.get_data(
            table_name="beta_derivatives",
            columns=beta_columns,
            db_close=True,
            filters=[
                f"alt = {alt}",
                f"mach = {mach}",
                f"aoa = {aoa}",
                f"aos = {aos}",
                f"aircraft = '{self.aircraft_name}'",
                "method = 'DLM'",
                f"chord = {self.nchordwise}",
                f"span = {self.nspanwise}",
                f"x_ref BETWEEN {x_hinge - tol} AND {x_hinge + tol}",
                f"y_ref BETWEEN {y_hinge - tol} AND {y_hinge + tol}",
                f"z_ref BETWEEN {z_hinge - tol} AND {z_hinge + tol}",
            ],
        )
        beta_datas.append(beta_data)

    db_df = DataFrame(beta_datas, columns=beta_columns)
    df_beta = df[beta_columns] if not df.empty else DataFrame(columns=beta_columns)

    if df_beta.empty and db_df.empty:
        return DataFrame(columns=beta_columns)
    if df_beta.empty:
        return db_df
    if db_df.empty:
        return df_beta

    return concat([df_beta, db_df], ignore_index=True)


def compute_alpha_dot_derivatives(
    self,
    alt: float,
    mach: float,
    aoa: float,
    aerogrid: dict,
    k_alpha_model: float,
    t: float,
    alpha_0: float,
    x_hinge: float,
    y_hinge: float,
    z_hinge: float,
) -> tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]:
    atm = Atmosphere(h=alt)

    # Velocity [m/s] in atmospheric environment (V_inf)
    velocity = atm.speed_of_sound[0] * mach
    q_dyn = get_dynamic_pressure(atm, velocity)

    you_want_to_compute_steady_distributions = False
    if you_want_to_compute_steady_distributions:
        log.info("--- Computing steady contributions ---")
        Qjj, _ = VLM.calc_Qjj(aerogrid=copy.deepcopy(aerogrid), Ma=mach)
        aoa_rad = math.radians(aoa)
        w_j = np.ones(aerogrid['n']) * np.sin(aoa_rad)
        c_p = Qjj.dot(w_j)
        f_xyz = - q_dyn * aerogrid['N'].T * aerogrid['A'] * c_p
        qs = q_dyn * self.s
        forces = f_xyz.sum(axis=1) / qs
        log.info(f'{forces=}')

    log.info(f"--- Computing AIC Matrix for {alt=} {mach=} ---")

    # AIC Matrix np.identity(model.aerogrid['n'])
    q_alpha_jj = DLM.calc_Qjj(copy.deepcopy(aerogrid), Ma=mach, k=k_alpha_model)
    # Ajj_DLM = DLM.calc_Ajj(aerogrid=copy.deepcopy(aerogrid), Ma=mach, k=k_alpha_model)
    # q_alpha_jj = -np.linalg.inv(Ajj_DLM)
    log.info(f"Finished computing alpha-dot derivatives for {alt=} {mach=}.")

    # Get angular frequency w
    omegaalpha = k_alpha_model * velocity  # = 2 pi frequency

    # Should stay at 0
    aoa_rad = math.radians(aoa)

    # Get forces on each panels at angle alpha(t)
    alphaforces = compute_alpha_panel_forces(
        aerogrid,
        q_alpha_jj,
        omegaalpha,
        q_dyn,
        t,
        alpha_0,
        aoa=aoa_rad,
    )

    # Complex decomposition
    alphaforces_real, alphaforces_imag = complex_decomposition(alphaforces)

    # Total force, sum on each panels (3, )
    falpha = alphaforces.sum(axis=1)

    # Complex decomposition
    falpha_real, falpha_imag = complex_decomposition(falpha)

    ############################################################
    # Get derivatives at (angle, angle_dot) = (alpha, 0)
    ############################################################

    fx_alpha, fy_alpha, fz_alpha = access_angle_derivatives(
        falpha_real, falpha_imag, omegaalpha, t, alpha_0
    )

    m_alpha = compute_moments(
        aerogrid=aerogrid,
        forces=access_angle_derivatives_np(
            alphaforces_real, alphaforces_imag, omegaalpha, t, alpha_0
        ),
        x_hinge=x_hinge, y_hinge=y_hinge, z_hinge=z_hinge,
    )

    ############################################################
    # Get dot derivatives at (angle, angle_dot) = (alpha, 0)
    ############################################################

    fx_alphadot, _, fz_alphadot = access_angle_dot_derivatives(
        falpha_real, falpha_imag, omegaalpha, t, alpha_0
    )

    m_alphadot = compute_moments(
        aerogrid=aerogrid,
        forces=access_angle_dot_derivatives_np(
            alphaforces_real, alphaforces_imag, omegaalpha, t, alpha_0
        ),
        x_hinge=x_hinge, y_hinge=y_hinge, z_hinge=z_hinge,
    )

    log.info(
        f"Scaling using dyn pres={q_dyn}, surface={self.s}, chord={self.c}, span={self.b}."
    )

    return scale_alpha_coefficients(
        self,
        q_dyn,
        fx_alpha, fy_alpha, fz_alpha,
        m_alpha[0], m_alpha[1], m_alpha[2],
        m_alphadot[1], fz_alphadot, fx_alphadot,
    )


def compute_beta_dot_derivatives(
    self,
    alt: float,
    mach: float,
    aoa: float,
    aos: float,
    aerogrid,
    k_beta_model,
    t,
    beta_0,
    x_hinge,
    y_hinge,
    z_hinge,
) -> tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]:
    atm = Atmosphere(h=alt)

    # Velocity [m/s] in atmospheric environment (V_inf)
    velocity = atm.speed_of_sound[0] * mach
    q_dyn = get_dynamic_pressure(atm, velocity)

    log.info(f"--- Computing AIC Matrix for {alt=} {mach=} {aoa=} {aos=} ---")

    # Convert to radiams
    aoa_rad, aos_rad = math.radians(aoa), math.radians(aos)

    # AIC Matrix np.identity(model.aerogrid['n'])
    q_beta_jj = DLM.calc_Qjj(aerogrid, Ma=mach, k=k_beta_model)

    # Get angular frequencies
    omegabeta = k_beta_model * velocity

    # Get forces on each panels at angle beta(t)
    betaforces = compute_beta_panel_forces(
        aerogrid,
        q_beta_jj,
        omegabeta,
        q_dyn,
        t,
        beta_0,
        aoa_rad,
        aos_rad,
    )

    # Complex decomposition
    betaforces_real, betaforces_imag = complex_decomposition(betaforces)

    # Total force, sum on each panels (3, )
    fbeta = betaforces.sum(axis=1)

    # Complex decomposition
    fbeta_real, fbeta_imag = complex_decomposition(fbeta)

    ############################################################
    # Get derivatives at (angle, angle_dot) = (beta, 0)
    ############################################################

    fx_beta, fy_beta, fz_beta = access_angle_derivatives(
        fbeta_real, fbeta_imag, omegabeta, t, beta_0
    )

    m_beta = compute_moments(
        aerogrid=aerogrid,
        forces=access_angle_derivatives_np(
            betaforces_real, betaforces_imag, omegabeta, t, beta_0
        ),
        x_hinge=x_hinge, y_hinge=y_hinge, z_hinge=z_hinge,
    )

    ############################################################
    # Get dot derivatives at (angle, angle_dot) = (beta, 0)
    ############################################################

    _, fy_betadot, _ = access_angle_dot_derivatives(
        fbeta_real, fbeta_imag, omegabeta, t, beta_0
    )

    m_betadot = compute_moments(
        aerogrid=aerogrid,
        forces=access_angle_dot_derivatives_np(
            betaforces_real, betaforces_imag, omegabeta, t, beta_0
        ),
        x_hinge=x_hinge, y_hinge=y_hinge, z_hinge=z_hinge,
    )

    log.info(
        f"Scaling using dyn pres={q_dyn}, surface={self.s}, chord={self.c}, span={self.b}."
    )

    return scale_beta_coefficients(
        self,
        q_dyn,
        fx_beta, fy_beta, fz_beta,
        m_beta[0], m_beta[1], m_beta[2],
        fy_betadot, m_betadot[0], m_betadot[2],
    )


def get_dynamic_pressure(atm: Atmosphere, velocity: float) -> float:
    return atm.density[0] * (velocity**2) / 2.0
