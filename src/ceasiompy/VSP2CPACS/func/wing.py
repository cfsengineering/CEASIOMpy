"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOMpy.
The geometry is built in OpenVSP, saved as a .vsp3 file, and then selected in the GUI.
It is subsequently processed by this module to generate a CPACS file.

| Author: Nicolo' Perasso
| Creation: 23/12/2025
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import openvsp as vsp

from math import comb

from scipy.interpolate import interp1d

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def Import_Wing(wing):

    # Some initializations
    Sections_information, Section_information = {}, {}
    n_section_idx = 0
    Twist_stored = [0]

    # ---- Trasforming information ----
    # Inside Extract_transformation there are the global informations that characterize the
    # component.
    Sections_information['Transformation'] = Extract_transformation(wing)
    Sections_information['Transformation']['idx_engine'] = None

    # ---- section informations ----
    # Save the parameters to define sections

    # Create a nested dictionary where
    # for every section there are specific keys to import the parameters
    Output_inf = [
        "Alias",
        "Dihedral_angle",
        "Sweep_angle",
        "Sweep_loc",
        "Twist",
        "Twist_loc",
        "Span",
    ]

    # Number of sections
    xsec_surf_id = vsp.GetXSecSurf(wing, 0)
    num_xsecs = vsp.GetNumXSec(xsec_surf_id)

    for i in range(num_xsecs):
        xsec_id = vsp.GetXSec(xsec_surf_id,i)
        if i != 0:
            # ---- from section 1 to tip's section ----#
            Section_VSP = Wing_Sections(wing,i)
            Section_information = dict(zip(Output_inf, Section_VSP))
            # ---- profile ---- #
            coord, Name, Scaling, shift = get_profile_section(
                wing,
                xsec_id,
                i,
                Section_information["Twist"],
                Section_information["Twist_loc"],
                Sections_information["Transformation"]["Relative_Twist"],
                Twist_stored,
            )
            Section_information['Airfoil'] = Name
            Section_information['Airfoil_coordinates'] = coord

            Sections_information[f'Section{n_section_idx}'] = Section_information

        else:

            # ---- takes the root section == section0
            # The root section is defined to have zero incidence; change it later if required.
            coordRoot, Name, Scaling, shift = get_profile_section(
                wing,
                xsec_id,
                i,
                Twist_val=0,
                Twist_loc=0,
                Rel=Sections_information["Transformation"]["Relative_Twist"],
                Twist_list=Twist_stored,
            )
            Sections_information[f'Section{n_section_idx}'] = {
                'Airfoil': Name,
                'Airfoil_coordinates': coordRoot,
            }
            Sections_information[f'Section{n_section_idx}']['Sweep_loc'] = 0

        # Scaling is defined by width and height (or chord) used to scale the normalized profile.
        if len(Scaling) == 2:
            Sections_information[f'Section{n_section_idx}']['x_scal'] = Scaling[0]
            Sections_information[f'Section{n_section_idx}']['y_scal'] = 1
            Sections_information[f'Section{n_section_idx}']['z_scal'] = Scaling[1]
        else:
            Sections_information[f'Section{n_section_idx}']['x_scal'] = Scaling[0]
            Sections_information[f'Section{n_section_idx}']['y_scal'] = 1
            Sections_information[f'Section{n_section_idx}']['z_scal'] = Scaling[0]

        # There is a shift to do if it is set EDIT CURVE, because OpenVSP doesn't set the
        # coordinate system on the LE; when the user changes the LE control point position,
        # a translation is necessary to obtain the same geometry.
        if shift is not None:
            Sections_information[f"Section{n_section_idx}"]["x_trasl"] = (
                (0.5 - np.abs(shift)) * Scaling[0]
            )
        else:
            Sections_information[f'Section{n_section_idx}']['x_trasl'] = 0

        # Compute translation to account for sweep location (shift from sweep_loc to LE)
        if Sections_information[f'Section{n_section_idx}']['Sweep_loc'] != 0:
            sweep_loc = Sections_information[f"Section{n_section_idx}"]["Sweep_loc"]
            chord_root = Sections_information[f"Section{n_section_idx - 1}"]["x_scal"]
            chord_tip = Sections_information[f"Section{n_section_idx}"]["x_scal"]
            dc_dy = (
                chord_tip - chord_root
            ) / Sections_information[f"Section{n_section_idx}"]["Span"]
            angle = Sections_information[f"Section{n_section_idx}"]["Sweep_angle"]
            Sections_information[f"Section{n_section_idx}"]["Sweep_angle"] = np.degrees(
                np.arctan(np.tan(np.radians(angle)) - sweep_loc * dc_dy)
            )

        # next section
        n_section_idx += 1

    return Sections_information


def get_params_by_name(xsec_id,label):
    # set a parameter athat you want and it will give you the value inside the vsp3 file
    result = {}
    for pid in vsp.GetXSecParmIDs(xsec_id):
        if not vsp.ValidParm(pid):
            continue
        name = vsp.GetParmName(pid)
        if name in label:
            result[name] = vsp.GetParmVal(pid)
    return result


def get_coord_naca5(xsec_id,n):

    """
    Compute coordinates of a NACA 5-series airfoil.

    Uses the section parameters (IdealCl, CamberLoc, ThickChord, Invert, Chord)
    to build the corresponding 5-digit NACA profile. The function:
    - derives the NACA name,
    - computes camber line and thickness,
    - constructs upper and lower surfaces,
    - optionally inverts the airfoil and applies chord scaling.

    Returns (x, y, Name, Scaling, None).
    """
    geom_parm = get_params_by_name(xsec_id, ['CamberLoc','ThickChord','IdealCl','Invert','Chord'])
    ideal_cl = geom_parm['IdealCl']
    p = geom_parm['CamberLoc']
    t = geom_parm['ThickChord']
    Invert_airfoil = geom_parm['Invert']
    XX = int(np.ceil(t * 100))
    n1, n2 = XX // 10, XX % 10

    # bug in openVSP, the five digit name is not correct !
    p1 = int(p / 0.05)
    Name = [int(round(ideal_cl / 0.15)), p1, 0, n1, n2]
    Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}{Name[4]}'

    theta = np.linspace(0, np.pi, n // 2)
    x_line = 0.5 * (1 - np.cos(theta))

    # thickness distribution
    y_t = (
        t / 0.2 * (
            0.2969 * x_line**0.5
            - 0.1260 * x_line
            - 0.3516 * x_line**2
            + 0.2843 * x_line**3
            - 0.1036 * x_line**4
        )
    )

    # mean data for the profiles 210–250
    p_values = np.array([0.05, 0.10, 0.15, 0.20, 0.25])
    m_values = np.array([0.0580, 0.1260, 0.2025, 0.2900, 0.3910])
    k1_values = np.array([361.400, 51.640, 15.957, 6.643, 3.230])

    # interpolation
    m = np.interp(p, p_values, m_values)
    k1 = np.interp(p, p_values, k1_values)

    # k1 scale
    Cl_ref = 0.3  # riferimento NACA
    k1 = k1 * (ideal_cl / Cl_ref)

    # split between front and back
    x_line_front = x_line[x_line < m]
    x_line_back = x_line[x_line >= m]

    # === Camber line (continuity fixed) ===
    # front (x < m)
    y_c_front = (k1 / 6) * (
        x_line_front**3 - 3 * m * x_line_front**2 + m**2 * (3 - m) * x_line_front
    )
    dyc_dx_front = (k1 / 6) * (
        3 * x_line_front**2 - 6 * m * x_line_front + m**2 * (3 - m)
    )

    # back (x >= m)
    y_c_back = (k1 * m**3 / 6) * (1 - x_line_back)

    # === CORRECT CONTINUITY FIX ===
    delta_y = y_c_front[-1] - y_c_back[0]
    y_c_back = y_c_back + delta_y

    dyc_dx_back = np.full_like(x_line_back, -k1 * m**3 / 6)

    # attach the two segment
    y_c = np.concatenate((y_c_front, y_c_back))
    dyc_dx = np.concatenate((dyc_dx_front, dyc_dx_back))

    theta = np.arctan(dyc_dx)

    # upper and lower surface
    x_u = x_line - y_t * np.sin(theta)
    y_u = y_c + y_t * np.cos(theta)
    x_l = x_line + y_t * np.sin(theta)
    y_l = y_c - y_t * np.cos(theta)

    x = np.concatenate((x_l[::-1], x_u), axis=0)
    y = np.concatenate((y_l[::-1], y_u), axis=0)
    x[-1] = x[0]
    y[-1] = y[0]

    # Invert the airfoil if required
    if Invert_airfoil:
        y = -y

    Scaling = [geom_parm['Chord']]

    return x, y, Name, Scaling, None


def get_coord_naca4(xsec_id,n):
    """
    Compute coordinates of a NACA 4-series airfoil.

    Uses the section parameters (Camber, CamberLoc, ThickChord, Invert, Chord)
    to build the corresponding 4-digit NACA profile. The function:
    - derives the NACA name,
    - computes camber line and thickness,
    - constructs upper and lower surfaces,
    - optionally inverts the airfoil and applies chord scaling.

    Returns (x, y, Name, Scaling, None).
    """

    geom_parm = get_params_by_name(xsec_id,['Camber','CamberLoc','ThickChord','Invert','Chord'])
    m = geom_parm['Camber']
    p = geom_parm['CamberLoc'] if m != 0 else 0
    t = geom_parm['ThickChord']

    theta = np.linspace(0, np.pi, n // 2)
    x_line = 0.5 * (1 - np.cos(theta))

    # thickness line
    y_t = (
        t
        / 0.2
        * (
            0.2969 * x_line**0.5
            - 0.126 * x_line
            - 0.3516 * x_line**2
            + 0.2843 * x_line**3
            + -0.1036 * x_line**4
        )
    )

    # cambered airfoil:
    if p != 0:
        XX = np.ceil(t * 100)
        n1,n2 = divmod(int(XX), 10)
        Name = [int(round(m * 100)), int(round(p * 10)), n1, n2]
        Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}'
        # camber line front of the airfoil (befor p)
        x_line_front = x_line[x_line < p]

        # camber line back of the airfoil (after p)
        x_line_back = x_line[x_line >= p]

        # total camber line
        y_c = np.concatenate(
            (
                (m / p**2) * (2 * p * x_line_front - x_line_front**2),
                (m / (1 - p) ** 2)
                * (1 - 2 * p + 2 * p * x_line_back - x_line_back**2),
            ),
            axis=0,
        )
        dyc_dx = np.concatenate(
            (
                (2 * m / p**2) * (p - x_line_front),
                (2 * m / (1 - p) ** 2) * (p - x_line_back),
            ),
            axis=0,
        )

        theta = np.arctan(dyc_dx)

        # upper and lower surface
        x_u = x_line - y_t * np.sin(theta)
        y_u = y_c + y_t * np.cos(theta)
        x_l = x_line + y_t * np.sin(theta)
        y_l = y_c - y_t * np.cos(theta)

    # uncambered airfoil:
    else:
        XX = np.ceil(t * 10)
        n1,n2 = divmod(int(XX), 10)
        Name = [int(round(m * 100)), int(round(p * 10)), n1, n2]
        Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}'
        y_c = 0 * x_line
        dyc_dx = y_c

        # upper and lower surface
        x_u = x_line
        y_u = y_t
        x_l = x_line
        y_l = -y_t

    # concatenate the upper and lower
    x = np.concatenate((x_l[::-1],x_u), axis=0)
    y = np.concatenate((y_l[::-1], y_u), axis=0)
    x[-1] = x[0]
    y[-1] = y[0]

    Scaling = [geom_parm['Chord']]

    return x, y, Name, Scaling, None


def get_coord_naca4_mod(xsec_id, n):
    """
    Compute coordinates of a modified NACA 4-series airfoil.

    Uses section parameters (Camber, CamberLoc, ThickChord, ThickLoc, LERadIndx,
    Invert, Chord) to generate a 4-digit NACA profile with custom leading-edge
    radius and thickness distribution. Polynomial coefficients for the thickness
    are interpolated from a predefined database and applied separately before and
    after the max-thickness location. Camber, upper and lower surfaces are built
    using standard 4-series definitions, with optional inversion.

    Returns (x, y, Name, Scaling, None).
    """

    geom_parm = get_params_by_name(
        xsec_id,
        ['Camber','CamberLoc','ThickChord','ThickLoc','LERadIndx','Invert','Chord']
    )
    m = geom_parm['Camber']
    p = geom_parm['CamberLoc']
    t = geom_parm['ThickChord']
    thick_loc = geom_parm['ThickLoc']
    Invert_airfoil = geom_parm['Invert']

    mods_value = int(
        f"{int(round(geom_parm['LERadIndx']))}{int(round(geom_parm['ThickLoc'] * 10))}"
    )

    airfoils = ["0020-03", "0020-05", "0020-34", "0020-35", "0020-62",
                "0020-63", "0020-64", "0020-65", "0020-66", "0020-93"]

    a0 = np.array([0.148450, 0.000000, 0.148450, 0.148450, 0.296900,
                   0.296900, 0.296900, 0.296900, 0.296900, 0.514246])
    a1 = np.array([0.412103, 0.477000, 0.193233, 0.083362, 0.213337,
                   -0.096082, -0.246867, -0.310275, -0.271180, -0.840115])
    a2 = np.array([-1.672610, -0.708000, -0.558166, -0.183150, -2.931954,
                   -0.543310, 0.175384, 0.341700, 0.140200, 1.110100])
    a3 = np.array([1.688690, 0.308000, 0.283208, -0.006910, 5.229170,
                   0.559395, -0.266917, -0.321820, -0.082137, -1.094010])
    d0 = np.array([0.002000] * 10)
    d1 = np.array([0.234000, 0.465000, 0.315000, 0.465000, 0.200000,
                   0.234000, 0.315000, 0.465000, 0.700000, 0.234000])
    d2 = np.array([-0.068571, -0.684000, -0.233333, -0.684000, -0.040625,
                   -0.068571, -0.233333, -0.684000, -1.662500, -0.068571])
    d3 = np.array([-0.093878, 0.292000, -0.032407, 0.292000, -0.070312,
                   -0.093878, -0.032407, 0.292000, 1.312500, -0.093878])

    mods = np.array([int(a.split('-')[-1]) for a in airfoils])
    coeffs = {}
    for name, arr in zip(['a0','a1','a2','a3','d0','d1','d2','d3'],
                         [a0,a1,a2,a3,d0,d1,d2,d3]):
        coeffs[name] = np.interp(mods_value, mods, arr)

    # Coordinate generation
    theta = np.linspace(0, np.pi, n // 2)
    x_line = 0.5 * (1 - np.cos(theta))

    # Thickness distribution (corrected)
    y_t = np.zeros_like(x_line)
    for i, x in enumerate(x_line):
        if x <= thick_loc:
            y_t[i] = (
                coeffs['a0'] * np.sqrt(x)
                + coeffs['a1'] * x
                + coeffs['a2'] * x**2
                + coeffs['a3'] * x**3
            )
        else:
            x1 = 1 - x
            y_t[i] = coeffs['d0'] + coeffs['d1'] * x1 + coeffs['d2'] * x1**2 + coeffs['d3'] * x1**3

    # Camber line and upper/lower surface
    if p != 0:
        XX = np.ceil(t * 100)
        n1,n2 = divmod(int(XX),10)
        Name = [int(round(m * 100)), int(round(p * 10)), n1, n2]
        Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}-{mods_value}'

        x_line_front = x_line[x_line < p]
        x_line_back = x_line[x_line >= p]
        y_c = np.concatenate([
            (m / p**2) * (2 * p * x_line_front - x_line_front**2),
            (m / (1 - p)**2) * (1 - 2 * p + 2 * p * x_line_back - x_line_back**2)
        ])
        dyc_dx = np.concatenate([
            (2 * m / p**2) * (p - x_line_front),
            (2 * m / (1 - p)**2) * (p - x_line_back)
        ])
        theta_camber = np.arctan(dyc_dx)
        x_u = x_line - y_t * np.sin(theta_camber)
        y_u = y_c + y_t * np.cos(theta_camber)
        x_l = x_line + y_t * np.sin(theta_camber)
        y_l = y_c - y_t * np.cos(theta_camber)
    else:
        XX = np.ceil(t * 100)
        n1,n2 = divmod(int(XX),10)
        Name = [int(round(m * 100)), 0, n1, n2]
        Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}-{mods_value}'
        x_u = x_line
        y_u = y_t
        x_l = x_line
        y_l = -y_t

    x = np.concatenate((x_l[::-1], x_u))
    y = np.concatenate((y_l[::-1], y_u))
    y *= t / 0.2  # scale thickness

    if Invert_airfoil:
        y = -y

    # close profile
    x[-1] = x[0]
    y[-1] = y[0]

    Scaling = [geom_parm['Chord']]
    return x, y, Name, Scaling, None


def get_coord_naca5_mod(xsec_id, n):
    """
    Compute coordinates of a modified NACA 5-series airfoil.

    Uses section parameters (IdealCl, CamberLoc, ThickChord, ThickLoc, LERadIndx,
    Invert, Chord) to generate a 5-digit NACA profile with custom leading-edge
    radius and thickness distribution. Polynomial coefficients for the thickness
    are interpolated from a predefined database and applied separately before and
    after the max-thickness location. Camber, upper and lower surfaces are built
    using standard 5-series definitions, with optional inversion.

    Returns (x, y, Name, Scaling, None).
    """

    # --- retrieve geometry params (user function) ---
    geom_parm = get_params_by_name(
        xsec_id,
        ['CamberLoc','ThickChord','IdealCl','ThickLoc','LERadIndx','Chord']
    )

    # user inputs
    ideal_cl = geom_parm['IdealCl']
    p = geom_parm['CamberLoc']
    t = geom_parm['ThickChord']
    thick_loc = geom_parm['ThickLoc']
    mods_value = int(
        f"{int(round(geom_parm['LERadIndx']))}{int(round(geom_parm['ThickLoc'] * 10))}"
    )

    # -----------------------------------------------------------
    # coefficients for thickness distribution (same as 4-digit mod)
    airfoils = ["0020-03", "0020-05", "0020-34", "0020-35", "0020-62",
                "0020-63", "0020-64", "0020-65", "0020-66", "0020-93"]

    a0 = np.array([0.148450, 0.000000, 0.148450, 0.148450, 0.296900,
                   0.296900, 0.296900, 0.296900, 0.296900, 0.514246])
    a1 = np.array([0.412103, 0.477000, 0.193233, 0.083362, 0.213337,
                   -0.096082, -0.246867, -0.310275, -0.271180, -0.840115])
    a2 = np.array([-1.672610, -0.708000, -0.558166, -0.183150, -2.931954,
                   -0.543310, 0.175384, 0.341700, 0.140200, 1.110100])
    a3 = np.array([1.688690, 0.308000, 0.283208, -0.006910, 5.229170,
                   0.559395, -0.266917, -0.321820, -0.082137, -1.094010])
    d0 = np.array([0.002000] * 10)
    d1 = np.array([0.234000, 0.465000, 0.315000, 0.465000, 0.200000,
                   0.234000, 0.315000, 0.465000, 0.700000, 0.234000])
    d2 = np.array([-0.068571, -0.684000, -0.233333, -0.684000, -0.040625,
                   -0.068571, -0.233333, -0.684000, -1.662500, -0.068571])
    d3 = np.array([-0.093878, 0.292000, -0.032407, 0.292000, -0.070312,
                   -0.093878, -0.032407, 0.292000, 1.312500, -0.093878])

    mods = np.array([int(a.split('-')[-1]) for a in airfoils])
    coeffs = {}
    for name, arr in zip(['a0','a1','a2','a3','d0','d1','d2','d3'],
                         [a0,a1,a2,a3,d0,d1,d2,d3]):
        coeffs[name] = np.interp(mods_value, mods, arr)

    # Build name
    XX = np.ceil(t * 100)
    n1,n2 = divmod(int(XX),10)

    # bug in openVSP, the five digit name is not correct !
    p1 = int(p / 0.05)
    Name = [int(round(ideal_cl / 0.15)), p1, 0, n1, n2]
    Name = f'NACA{Name[0]}{Name[1]}{Name[2]}{Name[3]}{Name[4]}-{mods_value}'

    # Thickness distribution
    theta = np.linspace(0, np.pi, n // 2)
    x_line = 0.5 * (1 - np.cos(theta))
    y_t = np.zeros_like(x_line)
    for i, x in enumerate(x_line):
        if x <= thick_loc:
            y_t[i] = (
                coeffs['a0'] * np.sqrt(x)
                + coeffs['a1'] * x
                + coeffs['a2'] * x**2
                + coeffs['a3'] * x**3
            )
        else:
            x1 = 1 - x
            y_t[i] = coeffs['d0'] + coeffs['d1'] * x1 + coeffs['d2'] * x1**2 + coeffs['d3'] * x1**3

    # Mean camber line (NACA 5-digit standard form)
    p_values = np.array([0.05, 0.10, 0.15, 0.20, 0.25])
    m_values = np.array([0.0580, 0.1260, 0.2025, 0.2900, 0.3910])
    k1_values = np.array([361.400, 51.640, 15.957, 6.643, 3.230])
    m = np.interp(p, p_values, m_values)
    k1 = np.interp(p, p_values, k1_values)
    Cl_ref = 0.3
    k1 *= (ideal_cl / Cl_ref)

    # Camber line equations (correct continuity)
    x_front = x_line[x_line < m]
    x_back = x_line[x_line >= m]
    y_c_front = (k1 / 6) * (x_front**3 - 3 * m * x_front**2 + m**2 * (3 - m) * x_front)
    y_c_back = (k1 * m**3 / 6) * (1 - x_back)
    dyc_dx_front = (k1 / 6) * (3 * x_front**2 - 6 * m * x_front + m**2 * (3 - m))
    dyc_dx_back = -(k1 * m**3 / 6) * np.ones_like(x_back)

    # join
    y_c = np.concatenate((y_c_front, y_c_back))
    dyc_dx = np.concatenate((dyc_dx_front, dyc_dx_back))
    theta_camber = np.arctan(dyc_dx)

    # Surface coordinates
    x_u = x_line - y_t * np.sin(theta_camber)
    y_u = y_c + y_t * np.cos(theta_camber)
    x_l = x_line + y_t * np.sin(theta_camber)
    y_l = y_c - y_t * np.cos(theta_camber)

    x = np.concatenate((x_l[::-1], x_u[1:]))
    y = np.concatenate((y_l[::-1], y_u[1:]))

    Scaling = geom_parm['Chord']

    return x, y, Name, Scaling, None


def get_coord_ellipse(xsec_id,n):
    """
    Generate coordinates for an elliptical airfoil-like profile.

    Builds a closed 2D ellipse from the input section parameters
    (Ellipse_Width, Ellipse_Height).
    """

    Name = 'Ellipse'
    geom_parm = get_params_by_name(xsec_id,['Ellipse_Height', 'Ellipse_Width'])
    a = 1
    b = 1

    theta = np.linspace(0, np.pi, n // 2)
    x = (a / 2) * np.cos(theta)
    y = (b / 2) * np.sin(theta)

    x_full = np.concatenate((x, -x), axis=0)
    y_full = np.concatenate((-y, y), axis=0)

    # close profile
    y_full[0] = y_full[-1]
    x_full[0] = x_full[-1]

    # shift
    idx_min = np.argmin(x_full)

    x_full = x_full - x_full[idx_min]
    y_full = y_full - y_full[idx_min]
    Scaling = [geom_parm['Ellipse_Width'],geom_parm['Ellipse_Height']]

    return x_full, y_full, Name, Scaling, None


def get_coord_superellipse(xsec_id):
    """
    Generate coordinates for an super-elliptical airfoil-like profile.

    """
    core_frac = 0.7
    n = 120
    Name = 'SuperEllipse'

    geom_parm = get_params_by_name(
        xsec_id,
        [
            'Super_Height', 'Super_Width', 'Super_N', 'Super_M',
            'Super_N_bot', 'Super_M_bot', 'Super_MaxWidthLoc',
        ])

    a = 1
    b = 1
    N_up = geom_parm['Super_N']
    N_low = geom_parm['Super_M']
    M_up = geom_parm['Super_N_bot']
    M_low = geom_parm['Super_M_bot']
    MacWLoc = geom_parm['Super_MaxWidthLoc']

    # --- Top half ---
    theta_up = np.linspace(0, np.pi / 2, int(n / 4))
    y_up = (a / 2) * np.abs(np.cos(theta_up))**(2 / N_up)
    x_up = (b / 2) * np.abs(np.sin(theta_up))**(2 / M_up)

    # --- Bottom half ---
    theta_low = np.linspace(0, np.pi / 2, int(n / 4))
    y_low = (a / 2) * np.abs(np.cos(theta_low))**(2 / N_low)
    x_low = (b / 2) * np.abs(np.sin(theta_low))**(2 / M_low)

    x_core = core_frac * (b / 2)

    def weight(x):
        # 0 in the center, 1 close to ±b/2
        w = np.zeros_like(x)
        mask = np.abs(x) > x_core
        s = (np.abs(x[mask]) - x_core) / ((b / 2) - x_core)
        w[mask] = 0.5 * (1 - np.cos(np.pi * s))
        return w

    w_up = weight(x_up)

    # --- vertical deformation (MacWLoc) ---
    y_up_stretched = y_up + MacWLoc * w_up
    y_low_stretched = y_low

    # --- close profile ---
    y_full = np.concatenate((-y_low_stretched[::-1], -y_low_stretched,
                             y_up_stretched[::-1], y_up_stretched))
    x_full = np.concatenate((x_low[::-1], -x_low, -x_up[::-1], x_up))

    # --- Shift  ---
    idx_min = np.argmin(x_full)
    x_full = x_full - x_full[idx_min]
    y_full = y_full - y_full[idx_min]
    Scaling = [geom_parm['Super_Width'], geom_parm['Super_Height']]
    return x_full, y_full, Name, Scaling, None


def get_coord_point(_):
    """
    Generate coordinates for point.
    It will be a circle with a scaling = 0
    d: diameter
    n: number of points
    """

    Name = 'Point'

    d = 1
    n = 40
    theta = np.linspace(0, np.pi, int(n / 2))
    x = d / 2 * np.cos(theta)
    y = d / 2 * np.sin(theta)
    x_full = np.concatenate((x, -x), axis=0)
    y_full = np.concatenate((-y, y), axis=0)

    # close profile
    y_full[0] = y_full[-1]
    x_full[0] = x_full[-1]

    # shift
    idx_min = np.argmin(x_full)
    x_full = x_full - x_full[idx_min]
    y_full = y_full - y_full[idx_min]

    Scaling = [1]
    return x_full,y_full, Name, Scaling, None


def get_coord_circle(xsec_id, n):
    """
    Generate coordinates for a cicle airfoil-like profile.
    d: diameter
    """
    Name = 'Circle'

    geom_parm = get_params_by_name(xsec_id,['Circle_Diameter'])
    d = 1
    theta = np.linspace(0, np.pi, int(n / 2))
    x = d / 2 * np.cos(theta)
    y = d / 2 * np.sin(theta)
    x_full = np.concatenate((x, -x), axis=0)
    y_full = np.concatenate((-y, y), axis=0)

    # close profile
    y_full[0] = y_full[-1]
    x_full[0] = x_full[-1]

    # shift
    idx_min = np.argmin(x_full)
    x_full = x_full - x_full[idx_min]
    y_full = y_full - y_full[idx_min]

    # Scaling
    Scaling = [geom_parm['Circle_Diameter']]
    return x_full, y_full, Name, Scaling, None


def get_coord_roundedrectangle(xsec_id, n):
    """
    Generate coordinates for a rounded-rectangle airfoil profile.

    Uses section parameters (width, height, skew, vertical skew, keystone taper,
    and individual corner radii) to build a closed shape with straight sides and
    Bezier-blended rounded corners.
    """

    Name = 'RoundedRectangle'

    geom_parm = get_params_by_name(xsec_id, [
        'RoundedRect_Height','RoundedRect_Width',
        'RoundRect_Skew','RoundRect_VSkew','RoundRect_Keystone',
        'RoundRectXSec_Radius','RoundRectXSec_RadiusBL',
        'RoundRectXSec_RadiusBR','RoundRectXSec_RadiusTL'
    ])

    w = 1
    h = 1
    skew = geom_parm['RoundRect_Skew']
    VSskew = geom_parm['RoundRect_VSkew']
    keystone = geom_parm['RoundRect_Keystone']
    TR_Radius = geom_parm['RoundRectXSec_Radius']
    TL_Radius = geom_parm['RoundRectXSec_RadiusTL']
    BR_Radius = geom_parm['RoundRectXSec_RadiusBR']
    BL_Radius = geom_parm['RoundRectXSec_RadiusBL']

    # --- Vertices ---
    bl = np.array([0 - skew / 2 - VSskew + (keystone - 0.5) * h / 2, 0])
    br = np.array([w - skew / 2, VSskew - (keystone - 0.5) * h / 2])
    tr = np.array([w + skew, h + VSskew + (keystone - 0.5) * h / 2])
    tl = np.array([0 + skew, h - VSskew - (keystone - 0.5) * h / 2])
    verts = [bl, br, tr, tl]
    radii = [BL_Radius, BR_Radius, TR_Radius, TL_Radius]
    eps = 1e-9
    info = []

    for i in range(4):
        p_prev = verts[i - 1]
        p_corner = verts[i]
        p_next = verts[(i + 1) % 4]
        r = float(radii[i])

        len_in = np.linalg.norm(p_corner - p_prev)
        len_out = np.linalg.norm(p_next - p_corner)
        dir_in = (p_corner - p_prev) / (len_in if len_in != 0 else 1)
        dir_out = (p_next - p_corner) / (len_out if len_out != 0 else 1)

        cut = 0.0 if r <= eps else min(r, 0.45 * len_in, 0.45 * len_out)
        p_start = p_corner - dir_in * cut
        p_end = p_corner + dir_out * cut

        info.append({'p_corner': p_corner, 'p_start': p_start, 'p_end': p_end, 'r': r})

    # --- secondary functions ---
    def interp(a, b, m):
        t = np.linspace(0, 1, m)
        return np.array([a + (b - a) * tt for tt in t])

    def make_bezier(p_start, p_corner, p_end, m: int = 20):
        t = np.linspace(0, 1, m)
        return (
            (1 - t)[:,None]**2 * p_start
            + 2 * (1 - t)[:,None] * t[:,None] * p_corner
            + t[:,None]**2 * p_end
        )

    def clean(points):
        # no duplicates
        cleaned = [points[0]]
        for p in points[1:]:
            if np.linalg.norm(p - cleaned[-1]) > 1e-8:
                cleaned.append(p)
        return np.array(cleaned)

    m_side = max(6, int(n / 4))
    m_arc = max(10, int(n / 10))

    bottom = np.vstack([
        interp(info[0]['p_end'], info[1]['p_start'], m_side),
        make_bezier(info[1]['p_start'], info[1]['p_corner'], info[1]['p_end'], m_arc)[1:]
    ])
    right = np.vstack([
        interp(info[1]['p_end'], info[2]['p_start'], m_side),
        make_bezier(info[2]['p_start'], info[2]['p_corner'], info[2]['p_end'], m_arc)[1:]
    ])
    top = np.vstack([
        interp(info[2]['p_end'], info[3]['p_start'], m_side),
        make_bezier(info[3]['p_start'], info[3]['p_corner'], info[3]['p_end'], m_arc)[1:]
    ])
    left = np.vstack([
        interp(info[3]['p_end'], info[0]['p_start'], m_side),
        make_bezier(info[0]['p_start'], info[0]['p_corner'], info[0]['p_end'], m_arc)[1:]
    ])

    # --- Create the profile ---
    # Lower: TE  → bottom → LE
    lower = clean(np.vstack([bottom[::-1], left[::-1]]))

    # Upper: LE → top → TE
    upper = clean(np.vstack([top[::-1], right[::-1]]))
    Coord = np.vstack([lower, upper])

    if not np.allclose(Coord[0], Coord[-1]):
        Coord = np.vstack([Coord, Coord[0]])

    Coord[:,1] = Coord[:,1] - np.mean(Coord[:,1])
    Scaling = [geom_parm['RoundedRect_Width'],geom_parm['RoundedRect_Height']]

    return Coord[:,0], Coord[:,1], Name ,Scaling, None


def get_coord_from_file(xsec_id, _):
    """
    Load airfoil coordinates from an external file (OpenVSP input).
    Suggest ot import an af file from selig database.

    Reads upper and lower surface points from the selected x-section, merges them
    into a closed profile, and returns the coordinates along with the section name
    and chord scaling.
    """
    geom_parm = get_params_by_name(xsec_id,['Chord'])
    Name = vsp.GetXSecCurveAlias(xsec_id).replace(' ','_')

    # import the points
    upper_pts = np.array(vsp.GetAirfoilUpperPnts(xsec_id))
    lower_pts = np.array(vsp.GetAirfoilLowerPnts(xsec_id))
    upper_coords = np.array([[p.x(), p.y(), p.z()] for p in upper_pts])
    lower_coords = np.array([[p.x(), p.y(), p.z()] for p in lower_pts])

    x_u, y_u = upper_coords[:, 0], upper_coords[:, 1]
    x_l, y_l = lower_coords[:, 0], lower_coords[:, 1]

    x = np.concatenate((x_l[::-1], x_u), axis=0)
    y = np.concatenate((y_l[::-1], y_u), axis=0)

    # check if it close
    x[-1] = x[0]
    y[-1] = y[0]

    Scaling = [geom_parm['Chord']]
    return x, y, Name, Scaling, None


def bezier_curve(ctrl_pts, n_points, s):
    n_points_per_seg = n_points // 10

    # built the bezier curve
    def bezier4(p):
        t = np.linspace(0, 1, n_points_per_seg)
        B = np.zeros((n_points_per_seg, 2))
        for i in range(4):
            B += np.outer(comb(3, i) * (t**i) * ((1 - t)**(3 - i)), p[i, :2])
        return B

    n = len(ctrl_pts)
    curve = []

    for i in range(0, n - 1, 3):
        if i + 3 < n:
            seg = bezier4(ctrl_pts[i: i + 4])
            curve.append(seg)

    # --- Convert list of segments into a single array ---
    curve = np.vstack(curve)

    # --- Find index of LE (minimum x) ---
    le_idx = np.argmin(curve[:, 0])

    # --- Separate lower and upper surfaces ---
    # Lower: TE (x~1) -> LE (x=0), include LE, exclude duplicate TE final
    lower_surface = curve[:le_idx + 1]

    # Upper: LE -> TE final (x~1), include TE final, exclude duplicate LE
    upper_surface = curve[le_idx + 1:]

    # --- Combine surfaces without duplicating TE or LE ---
    ordered_curve = np.vstack([lower_surface, upper_surface])

    # --- Normalize chord length to 1 and save scaling ---
    x = ordered_curve[:, 0]
    y = ordered_curve[:, 1]

    # Shift so LE is at x=0
    x -= s
    x[-1] = x[0]
    y[-1] = y[0]

    return np.column_stack([x, y])


def spline_curve(ctrl_pts, n_points,s):
    """
    Reconstruct a complete cubic spline curve from control points.

    ctrl_pts: numpy array of shape (N, 2)
        Control points from OpenVSP (usually only one side of the profile)
    n_points: int
        Total number of points to generate along the spline

    Returns:
        curve: numpy array of shape (M, 2)
            Interpolated spline points forming a complete airfoil profile
    """
    alpha = 0.5  # centripetal Catmull-Rom parameter

    # --- Take XY coordinates (ignore Z) ---
    pts = np.array(ctrl_pts[:, :2])

    # --- Remove duplicate consecutive points ---
    pts_diff = np.diff(pts, axis=0)
    pts = pts[np.concatenate([[True], np.any(pts_diff != 0, axis=1)])]

    # --- Pad endpoints ---
    pts = np.vstack([pts[0], pts, pts[-1]])

    def tj(ti, pi, pj):
        return ((np.linalg.norm(pj - pi))**alpha) + ti

    n_segments = len(pts) - 3
    n_points_per_seg = max(n_points // n_segments, 2)

    curve = []

    for i in range(n_segments):
        p0, p1, p2, p3 = pts[i: i + 4]

        t0 = 0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)

        # avoid division by zero
        if t1 == t0:
            t1 += 1e-6
        if t2 == t1:
            t2 += 1e-6
        if t3 == t2:
            t3 += 1e-6

        t = np.linspace(t1, t2, n_points_per_seg)
        for tt in t:
            A1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
            A2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
            A3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
            B1 = (t2 - tt) / (t2 - t0) * A1 + (tt - t0) / (t2 - t0) * A2
            B2 = (t3 - tt) / (t3 - t1) * A2 + (tt - t1) / (t3 - t1) * A3
            C = (t2 - tt) / (t2 - t1) * B1 + (tt - t1) / (t2 - t1) * B2
            curve.append(C)

    # --- Convert list of segments into a single array ---
    curve = np.vstack(curve)

    # --- Find index of LE (minimum x) ---
    le_idx = np.argmin(curve[:, 0])

    # --- Separate lower and upper surfaces ---
    # Lower: TE (x~1) -> LE (x=0), include LE, exclude duplicate TE final
    lower_surface = curve[:le_idx + 1]

    # Upper: LE -> TE final (x~1), include TE final, exclude duplicate LE
    upper_surface = curve[le_idx + 1:]

    # --- Combine surfaces without duplicating TE or LE ---
    ordered_curve = np.vstack([lower_surface, upper_surface])

    # --- Normalize chord length to 1 and save scaling ---
    x = ordered_curve[:, 0]
    y = ordered_curve[:, 1]

    # Shift so LE is at x=0
    x -= s
    x[-1] = x[0]
    y[-1] = y[0]
    return np.column_stack([x, y])


def linear_curve(ctrl_pts, n_points, s):
    """Linear curve with control points."""
    n_points_per_seg = n_points // 4
    curve = []
    for i in range(len(ctrl_pts) - 1):
        seg = np.linspace(ctrl_pts[i, :2], ctrl_pts[i + 1, :2], n_points_per_seg)
        curve.append(seg)

    # --- Convert list of segments into a single array ---
    curve = np.vstack(curve)

    # --- Find index of LE (minimum x) ---
    le_idx = np.argmin(curve[:, 0])

    # --- Lower surface: TE -> LE (exclude LE at the end) ---
    lower_surface = curve[:le_idx]  # up to but not including LE

    # --- Upper surface: LE -> TE (include LE at start) ---
    upper_surface = curve[le_idx:]  # from LE to TE
    upper_surface = upper_surface[::-1]  # reverse to go LE -> TE

    # --- Combine lower + upper without duplicating points ---
    ordered_curve = np.vstack([lower_surface, upper_surface])

    # --- Normalize chord length to 1 and save scaling ---
    x = ordered_curve[:, 0]
    y = ordered_curve[:, 1]

    # Shift so LE is at x=0
    x -= s
    x[-1] = x[0]
    y[-1] = y[0]

    normalized_curve = np.column_stack([x, y])

    return normalized_curve


def get_coord_edit_curve(xsec_id,n):
    """
    Generate coordinates from an editable user-defined curve.

    Reads the control points of the selected cross-section and evaluates the
    resulting curve using the type specified in OpenVSP (linear, spline, or
    cubic Bézier).
    """
    geom_parm = get_params_by_name(xsec_id,['Width','Height'])
    Scaling = [geom_parm['Width'],geom_parm['Height']]
    control_points = vsp.GetEditXSecCtrlVec(xsec_id,non_dimensional=True)
    pts = np.array([[p.x(),p.y(),p.z()] for p in control_points])

    le_idx = len(pts) // 2
    le_pt = pts[le_idx]
    shift = le_pt[0]

    # check the type of curve
    # 0 -> linear
    # 1 -> spline
    # 2 -> cubic bezier
    curve_type_parm = vsp.GetXSecParm(xsec_id, "CurveType")
    curve_type = int(vsp.GetParmVal(curve_type_parm))
    if curve_type == 0:
        curve_pts = linear_curve(pts,n,shift)
        Name = "Linear_Spline"
    elif curve_type == 1:
        curve_pts = spline_curve(pts,n,shift)
        Name = "Cubic_Spline"
    elif curve_type == 2:
        curve_pts = bezier_curve(pts,n,shift)
        Name = "Cubic_Bézier"
    return curve_pts[:, 0], curve_pts[:, 1], Name, Scaling, shift


profile_mapping = {
    vsp.XS_UNDEFINED: "Undefined",
    vsp.XS_POINT: get_coord_point,  # 0
    vsp.XS_CIRCLE: get_coord_circle,  # 1
    vsp.XS_ELLIPSE: get_coord_ellipse,  # 2
    vsp.XS_SUPER_ELLIPSE: get_coord_superellipse,  # 3
    vsp.XS_ROUNDED_RECTANGLE: get_coord_roundedrectangle,  # 4
    vsp.XS_GENERAL_FUSE: "General Fuselage",  # 5
    vsp.XS_FILE_FUSE: "Fuselage File",  # 6
    vsp.XS_FOUR_SERIES: lambda idx, n=None: get_coord_naca4(idx, n),  # 7
    vsp.XS_SIX_SERIES: "NACA 6-Series",  # 8
    vsp.XS_BICONVEX: "Biconvex",  # 9
    vsp.XS_WEDGE: "Wedge",  # 10
    vsp.XS_EDIT_CURVE: get_coord_edit_curve,  # 11
    vsp.XS_FILE_AIRFOIL: lambda idx, n=None: get_coord_from_file(idx, n),  # 12
    vsp.XS_CST_AIRFOIL: "CST Parameterized",  # 13
    vsp.XS_VKT_AIRFOIL: "VKT ",  # 14
    vsp.XS_FOUR_DIGIT_MOD: lambda idx, n=None: get_coord_naca4_mod(idx, n),  # 15
    vsp.XS_FIVE_DIGIT: lambda idx, n=None: get_coord_naca5(idx, n),  # 16
    vsp.XS_FIVE_DIGIT_MOD: lambda idx, n=None: get_coord_naca5_mod(idx, n),  # 17
    vsp.XS_ONE_SIX_SERIES: "16-Series",  # 18
    vsp.XS_NUM_TYPES: "Number of XSec Types (placeholder)",  # 19
}


def Get_coordinates_profile(idx, *args, **kwargs):
    """
    profile_mapping links each OpenVSP XSec shape ID to the corresponding
    coordinate generation function. `Get_coordinates_profile()` reads the section
    type from OpenVSP, selects the appropriate function, and returns the computed
    coordinate set. Functions that require discretization receive `n`; others are
    called without it.

    CPACS requires:
    - For a conventional wing, the airfoil coordinates are defined in x and z with
      all the y-coordinates set to "0". The points have to be ordered from the
      trailing edge along the lower side to the leading edge and then along the
      upper side back to the trailing edge.
    """

    Airfoil_name_type = vsp.GetXSecShape(idx)
    func = profile_mapping[Airfoil_name_type]
    try:
        return func(idx, *args, **kwargs)
    except TypeError:
        return func(idx)



def get_profile_section(
    Component,
    xsec_id,
    idx,
    Twist_val,
    Twist_loc,
    Rel,
    Twist_list,
):

    # Tess_W control how many points you need to define the shape of the profile
    Tess_W = int(vsp.GetParmVal(Component, "Tess_W", "Shape"))

    # get profile
    x, y, Airfoil_name, Scaling, shift = Get_coordinates_profile(xsec_id, Tess_W)

    # ---- Tesselation ----
    if vsp.GetGeomTypeName(Component) == "Wing":
        x_airfoil, y_airfoil = Tesselation(Component, xsec_id, x, y)

        # ---- geometrical twist ----
        if idx >= 1:
            # Twist value
            Twist = Twist_val - Twist_list(-1) if Rel else Twist_val

            # positive Twist if clockwise
            Twist_rad = np.deg2rad(-Twist)

            # rotation using X' = X_0 + R*X

            RotationMatrix = np.array(
                [
                    [np.cos(Twist_rad), -np.sin(Twist_rad)],
                    [np.sin(Twist_rad), np.cos(Twist_rad)],
                ]
            )

            # the origin_shift control the Twist location from openVSP
            Origin_shift = np.array([float(Twist_loc), 0])
            Origin_shift = Origin_shift.reshape(2, 1)
            Coord_noTwist = np.array(
                [
                    x_airfoil,
                    y_airfoil,
                ]
            )
            Coord_shift = Coord_noTwist - Origin_shift
            Coord_rot = np.dot(RotationMatrix, Coord_shift) + Origin_shift
            x = Coord_rot[0, :]
            y = Coord_rot[1, :]
    
    # LE duplicates from twist part. 
    zero_idx = np.where(np.isclose(x, 0.0, atol=1e-12))[0]
    if len(zero_idx) > 1:
        x = np.delete(x, zero_idx[1:])
        y = np.delete(y, zero_idx[1:])

    return [x, y], Airfoil_name, Scaling, shift


def Tesselation(Component, idx, x, y):

    # ---- import from the vsp file ----
    TessLE = vsp.GetParmVal(Component, "LECluster", "WingGeom")
    TessTE = vsp.GetParmVal(Component, "TECluster", "WingGeom")

    # ---- Constrain ot the tesselation values ----
    if TessLE > 9:
        TessLE = 9
    elif TessLE < 1:
        TessLE = 1

    if TessTE > 9:
        TessTE = 9
    elif TessTE < 1:
        TessTE = 1

    # ---- default Tessselation ----
    nb_points = int(np.shape(x)[0])

    if vsp.GetXSecShape(idx) in [7, 12, 15, 16, 17]:

        LE_index = np.argmin(x)
        x_upper = x[LE_index:]
        y_upper = y[LE_index:]
        x_lower = x[: LE_index + 1]
        y_lower = y[: LE_index + 1]

        # ---- LE and TE tesselation ---- #
        # This part refines and reconstructs the airfoil’s surface by redistributing points
        # near the leading and trailing edges using adjustable tessellation parameters
        # (TessLE, TessTE).

        minimum = 0
        maximum = 1
        x_inter_LE = np.concatenate(
            (
                np.linspace(
                    minimum,
                    maximum / 2 * (TessLE / 10),
                    int(nb_points / 2 * (1 - TessLE / 10)),
                ),
                np.linspace(
                    maximum / 2 * TessLE / 10,
                    maximum / 2,
                    int(nb_points / 2 * TessLE / 10),
                ),
            ),
            axis=0,
        )
        x_inter_TE = np.concatenate(
            (
                np.linspace(
                    maximum / 2,
                    maximum - (maximum / 2 * TessTE / 10),
                    int(nb_points / 2 * TessTE / 10),
                ),
                np.linspace(
                    maximum - (maximum / 2 * TessTE / 10),
                    maximum,
                    int(nb_points / 2 * (1 - TessTE / 10)),
                ),
            ),
            axis=0,
        )
        x_inter = np.concatenate((x_inter_LE, x_inter_TE), axis=0)
        x_upper, unique_idx = np.unique(x_upper, return_index=True)
        y_upper = y_upper[unique_idx]
        f_u = interp1d(
            x_upper,
            y_upper,
            kind="cubic",
            bounds_error=False,
        )
        y_upper = f_u(x_inter)
        x_lower, unique_idx = np.unique(x_lower, return_index=True)
        y_lower = y_lower[unique_idx]
        f_l = interp1d(
            x_lower,
            y_lower,
            kind="cubic",
            bounds_error=False,
        )
        y_lower = f_l(x_inter)
        x = np.concatenate((np.flip(x_inter), x_inter), axis=0)
        y = np.concatenate((np.flip(y_lower), y_upper), axis=0)

    # Close the profile
    y[-1] = y[0]
    x[-1] = x[0]

    return x, y


def Extract_transformation(Component):
    Name_type = vsp.GetGeomTypeName(Component)
    if Name_type == "Wing":
        Name_default_comp = "WingGeom"
        reference_length = vsp.GetParmVal(Component, "MAC", "WingGeom")
    elif Name_type == "Fuselage":
        Name_default_comp = "FuseGeom"
        reference_length = 0  # it will be update later wiht the diameter
    elif Name_type == "Pod":
        Name_default_comp = "Geom"
        reference_length = 0  # it will be update later wiht the diameter

    # Name
    Name = vsp.GetGeomName(Component)
    rot_names = ["X_Rotation", "Y_Rotation", "Z_Rotation"]
    trasl_names = ["X_Location", "Y_Location", "Z_Location"]
    x_Rot, y_Rot, z_Rot = [
        vsp.GetParmVal(vsp.GetParm(Component, pname, "XForm")) for pname in rot_names
    ]
    x_trasl, y_trasl, z_trasl = [
        vsp.GetParmVal(vsp.GetParm(Component, pname, "XForm")) for pname in trasl_names
    ]

    Sym_value = vsp.GetParmVal(vsp.GetParm(Component, "Sym_Planar_Flag", "Sym"))
    Symm_index = [" ", "x-y-plane", "x-z-plane", "y-z-plane"]
    Symmetry = Symm_index[int(float(Sym_value))] if Sym_value != "0" else "0"
    ParentUid = vsp.GetGeomParent(Component)
    ParentUid = ParentUid if ParentUid is not None else 0

    # Only wings expose these parameters; avoid querying them for fuselages/pods
    # to prevent OpenVSP "Can't Find Parm" errors.
    Relative_dih = 0.0
    Relative_Twist = 0.0
    if Name_type == "Wing":
        Relative_dih = float(
            vsp.GetParmVal(vsp.GetParm(Component, "RelativeDihedralFlag", Name_default_comp))
        )
        Relative_Twist = float(
            vsp.GetParmVal(vsp.GetParm(Component, "RelativeTwistFlag", Name_default_comp))
        )

    transformation_dict = {
        "Name_type": Name_type,
        "Name": Name,
        "X_Rot": [x_Rot, y_Rot, z_Rot],
        "X_Trasl": [x_trasl, y_trasl, z_trasl],
        "Symmetry": Symmetry,
        "abs_system": True,
        "Relative_dih": Relative_dih,
        "Relative_Twist": Relative_Twist,
        "ParentUid": ParentUid,
        "reference_length": reference_length,
    }
    return transformation_dict


def Wing_Sections(wing, idx):
    Alias = f'Section{idx}'
    Dihedral_Angle = vsp.GetParmVal(wing,'Dihedral',f'XSec_{idx}')
    Sweep_angle = vsp.GetParmVal(wing,'Sweep',f'XSec_{idx}')
    Sweep_loc = vsp.GetParmVal(wing,'Sweep_Location',f'XSec_{idx}')
    Twist = vsp.GetParmVal(wing,'Twist',f'XSec_{idx}')
    Twist_loc = vsp.GetParmVal(wing,'Twist_Location',f'XSec_{idx}')
    Span = vsp.GetParmVal(wing,'Span',f'XSec_{idx}')
    return [Alias, Dihedral_Angle, Sweep_angle,Sweep_loc, Twist, Twist_loc, Span]
