"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'

Python version: >=3.8

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
from ceasiompy.CPACS2GMSH.func.wingclassification import get_entities_from_volume
from ceasiompy.SU2Run.func.utils import get_mesh_markers
from ceasiompy.utils.ceasiompyutils import remove_file_type_in_dir
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")
CPACS_IN_SIMPLE_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_engine.xml")
CPACS_IN_SIMPLE_DOUBLEFLUX_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_doubleflux_engine.xml")
CPACS_IN_PROPELLER_ENGINE_PATH = Path(CPACS_FILES_PATH, "simple_propeller.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_generate_gmsh():
    """
    This test try to generate a simple mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml
    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        tixi=cpacs.tixi,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=2,
        symmetry=False,
        farfield_size_factor=17,
        n_power_factor=2,
        n_power_field=0.9,
        fuselage_mesh_size_factor=1,
        wing_mesh_size_factor=1,
        mesh_size_engines=0.2,
        mesh_size_propellers=0.2,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=False,
    )

    mesh_markers = get_mesh_markers(Path(TEST_OUT_PATH, "mesh.su2"))
    assert mesh_markers["wall"] == ["SimpleFuselage", "Wing", "Wing_mirrored"]
    assert mesh_markers["farfield"] == ["Farfield"]

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


def test_generate_gmsh_symm():
    """
    This test try to generate a simple symmetric mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        tixi=cpacs.tixi,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=True,
        farfield_size_factor=17,
        n_power_factor=2,
        n_power_field=0.9,
        fuselage_mesh_size_factor=1,
        wing_mesh_size_factor=1,
        mesh_size_engines=0.5,
        mesh_size_propellers=0.5,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=False,
    )

    mesh_markers = get_mesh_markers(Path(TEST_OUT_PATH, "mesh.su2"))
    assert mesh_markers["wall"] == ["SimpleFuselage", "Wing"]
    assert mesh_markers["symmetry"] == ["symmetry"]
    assert mesh_markers["farfield"] == ["Farfield"]

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


def test_get_entities_from_volume():
    """
    Test on a simple cube if the lower dimensions entities are correctly found.
    """

    gmsh.initialize()
    test_cube = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    surfaces_dimtags, lines_dimtags, points_dimtags = get_entities_from_volume([(3, test_cube)])
    assert len(surfaces_dimtags) == 6
    assert len(lines_dimtags) == 12
    assert len(points_dimtags) == 8
    assert surfaces_dimtags == [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]
    assert lines_dimtags == [(1, i) for i in range(1, 13)]
    assert points_dimtags == [(0, i) for i in range(1, 9)]
    gmsh.clear()
    gmsh.finalize()


def test_ModelPart_associate_child_to_parent():
    """
    Test if the ModelPart associate_child_to_parent function works correctly.
    """

    gmsh.initialize()
    cube_child_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    model_part = ModelPart("cube_parent")
    model_part.associate_child_to_parent((3, cube_child_tag))

    # assert correct number of associated entities
    assert len(model_part.volume_tag) == 1
    assert len(model_part.surfaces_tags) == 6
    assert len(model_part.lines_tags) == 12
    assert len(model_part.points_tags) == 8

    gmsh.clear()
    gmsh.finalize()


def test_ModelPart_clean_inside_entities():
    """Test if the ModelPart clean_inside_entities function works correctly."""

    gmsh.initialize()
    final_domain_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    final_domain = ModelPart("fluid")
    final_domain.associate_child_to_parent((3, final_domain_tag))

    cube_child_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()

    model_part = ModelPart("cube_parent")
    model_part.associate_child_to_parent((3, cube_child_tag))
    model_part.clean_inside_entities(final_domain)

    # assert correct number of cleaned inside entities
    assert len(model_part.surfaces_tags) == 0
    assert len(model_part.lines_tags) == 0
    assert len(model_part.points_tags) == 0

    gmsh.clear()
    gmsh.finalize()


def test_define_engine_bc():
    """
    Test if the engine bc are correctly assigned

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_SIMPLE_ENGINE_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        tixi=cpacs.tixi,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=2,
        symmetry=False,
        farfield_size_factor=17,
        n_power_factor=2,
        n_power_field=0.9,
        fuselage_mesh_size_factor=1,
        wing_mesh_size_factor=1,
        mesh_size_engines=0.2,
        mesh_size_propellers=0.2,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=True,
    )
    physical_groups = gmsh.model.getPhysicalGroups(dim=-1)

    # Check if the engine integration did not disturb the BC assignation
    assert len(physical_groups) == 13

    assert gmsh.model.getPhysicalName(*physical_groups[0]) == "Pylon"
    assert gmsh.model.getPhysicalName(*physical_groups[1]) == "Pylon_mirrored"
    assert gmsh.model.getPhysicalName(*physical_groups[2]) == "SimpleEngine"
    assert gmsh.model.getPhysicalName(*physical_groups[3]) == "SimpleEngine_fan_In"
    assert gmsh.model.getPhysicalName(*physical_groups[4]) == "SimpleEngine_fan_Ex"
    assert gmsh.model.getPhysicalName(*physical_groups[5]) == "SimpleEngine_mirrored"
    assert gmsh.model.getPhysicalName(*physical_groups[6]) == "SimpleEngine_mirrored_fan_In"
    assert gmsh.model.getPhysicalName(*physical_groups[7]) == "SimpleEngine_mirrored_fan_Ex"
    assert gmsh.model.getPhysicalName(*physical_groups[8]) == "SimpleFuselage"
    assert gmsh.model.getPhysicalName(*physical_groups[9]) == "Wing"
    assert gmsh.model.getPhysicalName(*physical_groups[10]) == "Wing_mirrored"
    assert gmsh.model.getPhysicalName(*physical_groups[11]) == "Farfield"
    assert gmsh.model.getPhysicalName(*physical_groups[12]) == "fluid"

    # Check that the correct surfaces were assigned to the engine inlet outlet bc
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[3]) == [22]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[4]) == [21]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[6]) == [44]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[7]) == [43]

    # End gmsh api
    gmsh.clear()
    gmsh.finalize()

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


def test_define_doubleflux_engine_bc():
    """
    Test if doubleflux engine bc are correctly assigned
    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_SIMPLE_DOUBLEFLUX_ENGINE_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        tixi=cpacs.tixi,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=3,
        symmetry=False,
        farfield_size_factor=13,
        n_power_factor=2,
        n_power_field=0.9,
        fuselage_mesh_size_factor=1,
        wing_mesh_size_factor=1,
        mesh_size_engines=0.05,
        mesh_size_propellers=0.05,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=True,
    )
    physical_groups = gmsh.model.getPhysicalGroups(dim=-1)

    # Check if the engine integration did not disturb the BC assignation
    assert len(physical_groups) == 15

    assert gmsh.model.getPhysicalName(*physical_groups[3]) == "SimpleEngine_fan_In"
    assert gmsh.model.getPhysicalName(*physical_groups[4]) == "SimpleEngine_fan_Ex"
    assert gmsh.model.getPhysicalName(*physical_groups[5]) == "SimpleEngine_core_Ex"
    assert gmsh.model.getPhysicalName(*physical_groups[7]) == "SimpleEngine_mirrored_fan_In"
    assert gmsh.model.getPhysicalName(*physical_groups[8]) == "SimpleEngine_mirrored_fan_Ex"
    assert gmsh.model.getPhysicalName(*physical_groups[9]) == "SimpleEngine_mirrored_core_Ex"

    # Check that the correct surfaces were assigned to the engine inlet outlet bc
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[3]) == [22]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[4]) == [21]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[5]) == [39]

    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[7]) == [47]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[8]) == [46]
    assert gmsh.model.getEntitiesForPhysicalGroup(*physical_groups[9]) == [51]

    # End gmsh api
    gmsh.clear()
    gmsh.finalize()

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


def test_disk_actuator_conversion():
    """
    Test if disk actuator conversion is working on the simple_propeller.xml
    by testing the physical groups
    """
    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PROPELLER_ENGINE_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        tixi=cpacs.tixi,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=3,
        symmetry=False,
        farfield_size_factor=10,
        n_power_factor=2,
        n_power_field=0.9,
        fuselage_mesh_size_factor=0.5,
        wing_mesh_size_factor=0.1,
        mesh_size_engines=0.4,
        mesh_size_propellers=0.3,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=True,
    )

    physical_groups = gmsh.model.getPhysicalGroups()

    for tag, dim in physical_groups:
        print(f"tag {tag} dim {dim}")

    # Check if the disk actuator integration was correct
    print(physical_groups)
    assert len(physical_groups) == 11

    assert gmsh.model.getPhysicalName(*physical_groups[0]) == "Propeller_AD_Inlet"
    assert gmsh.model.getPhysicalName(*physical_groups[1]) == "Propeller_mirrored_AD_Inlet"
    assert gmsh.model.getPhysicalName(*physical_groups[8]) == "Propeller_AD_Outlet"
    assert gmsh.model.getPhysicalName(*physical_groups[9]) == "Propeller_mirrored_AD_Outlet"

    # End gmsh api
    gmsh.clear()
    gmsh.finalize()

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
