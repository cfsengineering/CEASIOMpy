"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created around the airplane and the
resulting domain is meshed using gmsh

Python version: >=3.8

| Author: Guido Vallifuoco
| Creation: 2024-02-01

TODO:

    - It may be good to move all the function and some of the code in generategmsh()
    that are related to disk actuator to another python script and import it here

    - It may be better to propose more options for the mesh size of the different
    part (pylon,engine,rotor)

    - Add a boolean to deactivate the refinement factor according to the thickness of the
    truncated te of the wings. This options often create very small meshes and is not
    always required.

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

import subprocess
from pathlib import Path
from ceasiompy.CPACS2GMSH.func.generategmesh import (
    add_disk_actuator,
    duplicate_disk_actuator_surfaces,
    control_disk_actuator_normal,
    process_gmsh_log,
    ModelPart,
)
from ceasiompy.CPACS2GMSH.func.gmsh_utils import MESH_COLORS
from ceasiompy.utils.commonnames import (
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,
    ENGINE_EXHAUST_SUFFIX,
    ENGINE_INTAKE_SUFFIX,
    GMSH_ENGINE_CONFIG_NAME,
)
from ceasiompy.utils.commonxpath import GMSH_MESH_SIZE_FUSELAGE_XPATH, GMSH_MESH_SIZE_WINGS_XPATH
from ceasiompy.utils.configfiles import ConfigFile
import gmsh
import numpy as np
import os
from typing import List
from ceasiompy.CPACS2GMSH.func.advancemeshing import (
    refine_wing_section,
    set_domain_mesh,
    refine_small_surfaces,
    min_fields,
)
from ceasiompy.CPACS2GMSH.func.wingclassification import classify_wing

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_part_type, run_software

from cpacspy.cpacsfunctions import create_branch

from ceasiompy.CPACS2GMSH.func.mesh_sizing import fuselage_size, wings_size


log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_2d_mesh_for_pentagrow(
    cpacs,
    cpacs_path,
    brep_dir,
    results_dir,
    open_gmsh=False,
    n_power_factor=2,
    n_power_field=0.9,
    fuselage_mesh_size_factor=1,
    wing_mesh_size_factor=1.5,
    mesh_size_engines=0.23,
    mesh_size_propellers=0.23,
    refine_factor=2.0,
    refine_truncated=False,
    auto_refine=True,
    testing_gmsh=False,
):
    """
    Function to generate a mesh from brep files forming an airplane
    Function 'generate_gmsh' is a subfunction of CPACS2GMSH which return a
    mesh file useful for pentagrow.
    The airplane is fused with the different brep files : fuselage, wings and
    other parts are identified and fused together in order to obtain a watertight volume.
    Args:
    ----------
    cpacs : CPACS
        CPACS object
    brep_dir : Path
        Path to the directory containing the brep files
    results_dir : Path
        Path to the directory containing the result (mesh) files
    open_gmsh : bool
        Open gmsh GUI after the mesh generation if set to true
    symmetry : bool
        If set to true, the mesh will be generated with symmetry wrt the x,z plane
    mesh_size_fuselage : float
        Size of the fuselage mesh
    mesh_size_wings : float
        Size of the wing mesh
    mesh_size_engines : float
        Size of the engine mesh
    mesh_size_propellers : float
        Size of the propeller mesh
    advance_mesh : bool
        If set to true, the mesh will be generated with advanced meshing options
    refine_factor : float
        refine factor for the mesh le and te edge
    refine_truncated : bool
        If set to true, the refinement can change to match the truncated te thickness
    auto_refine : bool
        If set to true, the mesh will be checked for quality
    testing_gmsh : bool
        If set to true, the gmsh sessions will not be clear and killed at the end of
        the function, this allow to test the gmsh feature after the call of generate_gmsh()
    ...
    Returns:
    ----------
    mesh_file : Path
        Path to the mesh file generated by gmsh


    """
    # Determine if rotor are present in the aircraft model
    rotor_model = False
    if Path(brep_dir, "config_rotors.cfg").exists():
        rotor_model = True

    if rotor_model:
        log.info("Adding disk actuator")
        config_file = ConfigFile(Path(brep_dir, "config_rotors.cfg"))
        add_disk_actuator(brep_dir, config_file)

    # Retrieve all brep
    brep_files = list(brep_dir.glob("*.brep"))
    brep_files.sort()

    # initialize gmsh
    gmsh.initialize()
    # Stop gmsh output log in the terminal
    gmsh.option.setNumber("General.Terminal", 0)
    # Log complexity
    gmsh.option.setNumber("General.Verbosity", 5)

    # Import each aircraft original parts / parent parts
    fuselage_volume_dimtags = []
    wings_volume_dimtags = []
    enginePylons_enginePylon_volume_dimtags = []
    engine_nacelle_fanCowl_volume_dimtags = []
    engine_nacelle_coreCowl_volume_dimtags = []
    vehicles_engines_engine_volume_dimtags = []
    vehicles_rotorcraft_model_rotors_rotor_volume_dimtags = []

    log.info(f"Importing files from {brep_dir}")

    for brep_file in brep_files:
        # Import the part and create the aircraft part object
        part_entities = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs.tixi, part_obj.uid)

        if part_obj.part_type == "fuselage":
            fuselage_volume_dimtags.append(part_entities[0])
            model_bb = gmsh.model.get_bounding_box(
                fuselage_volume_dimtags[0][0], fuselage_volume_dimtags[0][1]
            )

            # return fuselage_volume_dimtags

        elif part_obj.part_type == "wing":
            wings_volume_dimtags.append(part_entities[0])
            # return wings_volume_dimtags

        elif part_obj.part_type == "enginePylons/enginePylon":
            enginePylons_enginePylon_volume_dimtags.append(part_entities[0])
            # return enginePylons_enginePylon_volume_dimtags

        elif part_obj.part_type == "engine/nacelle/fanCowl":
            engine_nacelle_fanCowl_volume_dimtags.append(part_entities[0])

        elif part_obj.part_type == "engine/nacelle/coreCowl":
            engine_nacelle_coreCowl_volume_dimtags.append(part_entities[0])

        elif part_obj.part_type == "vehicles/engines/engine":
            vehicles_engines_engine_volume_dimtags.append(part_entities[0])

        elif part_obj.part_type == "vehicles/rotorcraft/model/rotors/rotor":
            vehicles_rotorcraft_model_rotors_rotor_volume_dimtags.append(part_entities[0])

        # log.warning(f"'{brep_file}' cannot be categorized!")
        # return None

    gmsh.model.occ.synchronize()
    log.info("Manipulating the geometry, please wait..")

    # we have to obtain a wathertight
    gmsh.model.occ.cut(wings_volume_dimtags, fuselage_volume_dimtags, -1, True, False)

    gmsh.model.occ.synchronize()

    gmsh.model.occ.fuse(wings_volume_dimtags, fuselage_volume_dimtags, -1, True, True)

    gmsh.model.occ.synchronize()

    log.info("Manipulation finished")

    model_dimensions = [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]
    gmsh.model.occ.translate(
        [(3, 1)],
        -((model_bb[0]) + (model_dimensions[0] / 2)),
        -((model_bb[1]) + (model_dimensions[1] / 2)),
        -((model_bb[2]) + (model_dimensions[2] / 2)),
    )

    gmsh.model.occ.synchronize()

    aircraft_parts = gmsh.model.get_bounding_box(-1, -1)

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process")

    # Frontal-Delunay: 6   1: MeshAdapt, 2: Automatic, 3: Initial mesh only, 5: Delaunay, 6: Frontal-Delaunay, 7: BAMG, 8: Frontal-Delaunay for Quads, 9: Packing of Parallelograms, 11: Quasi-structured Quad
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    mesh_size = model_dimensions[0] * 0.005
    gmsh.option.set_number("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.set_number("Mesh.MeshSizeMax", mesh_size)
    gmsh.model.occ.synchronize()
    gmsh.logger.start()
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)

    if open_gmsh:
        log.info("Result of 2D surface mesh")
        log.info("GMSH GUI is open, close it to continue...")
        gmsh.fltk.run()

    # # Control of the mesh quality
    # if refine_factor != 1 and auto_refine:
    #     bad_surfaces = []

    #     for part in aircraft_parts:
    #         refined_surfaces, mesh_fields = refine_small_surfaces(
    #             mesh_fields,
    #             part,
    #             max(model_dimensions),
    #         )
    #         bad_surfaces.extend(refined_surfaces)

    #     if bad_surfaces:
    #         log.info(f"{len(bad_surfaces)} surface(s) need to be refined")

    #         # Reset the background mesh
    #         mesh_fields = min_fields(mesh_fields)

    #         if open_gmsh:
    #             log.info("Insufficient mesh size surfaces are displayed in red")
    #             log.info("GMSH GUI is open, close it to continue...")
    #             gmsh.fltk.run()

    #         log.info("Start of gmsh 2D surface remeshing process")

    #         gmsh.model.mesh.generate(1)
    #         gmsh.model.mesh.generate(2)

    #         for surface in bad_surfaces:
    #             gmsh.model.setColor([(2, surface)], *MESH_COLORS["good_surface"], recursive=False)

    #         log.info("Remeshing process finished")
    #         if open_gmsh:
    #             log.info("Corrected mesh surfaces are displayed in green")

    # # Apply smoothing
    # log.info("2D mesh smoothing process started")
    # gmsh.model.mesh.optimize("Laplace2D", niter=10)
    # log.info("Smoothing process finished")

    gmsh.model.occ.synchronize()

    # su2mesh_path = Path(results_dir, "mesh.su2")
    # gmsh.write(str(su2mesh_path))

    mesh_2d_path = Path(results_dir, "mesh_2d.stl")
    gmsh.write(str(mesh_2d_path))

    # process1.wait(20)

    # process2 = subprocess.Popen("paraview hybrid.cgns",
    #                             shell=True, cwd=results_dir, start_new_session=True)

    # process2.wait()

    if rotor_model:
        log.info("Duplicating disk actuator mesh surfaces")
        for part in aircraft_parts:
            if part.part_type == "rotor":
                duplicate_disk_actuator_surfaces(part)

        # option to use when duplicating disk actuator surfaces
        gmsh.option.setNumber("Mesh.SaveAll", 1)

        # Control surface orientation
        control_disk_actuator_normal()

    process_gmsh_log(gmsh.logger.get())

    if not testing_gmsh:
        gmsh.clear()
        gmsh.finalize()
    return mesh_2d_path, aircraft_parts


def pentagrow_3d_mesh(result_dir, Dimension: float) -> None:
    # create the config file for pentagrow
    config_penta_path = Path(result_dir, "config.cfg")
    # Variables
    InputFormat = "stl"
    NLayers = 25
    FeatureAngle = 120.0
    InitialHeight = 0.00003
    MaxLayerThickness = 1
    FarfieldRadius = Dimension * 20
    OutputFormat = "su2"
    HolePosition = "0.0 0.0 0.0"
    TetgenOptions = "-pq1.2VY"
    TetGrowthFactor = 1.35
    HeightIterations = 8
    NormalIterations = 8
    MaxCritIterations = 128
    LaplaceIterations = 8
    # writing to file
    file = open(config_penta_path, "w")
    file.write(f"InputFormat = {InputFormat}\n")
    file.write(f"NLayers = {NLayers}\n")
    file.write(f"FeatureAngle = {FeatureAngle}\n")
    file.write(f"InitialHeight = {InitialHeight}\n")
    file.write(f"MaxLayerThickness = {MaxLayerThickness}\n")
    file.write(f"FarfieldRadius = {FarfieldRadius}\n")
    file.write(f"OutputFormat = {OutputFormat}\n")
    file.write(f"HolePosition = {HolePosition}\n")
    file.write(f"TetgenOptions = {TetgenOptions}\n")
    file.write(f"TetGrowthFactor = {TetGrowthFactor}\n")
    file.write(f"HeightIterations = {HeightIterations}\n")
    file.write(f"NormalIterations = {NormalIterations}\n")
    file.write(f"MaxCritIterations = {MaxCritIterations}\n")
    file.write(f"LaplaceIterations = {LaplaceIterations}\n")
    file.close

    os.chdir("Results/GMSH")

    process = subprocess.run(
        "pentagrow mesh_2d.stl config.cfg", shell=True, cwd=result_dir, start_new_session=False
    )

    # run_software('pentagrow', ['mesh_2d.stl', 'config.cfg'], result_dir)
    # output, error = process1.communicate()

    mesh_3d_path = Path(result_dir, "hybrid.su2")

    return mesh_3d_path