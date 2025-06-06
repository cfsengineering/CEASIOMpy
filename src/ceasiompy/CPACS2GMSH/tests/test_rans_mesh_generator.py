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

from ceasiompy.CPACS2GMSH.func.utils import load_rans_cgf_params
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.utils.ceasiompyutils import (
    remove_file_type_in_dir,
    get_part_type,
)
from ceasiompy.SU2Run.func.utils import get_mesh_markers
from ceasiompy.CPACS2GMSH.func.rans_mesh_generator import (
    generate_2d_mesh_for_pentagrow,
    sort_surfaces_and_create_physical_groups,
    choose_correct_part,
    pentagrow_3d_mesh,
)
from ceasiompy.CPACS2GMSH.func.generategmesh import (
    ModelPart,
)
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
import gmsh
import shutil
from pathlib import Path
import pyvista as pv

MODULE_DIR = Path(__file__).parent
BREP_IN_PATH = Path(MODULE_DIR, "ToolInput/brep_files_test_rans")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")
CPACS_D150_IN_PATH = Path(CPACS_FILES_PATH, "D150_simple.xml")


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
    all_lines = gmsh.model.getEntities(1)
    print("total lines", len(all_lines))
    all_surfaces = gmsh.model.getEntities(2)
    formatted_all = []
    for dim, tag in all_surfaces:
        bbb = gmsh.model.getBoundingBox(dim, tag)
        formatted_bbb = [f"{x:.2f}" for x in bbb]
        print(tag, " : ", formatted_bbb)
        formatted_all.append(formatted_bbb)
    print(formatted_all)
    gmsh.model.occ.synchronize()

    sort_surfaces_and_create_physical_groups(
        aircraft_parts, brep_files, cpacs, model_bb, model_dimensions)

    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)

    gmsh.model.mesh.field.add("Constant", 1)
    gmsh.model.mesh.field.setNumbers(1, "SurfacesList", [t for (d, t) in all_surfaces])
    gmsh.model.mesh.field.setNumber(1, "VIn", 0.4)
    gmsh.model.mesh.field.setAsBackgroundMesh(1)
    gmsh.model.mesh.generate(2)
    gmesh_path = Path(TEST_OUT_PATH, "surface_mesh.stl")
    gmsh.write(str(gmesh_path))
    test_holes(TEST_OUT_PATH)

    assert len(aircraft_parts[0].surfaces_tags) == 61  # fuselage
    assert len(aircraft_parts[1].surfaces_tags) == 8  # wing1
    assert len(aircraft_parts[2].surfaces_tags) == 8  # wing1_mirrored

    gmsh.finalize()

    remove_file_type_in_dir(TEST_OUT_PATH, [".brep", ".su2", ".cfg", ".stl"])


def create_interactive_plotter():
    """Create an interactive plotter with enhanced features."""
    plotter = pv.Plotter(
        notebook=False)  # Set notebook=False for external window

    # Enable advanced interactivity
    plotter.enable_terrain_style(mouse_wheel_zooms=True)
    # plotter.enable_anti_aliasing('msaa')  # Smooth rendering
    plotter.enable_parallel_projection()  # Useful for CAD models

    return plotter


def analyze_mesh(mesh, name="Mesh", depth=0):
    """Analyze a single mesh (non-MultiBlock)."""
    indent = "  " * depth
    print(f"\n{indent}🔍 Analyzing mesh: {name}")
    print(f"{indent}----------------------------------------")

    results = {
        'edges': None,
        'intersections': None,
        'bad_cells': None,
        'has_problems': False
    }

    try:
        # Basic info
        print(f"{indent}Number of points: {mesh.n_points}")
        print(f"{indent}Number of cells: {mesh.n_cells}")
        print(f"{indent}Mesh type: {type(mesh).__name__}")

        # Not really necessary for my purposes
        # 1. Check for holes
        results['edges'] = mesh.extract_feature_edges(
            boundary_edges=True,
            feature_edges=False,
            manifold_edges=False
        )
        print(f"{indent}🔎 Open edges (holes): {results['edges'].n_lines}")
        if results['edges'].n_lines > 0:
            results['has_problems'] = True

        # 2. Check self-intersections
        results['intersections'] = mesh.extract_feature_edges(
            boundary_edges=False,
            feature_edges=True,
            manifold_edges=False
        )
        print(
            f"{indent}⚠️ Self-intersections: {results['intersections'].n_lines}")
        if results['intersections'].n_lines > 0:
            results['has_problems'] = True

        # 3. Check cell quality
        if hasattr(mesh, 'compute_cell_quality'):
            quality = mesh.compute_cell_quality()
            if 'CellQuality' in quality.array_names:
                bad_cells = quality.threshold(
                    0, scalars='CellQuality', invert=True)
                results['bad_cells'] = bad_cells
                bad_count = bad_cells.n_cells if bad_cells else 0
                print(f"{indent}🚨 Degenerate cells: {bad_count}")
                if bad_count > 0:
                    results['has_problems'] = True
            else:
                print(f"{indent}ℹ️ No cell quality data available")

    except Exception as e:
        print(f"{indent}❌ Analysis error: {str(e)}")

    return results


def visualize_problems_interactive(mesh, results, name=""):
    """Interactive visualization with toggle controls for all elements."""
    if mesh is None or not results['has_problems']:
        return

    plotter = create_interactive_plotter()

    try:
        plotter.background_color = 'white'
        actors = {}  # Dictionary to store all actors

        # Add main mesh
        actors['main'] = plotter.add_mesh(
            mesh, style="wireframe", color="lightblue", opacity=0.7,
            label=f"{name} Original", smooth_shading=True, show_edges=True
        )

        # Add bad cells if they exist
        if results['bad_cells'] and results['bad_cells'].n_cells > 0:
            actors['bad_cells'] = plotter.add_mesh(
                results['bad_cells'], color="red",
                label=f"Degenerate cells ({results['bad_cells'].n_cells})",
                point_size=10, render_points_as_spheres=True
            )

        # Add intersections if they exist
        if results['intersections'] and results['intersections'].n_lines > 0:
            actors['intersections'] = plotter.add_mesh(
                results['intersections'], color="green", line_width=5,
                label=f"Self-intersections ({results['intersections'].n_lines})",
                render_lines_as_tubes=True
            )

        if results['edges']:
            actors['holes'] = plotter.add_mesh(
                results['edges'], color="pink", line_width=5,
                label=f"Holes ({results['edges'].n_lines})",
                render_lines_as_tubes=True
            )

        # Add y=0 cutting plane
        y_plane = mesh.slice(normal=[0, 1, 0], origin=[0, 0, 0])
        actors['y_plane'] = plotter.add_mesh(
            y_plane, color="orange", opacity=0.5,
            label="Y=0 Cut Plane", show_edges=True
        )
        actors['y_plane'].SetVisibility(False)  # Start with plane hidden

        # Create toggle functions for each element
        def toggle_main_mesh(flag):
            actors['main'].SetVisibility(flag)
            plotter.render()

        def toggle_holes(flag):
            if 'holes' in actors:
                actors['holes'].SetVisibility(flag)
                plotter.render()

        def toggle_bad_cells(flag):
            if 'bad_cells' in actors:
                actors['bad_cells'].SetVisibility(flag)
                plotter.render()

        def toggle_intersections(flag):
            if 'intersections' in actors:
                actors['intersections'].SetVisibility(flag)
                plotter.render()

        def toggle_y_plane(flag):
            if 'y_plane' in actors:
                actors['y_plane'].SetVisibility(flag)
                plotter.render()

        # Add toggle buttons in a vertical column
        button_y = 10  # Starting Y position
        button_size = 25
        x_pos = 10

        # Main mesh toggle
        plotter.add_checkbox_button_widget(
            toggle_main_mesh,
            value=True,
            position=(x_pos, button_y),
            size=button_size,
            color_on='blue',
            color_off='gray'
        )
        plotter.add_text("Main Mesh", position=(x_pos + 30, button_y - 5),
                         color='black', font_size=12)
        button_y += 30

        # Bad cells toggle
        if 'bad_cells' in actors:
            plotter.add_checkbox_button_widget(
                toggle_bad_cells,
                value=True,
                position=(x_pos, button_y),
                size=button_size,
                color_on='red',
                color_off='gray'
            )
            plotter.add_text("Bad Cells", position=(x_pos + 30, button_y - 5),
                             color='black', font_size=12)
            button_y += 30

        # Intersections toggle
        if 'intersections' in actors:
            plotter.add_checkbox_button_widget(
                toggle_intersections,
                value=True,
                position=(x_pos, button_y),
                size=button_size,
                color_on='green',
                color_off='gray'
            )
            plotter.add_text("Intersections", position=(x_pos + 30, button_y - 5),
                             color='black', font_size=12)
            button_y += 30

        # Holes toggle
        if 'holes' in actors:
            plotter.add_checkbox_button_widget(
                toggle_holes,
                value=True,
                position=(x_pos, button_y),
                size=button_size,
                color_on='pink',
                color_off='gray'
            )
            plotter.add_text("Open edges (holes)", position=(x_pos + 30, button_y - 5),
                             color='black', font_size=12)
            button_y += 30

        # Y-plane toggle
        plotter.add_checkbox_button_widget(
            toggle_y_plane,
            value=False,  # Start with plane hidden
            position=(x_pos, button_y),
            size=button_size,
            color_on='yellow',
            color_off='gray'
        )
        plotter.add_text("Y=0 Plane", position=(x_pos + 30, button_y - 5),
                         color='black', font_size=12)

        # Add axes and legend
        plotter.add_axes(interactive=True)
        plotter.add_legend(bcolor='white', size=(0.2, 0.2))

        # Start interactive mode
        plotter.show(title=f"Mesh Analysis: {name}")

    except Exception as e:
        print(f"❌ Visualization error: {str(e)}")
        plotter.close()


def process_block(block, name="", depth=0):
    """Process a single block (mesh or MultiBlock)."""
    if block is None:
        return

    if isinstance(block, pv.MultiBlock):
        print(f"\n{'  '*depth}📦 Found MultiBlock '{name}' with {len(block)} blocks")
        for i, sub_block in enumerate(block):
            process_block(sub_block, name=f"{name}-{i}", depth=depth + 1)
    else:
        results = analyze_mesh(block, name=name, depth=depth)
        visualize_problems_interactive(block, results, name)


def test_holes(stlfilepath):
    """Main function."""
    try:
        # Load file
        reader = pv.STLReader(Path(stlfilepath, "surface_mesh.stl"))
        reader.load_boundary_patch = False
        main_mesh = reader.read()

        if isinstance(main_mesh, pv.MultiBlock):
            print(
                f"🔷 File contains MultiBlock structure with {len(main_mesh)} main blocks")
            for i, block in enumerate(main_mesh):
                process_block(block, name=f"Block {i}")
        else:
            results = analyze_mesh(main_mesh)
            visualize_problems_interactive(main_mesh, results)

    except Exception as e:
        print(f"❌ Critical error: {str(e)}")


# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":
    # test_generate_rans_mesh()
    test_choose_correct_part()
    test_sort_surfaces_and_create_physical_groups()
