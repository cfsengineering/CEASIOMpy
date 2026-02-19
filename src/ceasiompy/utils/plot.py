
# Imports
import os
import tempfile
import numpy as np
import streamlit as st

from stl import mesh
from pathlib import Path
from numpy import ndarray
from cpacspy.cpacspy import CPACS


# Functions

def get_aircraft_mesh_data(cpacs: CPACS, symmetry: bool) -> tuple[
    ndarray, ndarray, ndarray,
    ndarray, ndarray, ndarray,
] | None:
    """Returns (x, y, z, i, j, k)."""
    aircraft_name = f"""aircraft{"_symmtry" if symmetry else ""}.stl"""
    stl_file = Path(Path(cpacs.cpacs_file).parent, aircraft_name)

    if not stl_file.exists():
        try:
            with st.spinner("Meshing geometry (STL export)..."):
                warning_signature = "Warning: 1 face has been skipped due to null triangulation"
                with (
                    tempfile.TemporaryFile(mode="w+b") as stdout_capture,
                    tempfile.TemporaryFile(mode="w+b") as stderr_capture,
                ):
                    saved_stdout_fd = os.dup(1)
                    saved_stderr_fd = os.dup(2)
                    try:
                        os.dup2(stdout_capture.fileno(), 1)
                        os.dup2(stderr_capture.fileno(), 2)
                        cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
                    finally:
                        os.dup2(saved_stdout_fd, 1)
                        os.dup2(saved_stderr_fd, 2)
                        os.close(saved_stdout_fd)
                        os.close(saved_stderr_fd)

                    stdout_capture.seek(0)
                    stderr_capture.seek(0)
                    captured_stdout = stdout_capture.read().decode("utf-8", errors="ignore")
                    captured_stderr = stderr_capture.read().decode("utf-8", errors="ignore")
                    captured_output = captured_stdout + "\n" + captured_stderr
                    if warning_signature in captured_output:
                        raise RuntimeError(warning_signature)
        except Exception as e:
            st.error(f"Cannot generate 3D preview (probably missing TIGL geometry handle): {e=}.")
            return None

    try:
        your_mesh = mesh.Mesh.from_file(stl_file)
    except Exception as e:
        st.error(f"Cannot load 3D preview mesh file: {e=}.")
        return None
    mesh_vectors = your_mesh.vectors
    if symmetry:
        mesh_vectors = mesh_vectors[np.all(mesh_vectors[:, :, 1] >= -1e-3, axis=1)]

    triangles = mesh_vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T
    return (
        x, y, z,
        i, j, k,
    )
