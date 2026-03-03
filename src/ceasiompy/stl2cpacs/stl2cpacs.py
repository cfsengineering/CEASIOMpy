from pathlib import Path
import numpy as np
import os
import struct
from ceasiompy.utils.exportcpacs import Export_CPACS
from pathlib import Path










def export_mesh(tri_filename, stl_filename,name):
    """
    Direct STL → TRI converter.
    """
    if not os.path.exists(stl_filename):
        raise FileNotFoundError(f"STL not found: {stl_filename}")

    print("Reading STL ...")
    tris = load_stl_auto(stl_filename)
    print(f"Loaded {tris.shape[0]} triangles")

    print("Writing Cart3D TRI ...")
    tri_dir = Path(tri_filename) / "STL2CPACS"
    tri_dir.mkdir(parents=True, exist_ok=True)
    tri_path = tri_dir / f"{name}.tri"
    write_cart3d_tri(tri_path, tris)
    print("Done.")
    return str(tri_path)



def cpacs_component_detection(stl_file) -> list:
    """
    Automatically detects if STL represents a wing, vertical tail, or fuselage
    using PCA.

    Criteria:
    - Wing: maximum variance approximately aligned with global Y axis
    - Vertical tail: maximum variance approximately aligned with global Z axis
    - Fuselage: maximum variance approximately aligned with global X axis

    Returns:
        List[str]: ["wing"], ["wing_vertical_tail"], or ["fuselage"]
    """

    cpacs_component = []

    if isinstance(stl_file, (str, Path)):
        stl_file = [stl_file]

    for path in stl_file:

        # ---------------------------------------------------------
        # 1) Load STL and extract unique vertices
        # ---------------------------------------------------------
        tris = load_stl_auto(path)
        points = tris.reshape(-1, 3)
        points = np.unique(points, axis=0)

        # ---------------------------------------------------------
        # 2) Center the geometry
        # ---------------------------------------------------------
        # PCA must be applied on centered data.
        # We subtract the centroid so that variance describes
        # only shape distribution and not absolute position.
        centroid = np.mean(points, axis=0)
        centered = points - centroid

        # ---------------------------------------------------------
        # 3) Principal Component Analysis (PCA)
        # ---------------------------------------------------------
        # Covariance matrix describes how geometry spreads in space.
        # Eigenvectors give principal directions of variance.
        # Eigenvalues give amount of variance in each direction.
        cov = np.cov(centered.T)
        eigvals, eigvecs = np.linalg.eigh(cov)

        # Sort eigenvalues descending so eigvecs[:,0] corresponds
        # to direction of maximum geometric development.
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]

        # ---------------------------------------------------------
        # 4) Principal direction (maximum variance direction)
        # ---------------------------------------------------------
        # This vector tells us along which axis the STL is
        # developing the most (longest geometric dimension).
        principal_dir = eigvecs[:, 0]

        # Normalize to make it a unit vector.
        # IMPORTANT:
        # For a unit vector v = [vx, vy, vz],
        # each component is a DIRECTION COSINE:
        #
        # vx = cos(angle with global X axis)
        # vy = cos(angle with global Y axis)
        # vz = cos(angle with global Z axis)
        #
        # This comes from the dot product definition:
        # v · ex = |v||ex| cos(theta_x)
        # Since both are unit vectors, v · ex = cos(theta_x).
        #
        # Therefore the components of a normalized vector
        # directly measure angular alignment with axes.
        principal_dir = principal_dir / np.linalg.norm(principal_dir)

        # ---------------------------------------------------------
        # 5) Axis alignment (direction cosines)
        # ---------------------------------------------------------
        # We take absolute value because orientation sign
        # does not matter:
        # +X and -X are both fuselage directions.
        #
        # Example:
        # align_x > 0.75  -> angle < acos(0.75) ≈ 41°
        # align_y > 0.6   -> angle < acos(0.6)  ≈ 53°
        #
        # So we are effectively testing whether the principal
        # direction lies inside a cone around a global axis.
        align_x = abs(principal_dir[0])
        align_y = abs(principal_dir[1])
        align_z = abs(principal_dir[2])

        # ---------------------------------------------------------
        # 6) Variance ratio (elongation check)
        # ---------------------------------------------------------
        # For a fuselage, geometry is strongly elongated in X.
        # So first eigenvalue should be significantly larger
        # than the second.
        #
        # If ratio is close to 1 → geometry is more isotropic.
        var_ratio = eigvals[0] / eigvals[1]

        # ---------------------------------------------------------
        # 7) Classification logic
        # ---------------------------------------------------------

        # Fuselage:
        #  - Strong elongation
        #  - Principal direction mostly aligned with X
        if align_x > 0.75 and var_ratio > 1.2:
            cpacs_component.append("fuselage")

        # Vertical tail:
        #  - Dominant direction along Z
        elif align_z > 0.6:
            cpacs_component.append("wing_vertical_tail")

        # Wing:
        #  - Dominant direction along Y
        #  - Works even with sweep or winglets
        elif align_y > 0.6:
            cpacs_component.append("wing")

        # Fallback: choose axis with strongest alignment
        else:
            if align_x > align_y and align_x > align_z:
                cpacs_component.append("fuselage")
            elif align_z > align_y:
                cpacs_component.append("wing_vertical_tail")
            else:
                cpacs_component.append("wing")



    return cpacs_component









def load_stl_auto(path):
    with open(path, "rb") as f:
        start = f.read(80)
    if start[:5].lower() == b"solid":
        try:
            return read_ascii_stl(path)
        except:
            return read_binary_stl(path)
    return read_binary_stl(path)

def write_cart3d_tri(filename, triangles):
    """
    Saves triangles to Cart3D .tri format 
    """
    verts = triangles.reshape(-1, 3)
    uniq, inverse = np.unique(verts, axis=0, return_inverse=True)
    tri_idx = inverse.reshape(-1, 3) + 1  # 1-based indices

    with open(filename, "w") as f:
        f.write(f"{uniq.shape[0]} {tri_idx.shape[0]}\n") # first lie
        for v in uniq:
            f.write(f"{v[0]:.9g} {v[1]:.9g} {v[2]:.9g}\n") # vertices 
        for t in tri_idx:
            f.write(f"{t[0]} {t[1]} {t[2]}\n") # triangle 

    return filename



def read_ascii_stl(path):
    """Reads ASCII STL and returns Nx3x3 triangle array"""
    tri = []
    with open(path, "r") as f:
        for line in f:
            if line.strip().startswith("vertex"):
                _, x, y, z = line.split()
                tri.append([float(x), float(y), float(z)])
    tri = np.array(tri).reshape(-1, 3, 3)
    return tri

def read_binary_stl(path):
    """Reads binary STL and returns Nx3x3 triangle array"""
    with open(path, "rb") as f:
        header = f.read(80)
        ntri = struct.unpack("<I", f.read(4))[0]
        data = f.read()

    tri = []
    offset = 0
    for _ in range(ntri):
        offset += 12  # skip normal
        v1 = struct.unpack_from("<fff", data, offset); offset += 12
        v2 = struct.unpack_from("<fff", data, offset); offset += 12
        v3 = struct.unpack_from("<fff", data, offset); offset += 12
        offset += 2   # skip attribute
        tri.append([v1, v2, v3])

    return np.array(tri, dtype=float)


def parse_cart3d_tri(filename):
    with open(filename, 'r') as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    header = lines[0].split()
    npts = int(header[0]); ntris = int(header[1])
    pts = np.zeros((npts,3), dtype=float)
    for i in range(npts):
        vals = lines[1+i].split()
        pts[i] = [float(vals[0]), float(vals[1]), float(vals[2])]
    tris = np.zeros((ntris,3), dtype=int)
    start = 1 + npts
    for i in range(ntris):
        a,b,c = lines[start+i].split()[:3]
        tris[i] = [int(a)-1, int(b)-1, int(c)-1] # TRI files use 1-based indexing so the -1 is only for python indexing 
    return pts, tris







def main(stl_file: list[str | Path], setting: list[dict], out_dir: str | Path) -> Path:
    """Convert STL components to one CPACS file and return output XML path."""
    # Local imports although it shows errors 
    from ceasiompy.stl2cpacs.func.stl2wing import stl2wing_main
    from ceasiompy.stl2cpacs.func.stl2fuselage import stl2fuselage_main
    
    cpacs_component = cpacs_component_detection(stl_file=stl_file)
    
    if not (len(stl_file) == len(cpacs_component) == len(setting)):
        raise ValueError(
            "stl_file, cpacs_component and setting must have the same length."
        )

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dict_exportcpacs = {}
    for idx, (stl_path, item, comp_setting) in enumerate(
        zip(stl_file, cpacs_component, setting), start=1
    ):
        item_norm = str(item).strip().lower()
       
        comp_name = Path(stl_path).stem
        if item_norm == "wing" or item_norm == "wing_vertical_tail":
            effective_setting = {
                "EXTREME_TOL_perc_start": 0.02,
                "EXTREME_TOL_perc_end": 0.02,
                "N_Y_SLICES": 50,
                "N_SLICE_ADDING": 0,
                "TE_CUT": 0.0,
                "N_BIN": 10,
                "vertical_tail": True if item_norm == "wing_vertical_tail" else False,
            }
            effective_setting.update(comp_setting)
            dict_exportcpacs[f"component_{idx}"] = stl2wing_main(
                stl_path, effective_setting, output_dir, comp_name
            )
        elif item_norm == "fuselage":
            effective_setting = {
                "EXTREME_TOL_perc_start": 0.02,
                "EXTREME_TOL_perc_end": 0.02,
                "N_X_SLICES": 50,
                "N_SLICE_ADDING": 0,
            }
            effective_setting.update(comp_setting)
            dict_exportcpacs[f"component_{idx}"] = stl2fuselage_main(
                stl_path, effective_setting, output_dir, comp_name
            )
        

    exporter = Export_CPACS(dict_exportcpacs, "stl2cpacs_file", output_dir)
    return exporter.run()
