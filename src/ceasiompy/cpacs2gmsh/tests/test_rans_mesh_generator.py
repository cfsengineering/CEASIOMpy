"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'

| Author : Tony Govoni
| Creation: 2022-03-22

"""

# Imports

from cpacspy.cpacspy import CPACS
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.ceasiompyutils import (
    remove_file_type_in_dir,
    get_part_type,
)
from ceasiompy.su2run.func.utils import get_mesh_markers
from ceasiompy.cpacs2gmsh.func.rans_mesh_generator import (
    generate_2d_mesh_for_pentagrow,
    sort_surfaces_and_create_physical_groups,
    choose_correct_part,
    pentagrow_3d_mesh,
)
from ceasiompy.cpacs2gmsh.func.generategmesh import (
    ModelPart,
)
from ceasiompy.cpacs2gmsh.func.exportbrep import export_brep
import gmsh
import shutil
from pathlib import Path

MODULE_DIR = Path(__file__).parent
BREP_IN_PATH = Path(MODULE_DIR, "ToolInput/brep_files_test_rans")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")
CPACS_D150_IN_PATH = Path(CPACS_FILES_PATH, "d150.xml")
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")


# Functions

def test_generate_rans_mesh():
    """
    This test try to generate a simple RANS mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml
    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_2d_mesh_for_pentagrow(
        cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        refine_factor=2,
        refine_truncated=True,
        refine_factor_angled_lines=1.5,
        fuselage_mesh_size_factor=0.7,
        wing_mesh_size_factor=0.8,
        mesh_size_engines=0.2,
        mesh_size_propellers=0.2,
        auto_refine=False,
        farfield_size_factor=10,
        symmetry=False,
    )

    pentagrow_3d_mesh(
        result_dir=str(TEST_OUT_PATH),
        fuselage_maxlen=20,
        farfield_factor=10,
        n_layer=30,
        h_first_layer=0.00003,
        max_layer_thickness=1,
        growth_factor=1.2,
        growth_ratio=1.2,
        feature_angle=40,
        symmetry=False,
        output_format="su2",
        surf=None,
        angle=None,
    )

    mesh_markers = get_mesh_markers(Path(TEST_OUT_PATH, "hybrid.su2"))
    assert mesh_markers["wall"] == ["SimpleFuselage", "Wing", "Wing_mirrored"]
    assert mesh_markers["farfield"] == ["Farfield"]

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


def test_choose_correct_part():
    """
    This test try to sort surfaces to the right part they belong in with
    the function choose_correct_part.
    """
    gmsh.initialize()
    gmsh.clear()

    b1 = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    b2 = gmsh.model.occ.addBox(0.5, 0.5, 0.5, 1, 1, 1)
    gmsh.model.occ.fuse([(3, b1)], [(3, b2)])
    gmsh.model.occ.synchronize()
    all_surfaces = gmsh.model.getEntities(2)
    parts_in_b1 = [t for (d, t) in gmsh.model.getEntitiesInBoundingBox(
        -0.1, -0.1, -0.1, 1.1, 1.1, 1.1, 2)]
    parts_in_b2 = [t for (d, t) in gmsh.model.getEntitiesInBoundingBox(
        0.4, 0.4, 0.4, 1.6, 1.6, 1.6, 2)]

    b1new = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    b2new = gmsh.model.occ.addBox(0.5, 0.5, 0.5, 1, 1, 1)

    modelpart_b1 = ModelPart("b1")
    modelpart_b1.surfaces_tags = [tag for (dim, tag) in all_surfaces]
    modelpart_b1.surfaces = all_surfaces
    new_modelpart_b1 = ModelPart("b1_new")
    new_modelpart_b1.volume = (3, b1new)

    modelpart_b2 = ModelPart("b2")
    modelpart_b2.surfaces_tags = [tag for (dim, tag) in all_surfaces]
    modelpart_b2.surfaces = all_surfaces
    new_modelpart_b2 = ModelPart("b2_new")
    new_modelpart_b2.volume = (3, b2new)

    all_surfaces_notmodified = all_surfaces.copy()
    for surf_dimtag in all_surfaces_notmodified:
        choose_correct_part([0, 1], surf_dimtag[1], [modelpart_b1, modelpart_b2],
                            [new_modelpart_b1, new_modelpart_b2])

    assert parts_in_b1 == modelpart_b1.surfaces_tags
    assert parts_in_b2 == modelpart_b2.surfaces_tags

    gmsh.finalize()


def test_sort_surfaces_and_create_physical_groups():
    """
    This function tests if the function sort_surfaces_and_create_physical_groups
    sorts the surfaces that are between fuselage and wing in D150 (known "problem").
    """
    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    brep_files = list(BREP_IN_PATH.glob("*.brep"))
    brep_files.sort()
    cpacs = CPACS(CPACS_D150_IN_PATH)

    gmsh.initialize()
    gmsh.clear()

    aircraft_parts = []
    vols = []
    for brep_file in brep_files:
        # Import the part and create the aircraft part object
        part_entities = gmsh.model.occ.importShapes(
            str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs.tixi, part_obj.uid)
        part_obj.volume = part_entities[0]
        part_obj.volume_tag = part_entities[0][1]
        vols.append(part_entities[0][1])

        aircraft_parts.append(part_obj)

    model_bb = gmsh.model.get_bounding_box(*aircraft_parts[0].volume)
    model_dimensions = [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]
    all_volumes = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        all_volumes,
        -((model_bb[0]) + (model_dimensions[0] / 2)),
        -((model_bb[1]) + (model_dimensions[1] / 2)),
        -((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()

    for model_part in aircraft_parts:
        bb = gmsh.model.get_bounding_box(*model_part.volume)
        model_part.bounding_box = [bb[0] - 0.1, bb[1] - 0.1,
                                   bb[2] - 0.1, bb[3] + 0.1, bb[4] + 0.1, bb[5] + 0.1]

    gmsh.model.occ.fuse([(3, vols[0])], [(3, vols[1]), (3, vols[2])])
    gmsh.model.occ.synchronize()

    sort_surfaces_and_create_physical_groups(
        aircraft_parts, brep_files, cpacs, model_bb, model_dimensions, symmetry=False)

    # Test if there are the right number of surfaces in each part of the aircraft
    assert len(aircraft_parts[0].surfaces_tags) == 60  # fuselage
    assert len(aircraft_parts[1].surfaces_tags) == 8  # wing1
    assert len(aircraft_parts[2].surfaces_tags) == 8  # wing1_mirrored

    gmsh.finalize()

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg", ".stl"])


# Main
if __name__ == "__main__":
    test_generate_rans_mesh()
