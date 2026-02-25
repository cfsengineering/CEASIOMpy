
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOMpy.
The geometry is built in OpenVSP, saved as a .vsp3 file, and then selected in the GUI.
It is subsequently processed by this module to generate a CPACS file.

| Author: Nicolo' Perasso
| Creation: 22/12/2025
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================
from pathlib import Path
from ceasiompy.vsp2cpacs.func.wing import Import_Wing
from ceasiompy.vsp2cpacs.func.fuselage import Import_Fuse
from ceasiompy.vsp2cpacs.func.pod import Import_POD
from ceasiompy.vsp2cpacs.func.duct import Import_Duct
from ceasiompy.vsp2cpacs.func.exportcpacs import Export_CPACS
import openvsp as vsp

import warnings

warnings.filterwarnings("ignore")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def CheckParent(Data, idx, Parents,Uid):
    # Check parent-child relationships between OpenVSP components
    Parents[f'{idx}'] = {
        'Uid_parent': Data[f'{idx}']['Transformation']['ParentUid'],
        'Uid': Uid,
        'Name': Data[f'{idx}']['Transformation']['Name']
    }
    for i in list(Parents.keys())[:idx]:
        if Parents[i]['Uid'] == Parents[f'{idx}']['Uid_parent']:
            Data[f'{idx}']['Transformation']['Child_to_Parent'] = Parents[i]['Name']
            break



def main(vsp_file):
    
    # Read the OpenVSP file 
    print('------------------- Start of VSP2CPACS -------------------------')   
    print('[INFO] Initializing VSP2CPACS module... ')
    vsp.ClearVSPModel()
    vsp.ReadVSPFile(vsp_file)
    
    # File Name
    name_file = Path(vsp_file).stem
    
    # Find the components
    geom_ids  = vsp.FindGeoms()
    
    # Some initializations
    ComponentIdx = 0      
    Data_from_VSP, Parent_List = {}, {}
    idx_engine = 0
    
    
    print('[INFO] Loading OpenVSP geometry... ')
    for geom_id  in geom_ids:
        # Determine the component type from the OpenVSP geometry
        geom_type = vsp.GetGeomTypeName(geom_id)
    
        

        if geom_type == 'Wing':
            
            # Extract the required parameters to define the CPACS component
            Data_from_VSP[f'{ComponentIdx}'] = Import_Wing(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(
                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            ComponentIdx += 1

        elif geom_type == 'Fuselage':
            
            # Extract the required parameters to define the CPACS component
            Data_from_VSP[f'{ComponentIdx}'] = Import_Fuse(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(

                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            ComponentIdx += 1
        elif geom_type == 'Pod' :
            
            # Extract the required parameters to define the CPACS component
            Data_from_VSP[f'{ComponentIdx}'] = Import_POD(geom_id)
            
            
            # Check if it is a child connected to a parent
            CheckParent(
                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            # The pod is also a part inside the engine (centerCowl)
            if ComponentIdx > 2 and Data_from_VSP[f'{ComponentIdx-1}']['Transformation']['Name_type'] == 'Duct' :
                Data_from_VSP[f'{ComponentIdx}']['Transformation']['idx_engine'] = idx_engine
            else:
                Data_from_VSP[f'{ComponentIdx}']['Transformation']['idx_engine'] = None
            ComponentIdx += 1
        
        elif geom_type == 'Custom':

            # Extract the required parameters to define the CPACS component
            Data_from_VSP[f'{ComponentIdx}'] = Import_Duct(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(
                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            # Check whether the component belongs to an engine.
            # A complete engine in CPACS consists of two ducts and one pod
            # (fan, core, and center body).
            if Data_from_VSP[f'{ComponentIdx-1}']['Transformation']['Name_type'] != 'Duct':
                idx_engine +=1 
            Data_from_VSP[f'{ComponentIdx}']['Transformation']['idx_engine'] = idx_engine     

            ComponentIdx += 1

    
    # Create a CPACS file.
    print('[INFO] Creating CPACS file...')
    
    CPACS_file = Export_CPACS(Data_from_VSP,name_file)
    CPACS_file.run()
    print('[INFO] CPACS file saved in WKDIR')
    print('-------------------End of VSP2CPACS-----------------------')
