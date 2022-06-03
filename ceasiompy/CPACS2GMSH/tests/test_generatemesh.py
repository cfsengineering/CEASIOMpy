"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'

Python version: >=3.7

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
    get_entities_from_volume,
)
from ceasiompy.SU2Run.func.su2utils import get_mesh_markers
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
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        mesh_size_engines=0.5,
        mesh_size_propellers=0.5,
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
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=True,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
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


def test_assignation():
    """
    Test if the assignation mechanism is correct on all parts
    test if the assignation of the entities of wing1 is correct
    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    _, aircraft_parts = generate_gmsh(
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        mesh_size_engines=0.5,
        mesh_size_propellers=0.5,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=False,
    )

    fuselage1_child = set([(3, 2)])
    wing1_m_child = set([(3, 5)])

    wing1_child = set([(3, 3)])
    wing1_volume_tag = [3]
    wing1_surfaces_tags = [5, 6, 7, 12, 13, 14, 19]
    wing1_lines_tags = [7, 8, 9, 15, 16, 17, 18, 19, 20, 29, 30, 31, 32, 33, 34]
    wing1_points_tags = [5, 6, 7, 12, 13, 14, 19, 20, 21]

    for part in aircraft_parts:
        if part.uid == "Wing_mirrored":
            assert part.children_dimtag == wing1_m_child
        if part.uid == "SimpleFuselage":
            assert part.children_dimtag == fuselage1_child
        if part.uid == "Wing":
            assert part.children_dimtag == wing1_child
            assert part.volume_tag == wing1_volume_tag
            assert part.surfaces_tags == wing1_surfaces_tags
            assert part.lines_tags == wing1_lines_tags
            assert part.points_tags == wing1_points_tags

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg"])


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
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=2,
        symmetry=False,
        mesh_size_farfield=2,
        mesh_size_fuselage=0.2,
        mesh_size_wings=0.2,
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
    assert gmsh.model.getPhysicalName(*physical_groups[3]) == "SimpleEngine_fan_Intake"
    assert gmsh.model.getPhysicalName(*physical_groups[4]) == "SimpleEngine_fan_Exhaust"
    assert gmsh.model.getPhysicalName(*physical_groups[5]) == "SimpleEngine_mirrored"
    assert gmsh.model.getPhysicalName(*physical_groups[6]) == "SimpleEngine_mirrored_fan_Intake"
    assert gmsh.model.getPhysicalName(*physical_groups[7]) == "SimpleEngine_mirrored_fan_Exhaust"
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
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=2,
        symmetry=False,
        mesh_size_farfield=2,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.05,
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

    assert gmsh.model.getPhysicalName(*physical_groups[3]) == "SimpleEngine_fan_Intake"
    assert gmsh.model.getPhysicalName(*physical_groups[4]) == "SimpleEngine_fan_Exhaust"
    assert gmsh.model.getPhysicalName(*physical_groups[5]) == "SimpleEngine_core_Exhaust"
    assert gmsh.model.getPhysicalName(*physical_groups[7]) == "SimpleEngine_mirrored_fan_Intake"
    assert gmsh.model.getPhysicalName(*physical_groups[8]) == "SimpleEngine_mirrored_fan_Exhaust"
    assert gmsh.model.getPhysicalName(*physical_groups[9]) == "SimpleEngine_mirrored_core_Exhaust"

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
        cpacs=cpacs,
        brep_dir=TEST_OUT_PATH,
        results_dir=TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        mesh_size_engines=0.5,
        mesh_size_propellers=0.5,
        refine_factor=1.0,
        refine_truncated=False,
        auto_refine=False,
        testing_gmsh=True,
    )

    physical_groups = gmsh.model.getPhysicalGroups(dim=-1)

    # Check if the disk actuator integration was correct
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
