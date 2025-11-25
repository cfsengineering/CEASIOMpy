
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
from pathlib import Path
from ceasiompy.VSP2CPACS.func.Wing import Import_Wing
#from ceasiompy.VSP2CPACS.func.Fuselage import Import_Fuse
#from ceasiompy.VSP2CPACS.func.POD import Import_POD
#from ceasiompy.VSP2CPACS.func.Duct import Import_Duct
from ceasiompy.VSP2CPACS.func.Export_CPACS_format import Export_CPACS
import openvsp as vsp


import warnings
warnings.filterwarnings("ignore")
# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def get_plantform_area(geom_id):
    vsp.Update()
    analysis = 'Projection'
    vsp.SetStringAnalysisInput(analysis,'TargetGeomID',[geom_id])
    vsp.SetIntAnalysisInput(analysis,'TargetSet',[0])
    vsp.SetIntAnalysisInput(analysis,'DirectionType',[2])
    res_id = vsp.ExecAnalysis(analysis)
    return vsp.GetDoubleResults(res_id,'Comp_Areas')
    
def CheckParent(Data, idx, Parents,Uid):

    Parents[f'{idx}'] = {
        'Uid_parent': Data[f'{idx}']['Transformation']['ParentUid'],
        'Uid': Uid,
        'Name': Data[f'{idx}']['Transformation']['Name']
    }
    for i in list(Parents.keys())[:idx]:
        if Parents[i]['Uid'] == Parents[f'{idx}']['Uid_parent']:
            Data[f'{idx}']['Transformation']['Child_to_Parent'] = Parents[i]['Name']
            break


#if __name__ == "__main__":

def main(vsp_file):
    
    # Read the file 
    print('------------------- VSP2CPACS -------------------------')   
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
    total_plantform_area = 0
    idx_engine = 0
    
    
    print('[INFO] Loading OpenVSP geometry... ')
    for geom_id  in geom_ids:
        # Search into the xml file the type of component.
        geom_type = vsp.GetGeomTypeName(geom_id)
    
        '''# Calculate plantform area of the component
        print(geom_type,float(get_plantform_area(geom_id)[ComponentIdx]))
        total_plantform_area += float(get_plantform_area(geom_id)[ComponentIdx])
        print('AREA ===',get_plantform_area(geom_id)[ComponentIdx])'''

        if geom_type == 'Wing':
            
            # Take the correct parameters ot define a CPACS file
            Data_from_VSP[f'{ComponentIdx}'] = Import_Wing(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(
                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            ComponentIdx += 1

        elif geom_type == 'Fuselage':
            
            # Take the correct parameters ot define a CPACS file
            Data_from_VSP[f'{ComponentIdx}'] = Import_Fuse(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(

                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            ComponentIdx += 1
        elif geom_type == 'Pod' :
            
            # Take the correct parameters ot define a CPACS file
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

            # Take the correct parameters ot define a CPACS file
            Data_from_VSP[f'{ComponentIdx}'] = Import_Duct(geom_id)
            
            # Check if it is a child connected to a parent
            CheckParent(
                Data_from_VSP, ComponentIdx, Parent_List,geom_id)
            
            # Check if it is an engine. To built a complete engine you need Duct + Duct + pod ( fan + core + center in CPACS)
            if Data_from_VSP[f'{ComponentIdx-1}']['Transformation']['Name_type'] != 'Duct':
                idx_engine +=1 
            Data_from_VSP[f'{ComponentIdx}']['Transformation']['idx_engine'] = idx_engine     

            ComponentIdx += 1

    
    
    '''# save the total area
    Data_from_VSP['total_area'] = total_plantform_area
    print('total plantoform area is ',total_plantform_area)
    breakpoint()
    vsp.Update()
    analysis = 'Projection'
    # Esegui analisi globale per tutti i componenti
    vsp.SetIntAnalysisInput(analysis, 'TargetSet', [0])  # include tutti i componenti
    vsp.SetIntAnalysisInput(analysis, 'DirectionType', [2])  # proiezione lungo Z (XY plane)

    res_id = vsp.ExecAnalysis(analysis)

    # Ottieni l'area totale della planform
    total_area = vsp.GetDoubleResults(res_id, 'Comp_Areas')
    print('aera with the other method ====',total_area)'''
    
    # Create a CPACS file.
    print('[INFO] Creating CPACS file...')
    
    CPACS_file = Export_CPACS(Data_from_VSP,name_file)
    CPACS_file.run()
    print('--------------------------------------------')