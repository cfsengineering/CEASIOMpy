"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'

| Author : Tony Govoni
| Creation: 2022-03-22

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
from pathlib import Path

import gmsh
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import (
    ModelPart,
    generate_gmsh,
)
from ceasiompy.CPACS2GMSH.func.rans_mesh_generator import (
    generate_2d_mesh_for_pentagrow,
    sort_surfaces_and_create_physical_groups,
    choose_correct_part,
    pentagrow_3d_mesh,

)
from ceasiompy.CPACS2GMSH.func.wingclassification import get_entities_from_volume
from ceasiompy.SU2Run.func.utils import get_mesh_markers
from ceasiompy.utils.ceasiompyutils import remove_file_type_in_dir
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from cpacspy.cpacspy import CPACS
from ceasiompy.CPACS2GMSH.func.utils import load_rans_cgf_params

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")
CPACS_IN_SIMPLE_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_engine.xml")
CPACS_IN_SIMPLE_DOUBLEFLUX_ENGINE_PATH = Path(
    CPACS_FILES_PATH, "simple_doubleflux_engine.xml")
CPACS_IN_PROPELLER_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_propeller.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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
        fuselage_mesh_size_factor=1,
        wing_mesh_size_factor=1,
        mesh_size_engines=0.2,
        mesh_size_propellers=0.2,
        auto_refine=False,
        farfield_size_factor=10
    )

    rans_cfg_params = load_rans_cgf_params(
        fuselage_maxlen=20,
        farfield_factor=10,
        n_layer=30,
        h_first_layer=0.00003,
        max_layer_thickness=1,
        growth_factor=1.2,
        growth_ratio=1.2,
        feature_angle=40,
    )

    pentagrow_3d_mesh(
        result_dir=TEST_OUT_PATH,
        cfg_params=rans_cfg_params,
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

    b1 = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    b2 = gmsh.model.occ.addBox(0.5, 0.5, 0.5, 1, 1, 1)
    fused = gmsh.model.occ.fuse([(3, b1)], [(3, b2)])
    gmsh.model.occ.synchronize()
    parts_in_b1 = [t for (d, t) in gmsh.model.getEntitiesInBoundingBox(
        -0.1, -0.1, -0.1, 1.1, 1.1, 1.1, 2)]
    parts_in_b2 = [t for (d, t) in gmsh.model.getEntitiesInBoundingBox(
        0.4, 0.4, 0.4, 1.6, 1.6, 1.6, 2)]
    all_surfaces = gmsh.model.getEntities(2)
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


def sort_surfaces_and_create_physical_groups():
    """
    This function tests if blabl
    """
    print("hello")


# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":
    # test_generate_rans_mesh()
    test_choose_correct_part()
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
