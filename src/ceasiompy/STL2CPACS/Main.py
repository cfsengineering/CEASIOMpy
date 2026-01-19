

import numpy as np
import os
import csv
import matplotlib.pyplot as plt
import struct
import matplotlib.cm as cm
from scipy.interpolate import PchipInterpolator
from ceasiompy.utils.exportcpacs import Export_CPACS
# ---------------------------
# CONFIG
# ---------------------------
#STL_FILE = "src/ceasiompy/STL2CPACS/test_wing.stl"
STL_FILE = "src/ceasiompy/STL2CPACS/test_wing_winglet.stl"
#STL_FILE = "src/ceasiompy/STL2CPACS/test_sweep.stl"

TRI_FILE = "src/ceasiompy/STL2CPACS/slice_mesh_output.tri"
N_Y_SLICES = 30 # number of Y slices 
INTERSECT_TOL = 1e-6
SLAB_TOLS = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3]
EXTREME_TOL = 1e-3   # at y ==0 and y == y_max the slicing captures point inside the airfoil so be aware about this setting 
SAVE_PER_SLICE_CSV = False  # set True if you want per-slice CSVs
SUMMARY_CSV = "slices_summary.csv"
N_SLICE_ADDING = 3  # number of slices to insert in transition regions
# ---------------------------


# ---------------------------
def fix_airfoil_cpacs(x, z, tol_x=1e-5):
    """
    Fix airfoil point ordering and duplicates for CPACS robustness.

    Input:
        x, z : 1D arrays of airfoil coordinates (normalized)
    Output:
        x_fixed, z_fixed : CPACS-safe airfoil polyline
    """

    x = np.asarray(x)
    z = np.asarray(z)

    # -----------------------------
    # Split lower / upper
    # -----------------------------
    lower = z < 0
    upper = z > 0

    xl, zl = x[lower], z[lower]
    xu, zu = x[upper], z[upper]

    # -----------------------------
    # Collapse duplicate x (LOWER)
    # keep most negative z
    # -----------------------------
    xlu = []
    zlu = []

    for xi in np.unique(np.round(xl / tol_x).astype(int)):
        mask = np.abs(xl - xi * tol_x) < tol_x
        xlu.append(np.mean(xl[mask]))
        zlu.append(np.min(zl[mask]))

    xl = np.array(xlu)
    zl = np.array(zlu)

    # -----------------------------
    # Collapse duplicate x (UPPER)
    # keep most positive z
    # -----------------------------
    xuu = []
    zuu = []

    for xi in np.unique(np.round(xu / tol_x).astype(int)):
        mask = np.abs(xu - xi * tol_x) < tol_x
        xuu.append(np.mean(xu[mask]))
        zuu.append(np.max(zu[mask]))

    xu = np.array(xuu)
    zu = np.array(zuu)

    # -----------------------------
    # Sort strictly
    # -----------------------------
    idx = np.argsort(xl)[::-1]   # TE → LE
    xl, zl = xl[idx], zl[idx]

    idx = np.argsort(xu)         # LE → TE
    xu, zu = xu[idx], zu[idx]

    # -----------------------------
    # Enforce single LE and TE
    # -----------------------------
    LE = np.array([[0.0], [0.0]])
    TE = np.array([[1.0], [0.0]])

    lower = np.vstack([xl, zl])
    upper = np.vstack([xu, zu])

    # remove near LE / TE
    lower = lower[:, lower[0] > tol_x]
    upper = upper[:, upper[0] < 1 - tol_x]

    airfoil = np.hstack([
        TE,
        lower,
        LE,
        upper,
        TE
    ])

    return airfoil

def resample_airfoil_cpacs(airfoil, n_points=50, eps=0.001):
    """
    CPACS-safe airfoil regularization.
    Removes spline oscillations and enforces monotonicity.
    """

    x = airfoil[0]
    z = airfoil[1]

    # -------------------------
    # Split surfaces
    # -------------------------
    i_le = np.argmin(x)

    lower_x = x[:i_le+1][::-1]   # LE → TE
    lower_z = z[:i_le+1][::-1]

    upper_x = x[i_le:]
    upper_z = z[i_le:]

    # Remove duplicates
    lower_x, idx = np.unique(lower_x, return_index=True)
    lower_z = lower_z[idx]

    upper_x, idx = np.unique(upper_x, return_index=True)
    upper_z = upper_z[idx]

    # -------------------------
    # Cosine spacing
    # -------------------------
    n_half = n_points // 2
    beta = np.linspace(0, np.pi, n_half)
    x_dist = 0.5 * (1 - np.cos(beta))  # LE → TE

    # -------------------------
    # -------------------------
    pchip_lower = PchipInterpolator(lower_x, lower_z)
    pchip_upper = PchipInterpolator(upper_x, upper_z)

    z_lower = pchip_lower(x_dist)
    z_upper = pchip_upper(x_dist)

    # -------------------------
    # -------------------------
    z_lower[0] = 0.0
    z_upper[0] = 0.0
    z_lower[-1] = 0.0
    z_upper[-1] = 0.0


    # -------------------------
    # Rebuild CPACS order
    # -------------------------
    airfoil_fixed = np.hstack([
        np.array([[1.0], [0.0]]),
        np.vstack([x_dist[::-1], z_lower[::-1]])[:, 1:-1],
        np.array([[0.0], [0.0]]),
        np.vstack([x_dist, z_upper])[:, 1:-1],
        np.array([[1.0], [0.0]])
    ])

    return airfoil_fixed


def extract_airfoil_surface_local(cloud_xyz, p0, n):
    """
    Extract CPACS-compatible airfoil from a rotated slice.

    Ordering (MANDATORY):
        TE -> LE on lower surface
        LE -> TE on upper surface

    Guarantees:
        LE at x=0
        TE at x=1
        unique LE and TE
    """

    if cloud_xyz.shape[0] < 10:
        return np.zeros((2, 0)), 0.0

    n = n / np.linalg.norm(n)

    # -----------------------------
    # Local 2D basis in slice plane
    # -----------------------------
    ex = np.array([1.0, 0.0, 0.0])
    e1 = ex - np.dot(ex, n) * n
    if np.linalg.norm(e1) < 1e-10:
        return np.zeros((2, 0)), 0.0
    e1 /= np.linalg.norm(e1)

    e2 = np.cross(n, e1)
    e2 /= np.linalg.norm(e2)

    # -----------------------------
    # Project cloud into 2D
    # -----------------------------
    local = np.array([
        [np.dot(p - p0, e1), np.dot(p - p0, e2)]
        for p in cloud_xyz
    ])

    x = local[:, 0]
    z = local[:, 1]

    # -----------------------------
    # Sort points CCW (needed for consistent traversal)
    # -----------------------------
    cx, cz = np.mean(x), np.mean(z)
    angles = np.arctan2(z - cz, x - cx)
    order = np.argsort(angles)
    x = x[order]
    z = z[order]

    # -----------------------------
    # LE and TE detection
    # -----------------------------
    i_le = np.argmin(x)
    i_te = np.argmax(x)

    x_le = x[i_le]
    x_te = x[i_te]
    chord = x_te - x_le

    if chord <= 0:
        return np.zeros((2, 0)), 0.0

    # -----------------------------
    # Split lower / upper surfaces
    # -----------------------------
    lower_mask = z < 0
    upper_mask = z >= 0

    x_lower = x[lower_mask]
    z_lower = z[lower_mask]

    x_upper = x[upper_mask]
    z_upper = z[upper_mask]

    # -----------------------------
    # Sort surfaces by x
    # -----------------------------
    idx = np.argsort(x_lower)[::-1]  # TE → LE
    x_lower, z_lower = x_lower[idx], z_lower[idx]

    idx = np.argsort(x_upper)        # LE → TE
    x_upper, z_upper = x_upper[idx], z_upper[idx]

    # -----------------------------
    # Normalize to chord
    # -----------------------------
    x_lower = (x_lower - x_le) / chord
    x_upper = (x_upper - x_le) / chord
    z_lower = z_lower / chord
    z_upper = z_upper / chord

    # -----------------------------
    # Enforce exact LE and TE
    # -----------------------------
    LE = np.array([[0.0], [0.0]])
    TE = np.array([[1.0], [0.0]])

    lower = np.vstack([x_lower, z_lower])
    upper = np.vstack([x_upper, z_upper])

    # remove near-LE / TE duplicates
    lower = lower[:, lower[0] > 1e-6]
    upper = upper[:, upper[0] < 1 - 1e-6]

    airfoil = fix_airfoil_cpacs(
    np.hstack([TE[0], lower[0], LE[0], upper[0], TE[0]]),
    np.hstack([TE[1], lower[1], LE[1], upper[1], TE[1]])
    )
    airfoil = resample_airfoil_cpacs(airfoil, n_points=60)
    return airfoil, chord



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

def intersect_triangle_with_plane_point_normal(p0, n, a, b, c, tol=INTERSECT_TOL):
    da = np.dot(n, a - p0); db = np.dot(n, b - p0); dc = np.dot(n, c - p0)
    pts = []
    def edge_int(p1,d1,p2,d2):
        if abs(d1) < tol and abs(d2) < tol: #Both vertices lie on the plane
            return [p1, p2]
        if abs(d1) < tol: #One vertex on plane
            return [p1]
        if abs(d2) < tol: # One vertex above, one below. There is a parametric line equation P9t) p1 + t*(p2 - p1)
            return [p2]
        if d1 * d2 < 0:
            t = d1 / (d1 - d2)
            return [p1 + t * (p2 - p1)]
        return [] # Edge does not intersect plane
    pts += edge_int(a,da,b,db)
    pts += edge_int(b,db,c,dc)
    pts += edge_int(c,dc,a,da)
    if not pts: 
        return []
    uniq = []
    for p in pts:
        if not any(np.linalg.norm(p - q) < 1e-10 for q in uniq): #Sometimes the intersection produces duplicate points
            uniq.append(p)
    return uniq


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

def export_mesh(tri_filename=TRI_FILE, stl_filename=STL_FILE):
    """
    Direct STL → TRI converter.
    Output is identical to OpenVSP EXPORT_CART3D.
    """
    if not os.path.exists(stl_filename):
        raise FileNotFoundError(f"STL not found: {stl_filename}")

    print("Reading STL ...")
    tris = load_stl_auto(stl_filename)
    print(f"Loaded {tris.shape[0]} triangles")

    print("Writing Cart3D TRI ...")
    write_cart3d_tri(tri_filename, tris)

    print("Done.")
    return tri_filename


def slice_mesh_rotated_Y(pts, tris, p0, dihedral_deg, tol=INTERSECT_TOL):
    """
    Slice mesh with a plane passing through p0,
    normal obtained by rotating +Y by dihedral about X.
    """

    # Base normal (Y direction)
    n0 = np.array([0.0, 1.0, 0.0])

    # Rotation about X (dihedral)
    a = np.deg2rad(dihedral_deg)
    Rx = np.array([
        [1, 0,           0          ],
        [0, np.cos(a),  -np.sin(a)],
        [0, np.sin(a),   np.cos(a)]
    ])

    n = Rx @ n0
    n = n / np.linalg.norm(n)

    # Signed distances
    dverts = (pts - p0) @ n
    dtri = dverts[tris]
    tri_min = dtri.min(axis=1)
    tri_max = dtri.max(axis=1)
  
    hits = np.where((tri_min <= tol) & (tri_max >= -tol))[0]
    if hits.size == 0:
        return np.zeros((0, 3))

    inter = []
    for ti in hits:
        i0, i1, i2 = tris[ti]
        a_pt, b_pt, c_pt = pts[i0], pts[i1], pts[i2]
        ip = intersect_triangle_with_plane_point_normal(
            p0, n, a_pt, b_pt, c_pt, tol=tol
        )
        if ip:
            inter.extend(ip)

    if not inter:
        return np.zeros((0, 3))

    arr = np.vstack(inter)

    # Deduplicate
    rtol = 1e-8
    key = np.round(arr / rtol).astype(np.int64)
    dtype = np.dtype((np.void, key.dtype.itemsize * key.shape[1]))
    _, idx = np.unique(key.view(dtype), return_index=True)
    return arr[np.sort(idx)],n

def slice_mesh_at_Y(pts, tris, y_plane, tol):
    """
    slicing with plane Y = y_plane
    """
    p0 = np.array([0.0, y_plane, 0.0])
    n  = np.array([0.0, 1.0, 0.0])  
    dverts = (pts - p0) @ n
    dtri = dverts[tris]
    
    
    
    tri_min = dtri.min(axis=1)
    tri_max = dtri.max(axis=1)
    
    hits = np.where((tri_min <= tol) & (tri_max >= -tol))[0]
    if hits.size == 0:
        return np.zeros((0, 3))

    inter = []
    for ti in hits:
        
        i0, i1, i2 = tris[ti]
        ip = intersect_triangle_with_plane_point_normal(
            p0, n, pts[i0], pts[i1], pts[i2], tol
        )
        if ip:
            inter.extend(ip)

    if not inter:
        return np.zeros((0, 3))

    arr = np.vstack(inter)

    # deduplicate
    rtol = 1e-9
    key = np.round(arr / rtol).astype(np.int64)
    dtype = np.dtype((np.void, key.dtype.itemsize * key.shape[1]))
    _, idx = np.unique(key.view(dtype), return_index=True)
    return arr[np.sort(idx)]


def slab_vertex_fallback(pts, y0, slab_list=SLAB_TOLS):
    """If exact plane intersection fails, try vertices within |y-y0|<=slab; return Nx3 or empty."""
    for slab in slab_list:
        mask = np.abs(pts[:,1] - y0) <= slab
        if np.any(mask):
            return pts[mask]
    return np.zeros((0,3))



def compute_local_angles_from_le(le_pts):
    """
    Compute sweep and dihedral from LE points.
    Sweep is defined in the XY plane.
    Dihedral is defined in the YZ plane.
    """

    le_pts = np.asarray(le_pts)
    M = le_pts.shape[0]
    if M < 2:
        return np.array([]), np.array([])

    sweep = np.zeros(M, dtype=int)
    dihedral = np.zeros(M, dtype=int)

    for i in range(M - 1):
        dx = le_pts[i+1, 0] - le_pts[i, 0]
        dy = le_pts[i+1, 1] - le_pts[i, 1]
        dz = le_pts[i+1, 2] - le_pts[i, 2]

        # ---- SWEEP: XY projection ----
        if abs(dy) < 1e-12:
            sweep[i] = 0
        else:
            sweep[i] = int(np.rint(np.degrees(np.arctan(dx / np.sqrt(dy**2 + dz**2)))))   # i don't know why every times add 9 degree !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # ---- DIHEDRAL: YZ projection ----
        if abs(dy) < 1e-12:
            dihedral[i] = 0
        else:
            dihedral[i] = int(np.rint(np.degrees(np.arctan(dz / dy))))

    # copy last value (CPACS convention)
    sweep[-1] = sweep[-2]
    dihedral[-1] = dihedral[-2]

    return sweep, dihedral



def filter_and_insert(y_vals, sweep_deg, dihedral_deg, le_pts, n_insert):
    """
    Refine wing sections for CPACS generation.

    Rules:
    - Keep first slice
    - Keep one slice before each transition
    - Insert interpolated slices in transitions
    - Skip slices in constant-angle regions after the first slice
    - Always keep last slice
    """
    import numpy as np

    y_vals = np.asarray(y_vals, dtype=float)
    sweep_deg = np.asarray(sweep_deg, dtype=float)
    dihedral_deg = np.asarray(dihedral_deg, dtype=float)
    le_pts = np.asarray(le_pts, dtype=float)

    # Initialize output arrays with the first slice
    y_out = [y_vals[0]]
    sweep_out = [sweep_deg[0]]
    dihedral_out = [dihedral_deg[0]]
    le_out = [le_pts[0]]
    is_inserted = [False]

    for i in range(len(y_vals) - 1):
        same_angle = (
            sweep_deg[i] == sweep_deg[i + 1] and
            dihedral_deg[i] == dihedral_deg[i + 1]
        )

        # If a transition is coming, keep the current slice as the "pre-transition" slice
        if not same_angle:
            # Keep current slice before starting transition
            y_out.append(y_vals[i])
            sweep_out.append(sweep_deg[i])
            dihedral_out.append(dihedral_deg[i])
            le_out.append(le_pts[i])
            is_inserted.append(False)

            # Interpolate transition slices
            for k in range(1, n_insert + 1):
                t = k / (n_insert + 1)
                y_new = (1 - t) * y_vals[i] + t * y_vals[i + 1]
                le_new = (1 - t) * le_pts[i] + t * le_pts[i + 1]
                sweep_new = (1 - t) * sweep_deg[i] + t * sweep_deg[i + 1]
                dihedral_new = (1 - t) * dihedral_deg[i] + t * dihedral_deg[i + 1]
                y_out.append(y_new)
                le_out.append(le_new)
                sweep_out.append(sweep_new)
                dihedral_out.append(dihedral_new)
                is_inserted.append(True)

            # Keep right boundary of the transition
            

        else:
            # Skip slice if same as previous (constant region), unless last slice
            if i == len(y_vals) - 2:  # keep last slice
                y_out.append(y_vals[i + 1])
                le_out.append(le_pts[i + 1])
                sweep_out.append(sweep_deg[i + 1])
                dihedral_out.append(dihedral_deg[i + 1])
                is_inserted.append(False)
            # else skip slice in constant region

    return (
        np.array(y_out),
        np.rint(sweep_out).astype(int),
        np.rint(dihedral_out).astype(int),
        np.array(le_out),
        np.array(is_inserted, dtype=bool),
    )


# ---------------------------
# MAIN
# ---------------------------
def main():
    
    print("Start: export mesh from OpenVSP")
    tri_fname = export_mesh(TRI_FILE)
    pts, tris = parse_cart3d_tri(tri_fname)
    print("Loaded mesh:", pts.shape, tris.shape)

    # some initializtion 
    airfoil_profiles = []
    Wing_Dict = {
        "1": {}
    }
    per_slice_clouds = []
    per_slice_clouds_rotate = []
    le_points = []   # leading edge per slice (min X)
    le_y = []
    summary_rows = []
    vi = 0
    per_slice_clouds_rotate = []

    
    # build Y sampling positions
    ymin, ymax = float(np.min(pts[:,1])), float(np.max(pts[:,1]))
    y_vals = np.linspace(ymin + EXTREME_TOL, ymax-EXTREME_TOL, N_Y_SLICES)

    
    # First slicing to get the LE points, obnc ei know them i re - slice the stl with the rotation of the plane.
    for i, y0 in enumerate(y_vals):
        cloud = slice_mesh_at_Y(pts, tris, y0, INTERSECT_TOL)

        # fallback: vertices in slab
        if cloud.shape[0] == 0:
            cloud = slab_vertex_fallback(pts, y0, slab_list=SLAB_TOLS)

        # if still empty, skip and record None
        if cloud.shape[0] == 0:
            print(f"Slice {i}: no points found at y={y0:.6g}")
            per_slice_clouds.append(np.zeros((0,3)))
            le_points.append(None)
            le_y.append(y0)
            summary_rows.append([i, y0, np.nan, np.nan, np.nan, np.nan, np.nan, 0])
            continue

        # find LE: point with minimum X
        min_idx = int(np.argmin(cloud[:,0]))
        le_pt = cloud[min_idx].copy()

        per_slice_clouds.append(cloud)
        le_points.append(le_pt)
        le_y.append(y0)

        


    # build LE array 
    valid_idxs = [i for i, p in enumerate(le_points) if p is not None]
    if len(valid_idxs) < 2:
        raise RuntimeError("Too few LE points found. Check mesh and N_Y_SLICES.")

    le_pts = np.vstack([le_points[i] for i in valid_idxs])
    print(f"Found {le_pts.shape[0]} LE points from {N_Y_SLICES} Y-slices")


    # start to build the dictionary to create all the necessary informations to generate the corresponding CPACS file. 
    Wing_Dict["1"]["Transformation"] = {
                "Name_type": "Wing",
                "Name": "Wing1", # load the name of the stl
                "X_Rot": [0, 0, 0],
                "X_Trasl": [0,0,0],
                "Symmetry": "2", # the user must split the component and tell with a botton if he wants the symmetric part part or not 
                "abs_system": True,
                "Relative_dih": 0,
                "Relative_Twist": 0,
                "ParentUid": 0,
                "reference_length": 0,
                "idx_engine":None
            }
    # compute sweep & dihedral along LE (per point)
    sweep_deg, dihedral_deg = compute_local_angles_from_le(le_pts)
    # fill summary rows: map back sweep/dihedral into the summary_rows entries for valid_idxs
    # we stored summary_rows in order; update entries where LE found
    
    y_vals = le_pts[:,1].copy()
    # filter y_vals . 
    y_vals,sweep_deg,dihedral_deg,le_pts,is_inserted = filter_and_insert(y_vals, sweep_deg, dihedral_deg,le_pts, N_SLICE_ADDING)
    # slice with plane that are rotated by the dihedral angle.
    airfoil_profiles = []
    airfoil_xz_prev = []
    for i, y0 in enumerate(y_vals):
        if le_pts[i] is None:
            per_slice_clouds_rotate.append(np.zeros((0,3)))
            continue

        lep = le_pts[i]
        dihedral = dihedral_deg[i]

        # slice and rotate mesh
        cloud_rot, n_rot = slice_mesh_rotated_Y(
            pts,
            tris,
            p0=lep,
            dihedral_deg=dihedral,
            tol=INTERSECT_TOL
        )

        # fallback if needed
        if cloud_rot.shape[0] == 0:
            print('necessary slab vertex')
            cloud_rot = slab_vertex_fallback(pts, lep[1])

        per_slice_clouds_rotate.append(cloud_rot)

        
        airfoil_xz, chord = extract_airfoil_surface_local(
            cloud_rot,
            p0=lep,
            n=n_rot,
        )
        if is_inserted[i]:
            airfoil_xz = airfoil_xz_prev[-1].copy()                        
        else:
            airfoil_xz_prev.append(airfoil_xz.copy())

        print(chord,'at section', i)
        
        '''plt.figure()
        plt.plot(airfoil_xz[0,:], airfoil_xz[1,:], '-o')   
        plt.title(f'Section {i} at y={y0:.3f}, chord={chord:.3f}')
        plt.xlabel('x'); plt.ylabel('z')
        plt.axis('equal')
        plt.grid(True)
        plt.show()'''
        # Store current chord for next iteration

        # Store in Wing_Dict
        if i==0: 
            Wing_Dict["1"][f'Section{i}'] = {
                'x_scal': round(chord, 2),
                'y_scal': 1,
                'z_scal': round(chord, 2),
                'x_trasl': 0,
                'Span': 0,
                'Airfoil': 'Airfoil',
                'Airfoil_coordinates': airfoil_xz,
                'Sweep_loc': 0,
                'Sweep_angle': sweep_deg[i],
                'Dihedral_angle': dihedral_deg[i]
            }
        
        else:            
            Wing_Dict["1"][f'Section{i}'] = {
            'x_scal': round(chord, 2),
            'y_scal': 1,
            'z_scal': round(chord, 2),
            'x_trasl': 0,
            'Span': abs((y_vals[i]-y_vals[i-1])/np.cos(np.deg2rad(dihedral_deg[i]))),
            'Airfoil': 'Airfoil',
            'Airfoil_coordinates': airfoil_xz,
            'Sweep_loc': 0,
            'Sweep_angle': sweep_deg[i],
            'Dihedral_angle': dihedral_deg[i]
            }

        airfoil_profiles.append(airfoil_xz)

    
    
    exporter = Export_CPACS(Wing_Dict, "Test_STL2CPACS",'src/ceasiompy/STL2CPACS')
    exporter.run()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # ---------- Save and debug ---------------------------
    
    # DEBUG PLOT
    fig = plt.figure(figsize=(10,7))
    ax = fig.add_subplot(111, projection='3d')

    colors = cm.rainbow(np.linspace(0,1,len(per_slice_clouds_rotate)))
    # ---- LEADING EDGE CURVE ----
    ax.plot(
        le_pts[:,0],
        le_pts[:,1],
        le_pts[:,2],
        '-k',
        lw=2,
        label='Leading Edge'
    )

    for i, cloud in enumerate(per_slice_clouds_rotate):
        if cloud.shape[0] > 0:
            ax.scatter(cloud[:,0], cloud[:,1], cloud[:,2], s=3, color=colors[i])
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.set_title("All slices + LE")
    # equal axis scale
    all_pts = np.vstack([c for c in per_slice_clouds_rotate if c.shape[0]>0])
    X,Y,Z = all_pts[:,0], all_pts[:,1], all_pts[:,2]
    max_range = np.max([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]) / 2.0
    mid_x = (X.max()+X.min())*0.5
    mid_y = (Y.max()+Y.min())*0.5
    mid_z = (Z.max()+Z.min())*0.5
    ax.set_xlim(mid_x-max_range, mid_x+max_range)
    ax.set_ylim(mid_y-max_range, mid_y+max_range)
    ax.set_zlim(mid_z-max_range, mid_z+max_range)
    plt.tight_layout()
    plt.show()
    
    
    

if __name__ == "__main__":
    main()
