"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import shutil
import subprocess

from ceasiompy.utils.ceasiompyutils import (
    run_software,
    get_install_path,
    get_sane_max_cpu,
)

from pathlib import Path
from ceasiompy.cpacs2gmsh.utility.utils import (
    MeshSettings,
    FarfieldSettings,
    BoundaryLayerSettings,
)

from ceasiompy.cpacs2gmsh import SOFTWARE_NAME


# Methods

def _load_rans_cgf_params(
    output_format: str,
    mesh_settings: MeshSettings,
    surface_mesh_path: Path,
    volume_mesh_settings: FarfieldSettings,
    boundary_layer_settings: BoundaryLayerSettings,
) -> dict[str, str]:
    return {
        "InputFormat": f"{surface_mesh_path.suffix}",
        "NLayers": str(boundary_layer_settings.n_layer),
        "FeatureAngle": str(boundary_layer_settings.feature_angle),
        "InitialHeight": str(boundary_layer_settings.h_first_layer),
        "MaxGrowthRatio": str(boundary_layer_settings.growth_ratio),
        "MaxLayerThickness": str(boundary_layer_settings.max_layer_thickness),
        "FarfieldRadius": str(volume_mesh_settings.farfield_radius),
        "OutputFormat": str(output_format).lower(),
        "HolePosition": "0.0 0.0 0.0",
        "FarfieldCenter": "0.0 0.0 0.0",
        "HeightIterations": str(boundary_layer_settings.height_itrations),
        "NormalIterations": str(boundary_layer_settings.normal_iterations),
        "MaxCritIterations": str(boundary_layer_settings.max_crit_iterations),
        "LaplaceIterations": str(boundary_layer_settings.laplace_iterations),
        "Symmetry": str(mesh_settings.symmetry).lower(),
    }


def _pentagrow_sanity_check() -> Path:
    # Fail fast with a clear error if Pentagrow runtime dependencies are missing.
    pentagrow_path = get_install_path(SOFTWARE_NAME)
    if pentagrow_path is None:
        raise ValueError(f"Could not find where {SOFTWARE_NAME=} is installed.")

    if shutil.which("ldd") is None:
        raise ValueError("ldd library is not installed.")

    ldd_run = subprocess.run(
        ["ldd", str(pentagrow_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    missing_deps = []
    for line in ldd_run.stdout.splitlines():
        if "=> not found" in line:
            dep_name = line.split("=>", 1)[0].strip()
            missing_deps.append(dep_name)

    if missing_deps:
        hdf5_deps = [dep for dep in missing_deps if dep.startswith("libhdf5")]
        if hdf5_deps:
            raise RuntimeError(
                "Pentagrow is installed but cannot start because required HDF5 "
                f"runtime libraries are missing: {hdf5_deps}. "
                "Install compatibility libraries matching Pentagrow's expected sonames "
                "(e.g. libhdf5_hl.so.100 and libhdf5.so.103), or point "
                "LD_LIBRARY_PATH to a directory containing those exact files."
            )


# Functions

def pentagrow_3d_mesh(
    results_dir: Path,
    output_format: str,
    mesh_settings: MeshSettings,
    surface_mesh_path: Path,
    volume_mesh_settings: FarfieldSettings,
    boundary_layer_settings: BoundaryLayerSettings,
) -> Path:
    pentagrow_results_dir = results_dir / SOFTWARE_NAME
    pentagrow_results_dir.mkdir(exist_ok=True, parents=True)

    configuration_file: str = f"{SOFTWARE_NAME}.cfg"
    cfg_params = _load_rans_cgf_params(
        mesh_settings=mesh_settings,
        output_format=output_format,
        surface_mesh_path=surface_mesh_path,
        volume_mesh_settings=volume_mesh_settings,
        boundary_layer_settings=boundary_layer_settings,
    )

    # Create the config file for pentagrow
    configuration_path = Path(pentagrow_results_dir, configuration_file)

    # Add cfg_params in config file
    with open(configuration_path, "w") as file:
        for key, value in cfg_params.items():
            file.write(f"{key} = {value}\n")

    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    if not configuration_path.is_file():
        raise FileNotFoundError(f"{configuration_path=} does not exist.")

    # Pentagrow may reuse the input STL path as CGNS section names; keep it short
    # to avoid CGNS 32-char truncation warnings. Place a local link/copy in the
    # Pentagrow working directory so relative CLI args always resolve.
    local_surface_mesh_path = pentagrow_results_dir / f"{surface_mesh_path.stem}.{surface_mesh_path.suffix}"
    if local_surface_mesh_path.exists() or local_surface_mesh_path.is_symlink():
        local_surface_mesh_path.unlink()
    local_surface_mesh_path.symlink_to(surface_mesh_path.resolve())

    command = [local_surface_mesh_path.name, configuration_path.name]

    # Sanity Check before running the software
    _pentagrow_sanity_check()

    # Running command = "pentagrow surface_mesh.stl config.cfg"
    run_software(
        software_name=SOFTWARE_NAME,
        arguments=command,
        wkdir=pentagrow_results_dir,
        with_mpi=False,
        nb_cpu=get_sane_max_cpu(),
    )

    expected = Path(pentagrow_results_dir, f"hybrid.{str(output_format).lower()}")
    if not expected.exists():
        raise FileNotFoundError(f"Pentagrow did not generate file at {expected=}")
    return expected
