
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOmpy. Built the geometry in openVSP, save as .svp3 and after select it inside the GUI. 
After it will pass through this module to have a CPACS file. 

| Author: Nicolo' Perasso
| Creation: ?????
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import openvsp as vsp

import warnings
warnings.filterwarnings("ignore")
# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def get_coord_engine_profile(geom_id,n):
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
    
    # import the parameters 
    m = vsp.GetParmVal(vsp.GetParm(geom_id,'Camber','Design'))
    p = vsp.GetParmVal(vsp.GetParm(geom_id,'CamberLoc','Design'))
    t = vsp.GetParmVal(vsp.GetParm(geom_id,'ThickChord','Design'))
    Invert_airfoil = vsp.GetParmVal(vsp.GetParm(geom_id,'InvertFlag','Design'))

    ###
    # NACA four digit: NACA XXXX
    # XXXX == 'mpt'
    
    ###
    Name = [int(round(m*100)), int(round(p*10)),int(round(t*100))]
    Name = f'NACA{Name[0]}{Name[1]}{Name[2]}'
    theta = np.linspace(0,np.pi,n//2)
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
    
    
    # If it is set to inverse the airfoil
    if Invert_airfoil:
        y_airfoil = - y_airfoil
        
    # center the normalized profile with the origin in the middle of the airfoil
    x -= 0.5
    
    Scaling = [vsp.GetParmVal(vsp.GetParm(geom_id,'Chord','Design')),vsp.GetParmVal(vsp.GetParm(geom_id,'Width','Design')),vsp.GetParmVal(vsp.GetParm(geom_id,'Height','Design'))]
    
    return [x, y], Name, Scaling
    
def Import_Duct(Duct):
    
    # Some inizializations
    Sections_information = {}
    parm_ids = vsp.GetGeomParmIDs(Duct)

    
    
    # ---- Trasforming information ----
    rot_names = ["X_Rotation", "Y_Rotation", "Z_Rotation"]
    trasl_names = ["X_Location", "Y_Location", "Z_Location"]
    x_Rot, y_Rot, z_Rot = [vsp.GetParmVal(vsp.GetParm(Duct, pname, "XForm")) for pname in rot_names]
    x_trasl, y_trasl, z_trasl = [vsp.GetParmVal(vsp.GetParm(Duct, pname, "XForm")) for pname in trasl_names]
    Sym_value = vsp.GetParmVal(vsp.GetParm(Duct, "Sym_Planar_Flag", "Sym"))
    Symm_index = [" ", "x-y-plane", "x-z-plane", "y-z-plane"]
    Symmetry = Symm_index[int(float(Sym_value))] if Sym_value != '0' else '0'
    ParentUid = vsp.GetGeomParent(Duct) if vsp.GetGeomParent(Duct) is not None else 0
    Sections_information['Transformation'] = {
        'Name_type': 'Duct',
        'Name': vsp.GetGeomName(Duct),
        'X_Rot': [x_Rot,y_Rot,z_Rot],
        'X_Trasl': [x_trasl,y_trasl,z_trasl],
        'Symmetry': Symmetry,
        'abs_system': True,
        'Relative_dih': False,
        'Relative_Twist': False ,
        'ParentUid': ParentUid,
        'reference_length':False
    }
    
    # ---- Take the airfoil section of the engine 
    coord,Name,Scaling = get_coord_engine_profile(Duct,120)
    Sections_information['Airfoil'] = Name
    Sections_information['Airfoil_coordinates'] = coord
    
    # ---- Import the transformation parameters 
    Sections_information['Transformation']['chord'] = Scaling[0]
    Sections_information['Transformation']['width'] = Scaling[1]
    Sections_information['Transformation']['height'] = Scaling[2]
    
    Sections_information['Transformation']['X_Rot'] = [x_Rot,y_Rot,z_Rot]
    Sections_information['Transformation']['X_Trasl'] = [x_trasl,y_trasl,z_trasl]
    
    return Sections_information
