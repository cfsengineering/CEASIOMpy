
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
from ceasiompy.VSP2CPACS.func.Wing import Extract_transformation
from ceasiompy.VSP2CPACS.func.Wing import get_profile_section
import copy
import openvsp as vsp

import warnings
warnings.filterwarnings("ignore")
# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def Import_Fuse(Fuselage):
    
    # Some inizializations
    Sections_information = {}
    n_section_idx = 0

    # ---- Trasforming information ----
    # Inside Extract_transformation there are the global informations that characterize the component
    Sections_information['Transformation'] = Extract_transformation(Fuselage)
    Sections_information['Transformation']['Length'] = vsp.GetParmVal(Fuselage,'Length','Design')
    Sections_information['Transformation']['idx_engine'] = None
    
    # ---- section informations ----
    # Save the parameters to define sections 
    # Create a nested dictionary where for every section there are specific keys to import the parameters
    Output_inf = ['x_rot', 'y_rot', 'z_rot' ,'x_loc', 'y_trasl', 'z_trasl', 'spin']


    # Number of sections
    xsec_surf_id = vsp.GetXSecSurf(Fuselage,0)
    num_xsecs = vsp.GetNumXSec(xsec_surf_id)
    

    
    for i in range(num_xsecs):
        xsec_id = vsp.GetXSec(xsec_surf_id,i)
        xsec_type = vsp.GetXSecShape(xsec_id)
        
        # ---- section ----
        Section_VSP = Fuse_Section(Fuselage, i, Sections_information['Transformation']['Length'])
        
        # ---- profile  ---- 
        Sections_information[f'Section{n_section_idx}'] = dict(zip(Output_inf, Section_VSP))
        coord, Name,Scaling,shift = get_profile_section(Fuselage,xsec_id,i,Twist_val=0,Twist_loc=0,Rel=0,Twist_list=0)        
       
        if shift is not None:
            Sections_information[f'Section{n_section_idx}']['z_trasl'] = Sections_information[f'Section{n_section_idx}']['z_trasl'] + (0.5- np.abs(shift)) 
        else:
            Sections_information[f'Section{n_section_idx}']['z_trasl'] = Sections_information[f'Section{n_section_idx}']['z_trasl']
    
        # center the points
        coord -= np.mean(coord,axis = 1, keepdims = True)
        
        # reorder the points
        coord= reorder_fuselage_profile(coord[0,:],coord[1,:])
        
        Sections_information[f'Section{n_section_idx}']['Airfoil'] = Name
        Sections_information[f'Section{n_section_idx}']['Airfoil_coordinates'] = coord
        
        # Scaling is composed by the width and hight or chord to scale the normalized profile. 
        if len(Scaling) == 2:
            Sections_information[f'Section{n_section_idx}']['x_scal'] = 1
            Sections_information[f'Section{n_section_idx}']['y_scal'] = Scaling[0]
            Sections_information[f'Section{n_section_idx}']['z_scal'] = Scaling[1]
            Sections_information['Transformation']['reference_length'] = Scaling[0] 
        else:
            Sections_information[f'Section{n_section_idx}']['x_scal'] = 1
            Sections_information[f'Section{n_section_idx}']['y_scal'] = Scaling[0]
            Sections_information[f'Section{n_section_idx}']['z_scal'] = Scaling[0]
        if Name == 'Point':
            Sections_information[f'Section{n_section_idx}']['x_scal'] = 0
            Sections_information[f'Section{n_section_idx}']['y_scal'] = 0
            Sections_information[f'Section{n_section_idx}']['z_scal'] = 0
            
        '''
        if Sections_information['Transformation']['reference_length'] < Scaling[0]:           
                Sections_information['Transformation']['reference_length'] = Scaling[0] 
        '''
        
        # spin feature
        if Sections_information[f'Section{n_section_idx}']['spin'] != 0:
                        
            '''
            If a section has a non-zero spin value, two additional sections are created
            to represent a smooth twisted transition. The original section is duplicated,
            then the copy is rotated around its local axis at two positions located
            half-distance (± mid_length) from the original x-location. This produces:
            - a “pre-spin” section
            - the original twisted section
            - a “post-spin” section
            After insertion, the section index jumps by 3, otherwise only one step.
            
            ''' 
            mid_length = (Sections_information[f'Section{n_section_idx}']['x_loc'] -
                          Sections_information[f'Section{n_section_idx-1}']['x_loc'])/2
            
            Sections_information[f'Section{n_section_idx + 1}'] = copy.deepcopy(Sections_information[f'Section{n_section_idx}'])

            Sections_information[f'Section{n_section_idx}'] = Spin_func(Sections_information[f'Section{n_section_idx+1}']['spin'], Sections_information[f'Section{n_section_idx + 1}'], Sections_information[f'Section{n_section_idx + 1}']['x_loc'] - mid_length,Sections_information[f'Section{n_section_idx+1}']['x_rot'])
            
            Sections_information[f'Section{n_section_idx+2}'] = Spin_func(Sections_information[f'Section{n_section_idx+1}']['spin'], Sections_information[f'Section{n_section_idx + 1}'], Sections_information[f'Section{n_section_idx + 1}']['x_loc'] + mid_length,Sections_information[f'Section{n_section_idx+1}']['x_rot'])
            n_section_idx += 3
        else:
            n_section_idx += 1

    return Sections_information

def reorder_fuselage_profile(x, y):
    """
    CPACS requires a different order for the profile's points for the fuselage respect the wing. 
    
    - the coordinates are typically given in y and z with x set to "0". 
    Starting point of the profile should be the lowest point (typically 
    in the symmetry plane), then upwards on the positive y-side up to the
    highest point (again, typically in the symmetry plane). Depending on, 
    whether the fuselage shall be specified with symmetry condition or not,
    the profile either ends there, or continues on the negative y-side back
    down to the lowest point. 
    
    """
    x = np.array(x)
    y = np.array(y)
    
    # Check dimensions
    if x.shape != y.shape:
        raise ValueError("x e y devono avere la stessa dimensione")
    
    # Filter negative points 
    neg_idx = np.where(y < 0)[0]
    if len(neg_idx) == 0:
        raise ValueError("Nessun punto con y negativa trovato")
    
    # Between the points with y<0, find which of them are closer to x = 0
    central_idx = neg_idx[np.argmin(np.abs(x[neg_idx]))]
    
    # If more points have x value close to 0, choose one with the minumum y
    candidate_idxs = neg_idx[np.abs(x[neg_idx] - x[central_idx]) < 1e-12]  # tolleranza numerica minima
    start_idx = candidate_idxs[np.argmin(y[candidate_idxs])]
    
    # Divide the profile in two parts: TE to starting pointand from the starting point to the TE passing through the LE
    lower_points_idx = np.arange(start_idx, len(x))
    upper_points_idx = np.arange(0, start_idx+1)
    
    
    
    # Combine
    final_idx = np.concatenate([lower_points_idx, upper_points_idx])
    x_new = x[final_idx]
    y_new = y[final_idx]
    coord = np.vstack((x_new, y_new))
    
    # Remove duplicates 
    mask = np.ones(coord.shape[1], dtype=bool)
    for i in range(1, coord.shape[1]):
        if np.allclose(coord[:, i], coord[:, i-1]):
            mask[i] = False
    coord = coord[:, mask]

    # Close the profie if necesssary
    if not np.allclose(coord[:, 0], coord[:, -1]):
        coord = np.hstack([coord, coord[:, 0:1]])
        
    return coord


def Fuse_Section(Fuselage,idx, l):
    
    # translations - rotations - spin - scaling
    x_loc = vsp.GetParmVal(Fuselage,'XLocPercent',f'XSec_{idx}') * l
    y_trasl = vsp.GetParmVal(Fuselage,'YLocPercent',f'XSec_{idx}') * l
    z_trasl = vsp.GetParmVal(Fuselage,'ZLocPercent',f'XSec_{idx}') * l
    x_rot = vsp.GetParmVal(Fuselage,'XRotate',f'XSec_{idx}')
    y_rot = vsp.GetParmVal(Fuselage,'YRotate',f'XSec_{idx}')
    z_rot = vsp.GetParmVal(Fuselage,'ZRotate',f'XSec_{idx}')
    spin = vsp.GetParmVal(Fuselage,'Spin',f'XSec_{idx}')
    
    return [x_rot, y_rot, z_rot,x_loc, y_trasl, z_trasl,spin]


def Spin_func(spin, Section_informations, x_loc,x_rot):
    # Spin parameters. 
    # It is an implementation different from openVSP but is very close ot it. Be aware of it. 
    # When at the section{i} is set a value of spin, it generates two more section one upstream 
    # and one downstream that scale their dimension and rotate by a factor that take count of the spin.
    
    # copy the section{i}
    Add_section = copy.deepcopy(Section_informations)
    
    a = abs(float(spin) + (- float(x_rot) * 0.25 / 90))
    
    Add_section['x_rot'] = float(
        x_rot) - ((float(spin) * 90)/0.25)
    Add_section['y_scal'] = 2 * abs(a - 0.5)
    Add_section['z_scal'] = 2 * abs(a - 0.5)
    Add_section['x_scal'] = 1
    Add_section['x_loc'] = x_loc
    return Add_section
