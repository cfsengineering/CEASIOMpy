"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import shutil
import subprocess

from ceasiompy.cpacs2gmsh.func.utils import (
    check_path,
    load_rans_cgf_params,
)
from ceasiompy.utils.ceasiompyutils import (
    run_software,
    get_install_path,
    get_sane_max_cpu,
)

from pathlib import Path
from ceasiompy.cpacs2gmsh.func.utils import BoundaryLayerSettings

from ceasiompy import log
from ceasiompy.cpacs2gmsh import SOFTWARE_NAME


# Functions

def pentagrow_3d_mesh(
    boundary_layer_settings: BoundaryLayerSettings,
) -> Path:
    cfg_params = load_rans_cgf_params(
        fuselage_maxlen=fuselage_maxlen,
        farfield_factor=farfield_factor,
        n_layer=n_layer,
        h_first_layer=h_first_layer,
        max_layer_thickness=max_layer_thickness,
        growth_factor=growth_factor,
        growth_ratio=growth_ratio,
        feature_angle=feature_angle,
        symmetry=symmetry,
        output_format=output_format,
    )

    # Create the config file for pentagrow
    config_penta_path = Path(result_dir, "config.cfg")

    # Add cfg_params in config file
    with open(config_penta_path, "w") as file:
        for key, value in cfg_params.items():
            file.write(f"{key} = {value}\n")

    check_path(Path(result_dir, "surface_mesh.stl"))
    check_path(Path(result_dir, "config.cfg"))
    log.info(f"(Checked in folder {result_dir}) (and config penta path is {config_penta_path})")

    command = ["surface_mesh.stl", "config.cfg"]

    # Fail fast with a clear error if Pentagrow runtime dependencies are missing.
    pentagrow_path = get_install_path(SOFTWARE_NAME)
    if pentagrow_path is not None and shutil.which("ldd") is not None:
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

    # Running command = "pentagrow surface_mesh.stl config.cfg"
    run_software(
        software_name=SOFTWARE_NAME,
        arguments=command,
        wkdir=result_dir,
        with_mpi=False,
        nb_cpu=get_sane_max_cpu(),
    )

    expected = Path(result_dir, f"hybrid.{str(output_format).lower()}")
    if expected.exists():
        return expected

    # Pentagrow builds have historically differed in their output casing/naming.
    candidates = []
    candidates.extend(Path(result_dir).glob("hybrid.*"))
    candidates.extend(Path(result_dir).glob("HYBRID.*"))

    # Prefer same extension (case-insensitive), if present.
    ext_lower = str(output_format).lower()
    for cand in candidates:
        if cand.suffix.lower().lstrip(".") == ext_lower:
            try:
                cand.rename(expected)
            except OSError:
                shutil.copyfile(cand, expected)
            return expected

    # If there is a single obvious 'hybrid.*', normalize its name.
    unique = [c for c in candidates if c.is_file()]
    if len(unique) == 1:
        cand = unique[0]
        try:
            cand.rename(expected)
        except OSError:
            shutil.copyfile(cand, expected)
        return expected

    raise FileNotFoundError(
        f"Pentagrow did not produce the expected mesh file '{expected}'. "
        f"Found candidates: {[c.name for c in unique]}"
    )
