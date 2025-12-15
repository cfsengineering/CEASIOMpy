import pyvista as pv

from ceasiompy import log

def create_interactive_plotter():
    """Create an interactive plotter with enhanced features."""
    plotter = pv.Plotter(notebook=False)  # Set notebook=False for external window
    
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

        # Not really necessary for my purpouses
        # 1. Check for holes
        # results['edges'] = mesh.extract_feature_edges(
        #     boundary_edges=True,
        #     feature_edges=False,
        #     manifold_edges=False
        # )
        # print(f"{indent}🔎 Open edges (holes): {results['edges'].n_lines}")
        # if results['edges'].n_lines > 0:
        #     results['has_problems'] = True
        
        # 2. Check self-intersections
        results['intersections'] = mesh.extract_feature_edges(
            boundary_edges=False,
            feature_edges=True,
            manifold_edges=False
        )
        print(f"{indent}⚠️ Self-intersections: {results['intersections'].n_lines}")
        if results['intersections'].n_lines > 0:
            results['has_problems'] = True
        
        # 3. Check cell quality
        if hasattr(mesh, 'compute_cell_quality'):
            quality = mesh.compute_cell_quality()
            if 'CellQuality' in quality.array_names:
                bad_cells = quality.threshold(0, scalars='CellQuality', invert=True)
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
        
        # Add y=0 cutting plane
        y_plane = mesh.slice(normal=[0,1,0], origin=[0,0,0])
        actors['y_plane'] = plotter.add_mesh(
            y_plane, color="orange", opacity=0.5,
            label="Y=0 Cut Plane", show_edges=True
        )
        actors['y_plane'].SetVisibility(False)  # Start with plane hidden
        
        # Create toggle functions for each element
        def toggle_main_mesh(flag):
            actors['main'].SetVisibility(flag)
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
            process_block(sub_block, name=f"{name}-{i}", depth=depth+1)
    else:
        results = analyze_mesh(block, name=name, depth=depth)
        visualize_problems_interactive(block, results, name)

def main():
    """Main function."""
    try:
        # Load file
        reader = pv.CGNSReader("/home/benedetti/surface_mesh_generator/surface_mesh_generator_cassandre/Breps/brep_file_D150/hybrid.cgns")
        reader.load_boundary_patch = False
        main_mesh = reader.read()
        
        if isinstance(main_mesh, pv.MultiBlock):
            print(f"🔷 File contains MultiBlock structure with {len(main_mesh)} main blocks")
            for i, block in enumerate(main_mesh):
                process_block(block, name=f"Block {i}")
        else:
            results = analyze_mesh(main_mesh)
            visualize_problems_interactive(main_mesh, results)
            
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")

if __name__ == "__main__":
    main()