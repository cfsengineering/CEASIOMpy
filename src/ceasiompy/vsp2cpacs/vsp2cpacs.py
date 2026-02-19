"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

openVSP integration inside CEASIOMpy.
The geometry is built in OpenVSP, saved as a .vsp3 file, and then selected in the GUI.
It is subsequently processed by this module to generate a CPACS file.

| Author: Nicolo' Perasso
| Creation: 23/12/2025
"""

# Imports

import openvsp as vsp

from pathlib import Path

from ceasiompy.vsp2cpacs.func.duct import Import_Duct
from ceasiompy.vsp2cpacs.func.fuselage import Import_Fuse
from ceasiompy.vsp2cpacs.func.pod import Import_POD
from ceasiompy.vsp2cpacs.func.wing import Import_Wing

from ceasiompy.vsp2cpacs.func.exportcpacs import Export_CPACS

from ceasiompy import log


# Functions

def get_plantform_area(geom_id):
    vsp.Update()
    analysis = "Projection"
    vsp.SetStringAnalysisInput(analysis, "TargetGeomID", [geom_id])
    vsp.SetIntAnalysisInput(analysis, "TargetSet", [0])
    vsp.SetIntAnalysisInput(analysis, "DirectionType", [2])
    res_id = vsp.ExecAnalysis(analysis)
    return vsp.GetDoubleResults(res_id, "Comp_Areas")


def CheckParent(Data, idx, Parents, Uid):
    # Check parent-child relationships between OpenVSP components
    Parents[f"{idx}"] = {
        "Uid_parent": Data[f"{idx}"]["Transformation"]["ParentUid"],
        "Uid": Uid,
        "Name": Data[f"{idx}"]["Transformation"]["Name"],
    }
    for i in list(Parents.keys())[:idx]:
        if Parents[i]["Uid"] == Parents[f"{idx}"]["Uid_parent"]:
            Data[f"{idx}"]["Transformation"]["Child_to_Parent"] = Parents[i]["Name"]
            break


def main(vsp_file: str | Path, output_dir: str | Path | None = None) -> Path:
    vsp_file = Path(vsp_file)
    output_dir = Path(output_dir) if output_dir is not None else None

    # Read the OpenVSP file
    log.info(f"Reading OpenVSP file: {vsp_file} ")
    vsp.ClearVSPModel()
    vsp.ReadVSPFile(str(vsp_file))

    # File Name
    name_file = vsp_file.stem

    log.info("Processing OpenVSP geometry... ")
    # Find the components
    geom_ids = vsp.FindGeoms()

    # Some initializations
    component_idx = 0
    data_from_vsp, parent_list = {}, {}
    idx_engine = 0

    log.info("Loading OpenVSP geometry... ")
    for geom_id in geom_ids:
        # Determine the component type from the OpenVSP geometry
        geom_type = vsp.GetGeomTypeName(geom_id)

        if geom_type == "Wing":
            # Extract the required parameters to define the CPACS component
            data_from_vsp[f"{component_idx}"] = Import_Wing(geom_id)

            # Check if it is a child connected to a parent
            CheckParent(data_from_vsp, component_idx, parent_list, geom_id)

            component_idx += 1

        elif geom_type == "Fuselage":
            # Extract the required parameters to define the CPACS component
            data_from_vsp[f"{component_idx}"] = Import_Fuse(geom_id)

            # Check if it is a child connected to a parent
            CheckParent(data_from_vsp, component_idx, parent_list, geom_id)

            component_idx += 1

        elif geom_type == "Pod":
            # Extract the required parameters to define the CPACS component
            data_from_vsp[f"{component_idx}"] = Import_POD(geom_id)

            # Check if it is a child connected to a parent
            CheckParent(data_from_vsp, component_idx, parent_list, geom_id)

            # The pod is also a part inside the engine (centerCowl)
            if (
                component_idx > 2
                and data_from_vsp[f"{component_idx - 1}"]["Transformation"]["Name_type"] == "Duct"
            ):
                data_from_vsp[f"{component_idx}"]["Transformation"]["idx_engine"] = idx_engine
            else:
                data_from_vsp[f"{component_idx}"]["Transformation"]["idx_engine"] = None

            component_idx += 1

        elif geom_type == "Custom":
            # Extract the required parameters to define the CPACS component
            data_from_vsp[f"{component_idx}"] = Import_Duct(geom_id)

            # Check if it is a child connected to a parent
            CheckParent(data_from_vsp, component_idx, parent_list, geom_id)

            # Check whether the component belongs to an engine.
            # A complete engine in CPACS consists of two ducts and one pod
            # (fan, core, and center body).
            if data_from_vsp[f"{component_idx - 1}"]["Transformation"]["Name_type"] != "Duct":
                idx_engine += 1
            data_from_vsp[f"{component_idx}"]["Transformation"]["idx_engine"] = idx_engine

            component_idx += 1

    # Create a CPACS file.
    log.info("Creating CPACS file...")

    exporter = Export_CPACS(data_from_vsp, name_file, output_dir=output_dir)
    return exporter.run()
