"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 2D airfoil mesh generation with gmshairfoil2d
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
import shutil

from pathlib import Path

from cpacspy.cpacsfunctions import create_branch
from gmshairfoil2d.airfoil_func import NACA_4_digit_geom
from ceasiompy.utils.cpacs_utils import create_minimal_cpacs_2d
from ceasiompy.CPACS2GMSH.func.airfoil2d import process_2d_airfoil

from ceasiompy.utils.cpacs_utils import SimpleCPACS

MODULE_DIR = Path(__file__).parent
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput_2D")

# =================================================================================================
#   FIXTURES
# =================================================================================================


@pytest.fixture
def test_output_dir():
    """Create and clean test output directory"""
    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()
    yield TEST_OUT_PATH
    # Cleanup after test
    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)


@pytest.fixture
def naca_2d_cpacs(test_output_dir):
    """Create a minimal 2D CPACS file with NACA airfoil configuration"""
    cpacs_path = test_output_dir / "test_2d_naca.xml"
    tixi = create_minimal_cpacs_2d(cpacs_path, "Test NACA 0012")

    # Add NACA airfoil configuration
    geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
    create_branch(tixi, geom_xpath + "/airfoilType")
    tixi.updateTextElement(geom_xpath + "/airfoilType", "NACA")
    create_branch(tixi, geom_xpath + "/airfoilCode")
    tixi.updateTextElement(geom_xpath + "/airfoilCode", "0012")

    # Add mesh parameters
    mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
    create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
    create_branch(tixi, mesh_xpath + "/externalMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldRadius")
    tixi.updateDoubleElement(mesh_xpath + "/farfieldRadius", 10.0, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldType")
    tixi.updateTextElement(mesh_xpath + "/farfieldType", "Circular")
    create_branch(tixi, mesh_xpath + "/structuredMesh")
    tixi.updateTextElement(mesh_xpath + "/structuredMesh", "False")
    create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
    tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "False")
    create_branch(tixi, mesh_xpath + "/firstLayerHeight")
    tixi.updateDoubleElement(mesh_xpath + "/firstLayerHeight", 0.001, "%g")
    create_branch(tixi, mesh_xpath + "/growthRatio")
    tixi.updateDoubleElement(mesh_xpath + "/growthRatio", 1.2, "%g")
    create_branch(tixi, mesh_xpath + "/numberOfLayers")
    tixi.updateIntegerElement(mesh_xpath + "/numberOfLayers", 25, "%d")
    create_branch(tixi, mesh_xpath + "/meshFormat")
    tixi.updateTextElement(mesh_xpath + "/meshFormat", "su2")

    tixi.save(str(cpacs_path), True)
    tixi.close()

    return SimpleCPACS(str(cpacs_path))


# =================================================================================================
#   TESTS
# =================================================================================================


def test_process_2d_naca_circular_farfield(naca_2d_cpacs, test_output_dir):
    """
    Test 2D mesh generation with NACA airfoil and circular farfield.
    Verify that mesh file is created successfully.
    """
    process_2d_airfoil(naca_2d_cpacs, test_output_dir)

    # Check that mesh file was created
    expected_mesh = test_output_dir / "mesh_airfoil_0012.su2"
    assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"
    assert expected_mesh.stat().st_size > 0, "Mesh file is empty"


def test_process_2d_rectangular_farfield(test_output_dir):
    """
    Test 2D mesh generation with rectangular farfield.
    """
    cpacs_path = test_output_dir / "test_2d_rect.xml"
    tixi = create_minimal_cpacs_2d(cpacs_path, "Test NACA 2412 Rectangular")

    # Add NACA airfoil configuration
    geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
    create_branch(tixi, geom_xpath + "/airfoilType")
    tixi.updateTextElement(geom_xpath + "/airfoilType", "NACA")
    create_branch(tixi, geom_xpath + "/airfoilCode")
    tixi.updateTextElement(geom_xpath + "/airfoilCode", "2412")

    # Add mesh parameters with rectangular farfield
    mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
    create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
    create_branch(tixi, mesh_xpath + "/externalMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldType")
    tixi.updateTextElement(mesh_xpath + "/farfieldType", "Rectangular")
    create_branch(tixi, mesh_xpath + "/length")
    tixi.updateDoubleElement(mesh_xpath + "/length", 5.0, "%g")
    create_branch(tixi, mesh_xpath + "/heightLength")
    tixi.updateDoubleElement(mesh_xpath + "/heightLength", 5.0, "%g")
    create_branch(tixi, mesh_xpath + "/structuredMesh")
    tixi.updateTextElement(mesh_xpath + "/structuredMesh", "False")
    create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
    tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "True")
    create_branch(tixi, mesh_xpath + "/meshFormat")
    tixi.updateTextElement(mesh_xpath + "/meshFormat", "su2")

    tixi.save(str(cpacs_path), True)
    tixi.close()

    cpacs = SimpleCPACS(str(cpacs_path))
    process_2d_airfoil(cpacs, test_output_dir)

    # Check that mesh file was created
    expected_mesh = test_output_dir / "mesh_airfoil_2412.su2"
    assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"


def test_process_2d_ctype_farfield_structured(test_output_dir):
    """
    Test 2D mesh generation with C-type farfield and structured mesh.
    """
    cpacs_path = test_output_dir / "test_2d_ctype.xml"
    tixi = create_minimal_cpacs_2d(cpacs_path, "Test NACA 4412 CType")

    # Add NACA airfoil configuration
    geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
    create_branch(tixi, geom_xpath + "/airfoilType")
    tixi.updateTextElement(geom_xpath + "/airfoilType", "NACA")
    create_branch(tixi, geom_xpath + "/airfoilCode")
    tixi.updateTextElement(geom_xpath + "/airfoilCode", "4412")

    # Add mesh parameters with CType farfield and structured mesh
    mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
    create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
    create_branch(tixi, mesh_xpath + "/externalMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldType")
    tixi.updateTextElement(mesh_xpath + "/farfieldType", "CType")
    create_branch(tixi, mesh_xpath + "/wakeLength")
    tixi.updateDoubleElement(mesh_xpath + "/wakeLength", 6.0, "%g")
    create_branch(tixi, mesh_xpath + "/heightLength")
    tixi.updateDoubleElement(mesh_xpath + "/heightLength", 5.0, "%g")
    create_branch(tixi, mesh_xpath + "/structuredMesh")
    tixi.updateTextElement(mesh_xpath + "/structuredMesh", "True")
    create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
    tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "False")
    create_branch(tixi, mesh_xpath + "/firstLayerHeight")
    tixi.updateDoubleElement(mesh_xpath + "/firstLayerHeight", 0.001, "%g")
    create_branch(tixi, mesh_xpath + "/growthRatio")
    tixi.updateDoubleElement(mesh_xpath + "/growthRatio", 1.2, "%g")
    create_branch(tixi, mesh_xpath + "/numberOfLayers")
    tixi.updateIntegerElement(mesh_xpath + "/numberOfLayers", 25, "%d")
    create_branch(tixi, mesh_xpath + "/meshFormat")
    tixi.updateTextElement(mesh_xpath + "/meshFormat", "su2")

    tixi.save(str(cpacs_path), True)
    tixi.close()

    cpacs = SimpleCPACS(str(cpacs_path))
    process_2d_airfoil(cpacs, test_output_dir)

    # Check that mesh file was created
    expected_mesh = test_output_dir / "mesh_airfoil_4412.su2"
    assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"


def test_process_2d_different_mesh_formats(test_output_dir):
    """
    Test 2D mesh generation with different output formats.
    Creates a fresh CPACS for each format to avoid ALREADY_SAVED errors.
    """
    formats = ["su2", "msh", "vtk"]

    for mesh_format in formats:
        # Create fresh CPACS for each format
        cpacs_path = test_output_dir / f"test_2d_{mesh_format}.xml"
        tixi = create_minimal_cpacs_2d(cpacs_path, f"Test NACA 0012 {mesh_format}")

        # Add NACA airfoil configuration
        geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
        create_branch(tixi, geom_xpath + "/airfoilType")
        tixi.updateTextElement(geom_xpath + "/airfoilType", "NACA")
        create_branch(tixi, geom_xpath + "/airfoilCode")
        tixi.updateTextElement(geom_xpath + "/airfoilCode", "0012")

        # Add mesh parameters
        mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
        create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
        tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
        create_branch(tixi, mesh_xpath + "/externalMeshSize")
        tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
        create_branch(tixi, mesh_xpath + "/farfieldRadius")
        tixi.updateDoubleElement(mesh_xpath + "/farfieldRadius", 10.0, "%g")
        create_branch(tixi, mesh_xpath + "/farfieldType")
        tixi.updateTextElement(mesh_xpath + "/farfieldType", "Circular")
        create_branch(tixi, mesh_xpath + "/structuredMesh")
        tixi.updateTextElement(mesh_xpath + "/structuredMesh", "False")
        create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
        tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "False")
        create_branch(tixi, mesh_xpath + "/firstLayerHeight")
        tixi.updateDoubleElement(mesh_xpath + "/firstLayerHeight", 0.001, "%g")
        create_branch(tixi, mesh_xpath + "/growthRatio")
        tixi.updateDoubleElement(mesh_xpath + "/growthRatio", 1.2, "%g")
        create_branch(tixi, mesh_xpath + "/numberOfLayers")
        tixi.updateIntegerElement(mesh_xpath + "/numberOfLayers", 25, "%d")
        create_branch(tixi, mesh_xpath + "/meshFormat")
        tixi.updateTextElement(mesh_xpath + "/meshFormat", mesh_format)

        tixi.save(str(cpacs_path), True)
        tixi.close()

        # Generate mesh
        cpacs = SimpleCPACS(str(cpacs_path))
        process_2d_airfoil(cpacs, test_output_dir)

        # Check that mesh file with correct format was created
        expected_mesh = test_output_dir / f"mesh_airfoil_0012.{mesh_format}"
        assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"

        # Clean up for next iteration
        if expected_mesh.exists():
            expected_mesh.unlink()


def test_process_2d_no_boundary_layer(test_output_dir):
    """
    Test 2D mesh generation without boundary layer.
    """
    tixi = create_minimal_cpacs_2d("Test NACA 0012 No BL")

    # Add NACA airfoil configuration
    geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
    create_branch(tixi, geom_xpath + "/airfoilType")
    tixi.updateTextElement(geom_xpath + "/airfoilType", "NACA")
    create_branch(tixi, geom_xpath + "/airfoilCode")
    tixi.updateTextElement(geom_xpath + "/airfoilCode", "0012")

    # Add mesh parameters without boundary layer
    mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
    create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
    create_branch(tixi, mesh_xpath + "/externalMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldRadius")
    tixi.updateDoubleElement(mesh_xpath + "/farfieldRadius", 10.0, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldType")
    tixi.updateTextElement(mesh_xpath + "/farfieldType", "Circular")
    create_branch(tixi, mesh_xpath + "/structuredMesh")
    tixi.updateTextElement(mesh_xpath + "/structuredMesh", "False")
    create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
    tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "True")
    create_branch(tixi, mesh_xpath + "/meshFormat")
    tixi.updateTextElement(mesh_xpath + "/meshFormat", "su2")

    tixi.save(str(cpacs_path), True)
    tixi.close()

    cpacs = SimpleCPACS(str(cpacs_path))
    process_2d_airfoil(cpacs, test_output_dir)

    # Check that mesh file was created
    expected_mesh = test_output_dir / "mesh_airfoil_0012.su2"
    assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"


def test_process_2d_custom_airfoil(test_output_dir):
    """
    Test 2D mesh generation with custom airfoil file.
    Uses NACA 2412 coordinates from gmshairfoil2d database saved as custom file.
    """
    # Create custom airfoil file using known NACA 2412 profile
    profiles_dir = test_output_dir / "profiles"
    profiles_dir.mkdir()
    airfoil_file = profiles_dir / "airfoil_test2412.dat"

    # Generate NACA 2412 coordinates using gmshairfoil2d

    coords = NACA_4_digit_geom("2412", nb_points=100)

    with open(airfoil_file, "w") as f:
        f.write("test2412\n")
        for point in coords:
            f.write(f"{point[0]:.8f} {point[1]:.8f}\n")

    # Create CPACS with custom airfoil reference
    tixi = create_minimal_cpacs_2d("Test Custom Airfoil")

    # Add custom airfoil to wingAirfoils
    airfoils_xpath = "/cpacs/vehicles/profiles/wingAirfoils"
    create_branch(tixi, airfoils_xpath)
    tixi.createElement(airfoils_xpath, "wingAirfoil")
    airfoil_xpath = f"{airfoils_xpath}/wingAirfoil[1]"
    tixi.addTextAttribute(airfoil_xpath, "uID", "airfoil_test2412")
    create_branch(tixi, airfoil_xpath + "/name")
    tixi.updateTextElement(airfoil_xpath + "/name", "test2412")
    create_branch(tixi, airfoil_xpath + "/pointList/file")
    tixi.updateTextElement(airfoil_xpath + "/pointList/file", str(airfoil_file))

    # Add custom airfoil configuration
    geom_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry"
    create_branch(tixi, geom_xpath + "/airfoilType")
    tixi.updateTextElement(geom_xpath + "/airfoilType", "Custom")
    create_branch(tixi, geom_xpath + "/airfoilName")
    tixi.updateTextElement(geom_xpath + "/airfoilName", "test2412")

    # Add mesh parameters
    mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/mesh/gmshOptions/airfoil2D"
    create_branch(tixi, mesh_xpath + "/airfoilMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/airfoilMeshSize", 0.01, "%g")
    create_branch(tixi, mesh_xpath + "/externalMeshSize")
    tixi.updateDoubleElement(mesh_xpath + "/externalMeshSize", 0.2, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldRadius")
    tixi.updateDoubleElement(mesh_xpath + "/farfieldRadius", 10.0, "%g")
    create_branch(tixi, mesh_xpath + "/farfieldType")
    tixi.updateTextElement(mesh_xpath + "/farfieldType", "Circular")
    create_branch(tixi, mesh_xpath + "/structuredMesh")
    tixi.updateTextElement(mesh_xpath + "/structuredMesh", "False")
    create_branch(tixi, mesh_xpath + "/noBoundaryLayer")
    tixi.updateTextElement(mesh_xpath + "/noBoundaryLayer", "True")
    create_branch(tixi, mesh_xpath + "/meshFormat")
    tixi.updateTextElement(mesh_xpath + "/meshFormat", "su2")

    tixi.save(str(cpacs_path), True)
    tixi.close()

    cpacs = SimpleCPACS(str(cpacs_path))
    process_2d_airfoil(cpacs, test_output_dir)

    # Check that mesh file was created (should be renamed without double airfoil_ prefix)
    expected_mesh = test_output_dir / "mesh_airfoil_test2412.su2"
    assert expected_mesh.exists(), f"Mesh file not found: {expected_mesh}"


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
