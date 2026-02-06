

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import os
import matplotlib.pyplot as plt
import struct
import matplotlib.cm as cm
from scipy.interpolate import PchipInterpolator
from ceasiompy.utils.exportcpacs import Export_CPACS
# ---------------------------
# CONFIG
# ---------------------------
STL_FILE = "src/ceasiompy/STL2CPACS/test_fuse.stl"

TRI_FILE = "src/ceasiompy/STL2CPACS/slice_mesh_output.tri"
N_Y_SLICES = 30 # number of Y slices 
INTERSECT_TOL = 1e-6
SLAB_TOLS = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3]
EXTREME_TOL_perc_start = 0.0001    # at y ==0 and y == y_max the slicing captures point inside the airfoil so be aware about this setting 
EXTREME_TOL_perc_end = 0.005    # at y ==0 and y == y_max the slicing captures point inside the airfoil so be aware about this setting 
N_SLICE_ADDING = 0 # number of slices to insert in transition regions
DEBUG_AIRFOIL = False 

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def fix_airfoil_cpacs(x, z, tol_x):
    """
    Remove duplicate / near-duplicate airfoil points.

    If two points have |x1 - x2| < tol_x → keep only one
    Keep the point that is farther from the local mean

    """

    x = np.asarray(x)
    z = np.asarray(z)
    # Sort by x 
    idx = np.argsort(x)
    x = x[idx]
    z = z[idx]

    x_clean = [x[0]]
    z_clean = [z[0]]
    i = 0
    while i < len(x)-1:
        print(i,abs(z[i] - z[i+1]))
        if  abs(z[i] - z[i+1]) < tol_x and abs(x[i] - x[i+1]) < tol_x:
            print('here')
            # if the points are too close keep the one farther from local mean
            z_mean = 0.5 * (z[i+1] + z[i])
            x_mean = 0.5 * (x[i+1] + x[i])
            z_clean.append(z[i] if abs(z[i] - z_mean) > abs(z[i+1] - z_mean) else z[i+1])
            x_clean.append(x[i] if abs(x[i] - x_mean) > abs(x[i+1] - x_mean) else x[i+1])
            i += 2  # skip next point
        
        else:
            x_clean.append(x[i])
            z_clean.append(z[i])
            i += 1
            
    print(f"Fixed airfoil: {len(x)} → {len(x_clean)} points")
    print('trailing edge', x_clean[np.argmax(x_clean)])
    if DEBUG_AIRFOIL:
        plt.plot(x_clean, z_clean, '.')
        plt.xlabel("x/c")
        plt.ylabel("z/c")
        plt.title("Cleaned Airfoil Points") 
        plt.axis("equal")
        plt.grid()
        plt.show()
    return np.array(x_clean), np.array(z_clean)



def resample_airfoil_cpacs(
    xu, zu,
    xl, zl,
    x_te, z_te,
    n_points,
    
):
    """
    Regularize an airfoil by spline-fitting upper/lower surfaces
    and resampling with either uniform or cosine spacing in x.

    xu, zu : array-like
        Upper surface points.
    xl, zl : array-like
        Lower surface points .
    x_te, z_te : float
        Trailing edge coordinates.
    n_points : int
        Total number of points for the closed airfoil polyline.
    """
    use_cosine_spacing=False
    xu = np.asarray(xu)
    zu = np.asarray(zu)
    xl = np.asarray(xl)
    zl = np.asarray(zl)
    print(f'shape is {np.shape(xu)} with inside { xu}')
    #breakpoint()
    # Sort surfaces
    # Upper: LE -> TE
    idx_u = np.argsort(xu)
    xu, zu = xu[idx_u], zu[idx_u]
    xu[-1] = x_te  
    zu[-1] = z_te  
    
    # Lower: TE -> LE 
    idx_l = np.argsort(xl)[::-1]
    xl, zl = xl[idx_l], zl[idx_l]
    xl[0] = x_te   
    zl[0] = z_te   
    
    # Detect LE
    x_le = min(xu.min(), xl.min())
    # Take average z at LE using closest points in each surface
    z_le = 0.5 * (zu[np.argmin(np.abs(xu - x_le))]
                  + zl[np.argmin(np.abs(xl - x_le))])

    # Build x-distribution on LE → TE
    n_half = n_points // 2
    if use_cosine_spacing:
        beta = np.linspace(0.0, np.pi, n_half)
        x_dist = x_le + (x_te - x_le) * 0.5 * (1 - np.cos(beta))
    else:
        x_dist = np.linspace(x_le, x_te, n_half)

    x_dist = x_dist[1:-1]
    # PCHIP interpolation 
    pchip_upper = PchipInterpolator(xu, zu, extrapolate=False)
    pchip_lower = PchipInterpolator(xl[::-1], zl[::-1], extrapolate=False)

    z_upper = pchip_upper(x_dist)
    z_lower = pchip_lower(x_dist)

    

    x_u, z_u = x_dist, z_upper              # LE -> TE
    x_l, z_l = x_dist[::-1], z_lower[::-1]  # TE -> LE
    # CPACS order
    x_te = 1.0
    x_le = 0.0
    airfoil = np.hstack([
        np.array([[x_te], [z_te]]),
        np.vstack([x_l, z_l])[:, 1:-1],     
        np.array([[x_le], [z_le]]),
        np.vstack([x_u, z_u])[:, 1:-1],     
        np.array([[x_te], [z_te]])
    ])
    if DEBUG_AIRFOIL:
        plt.plot(airfoil[0, :], airfoil[1, :], '-g')
        plt.plot(x_u, z_u, '.r', label='Upper Spline')
        plt.plot(x_l, z_l, '.b', label='Lower Spline')
        plt.xlabel("x/c")
        plt.ylabel("z/c")
        plt.title("Resampled Airfoil Points")
        plt.axis("equal")
        plt.grid()
        plt.show()
    
    return airfoil




def extract_airfoil_surface_local(cloud_xyz, p0, n):
    if cloud_xyz.shape[0] < 10:
        return np.zeros((2, 0)), 0.0

    n = n / np.linalg.norm(n)

    # Local basis
    ex = np.array([1.0, 0.0, 0.0])
    e1 = ex - np.dot(ex, n) * n
    if np.linalg.norm(e1) < 1e-10:
        return np.zeros((2, 0)), 0.0
    e1 /= np.linalg.norm(e1)

    e2 = np.cross(n, e1)
    e2 /= np.linalg.norm(e2)

    # Project STL cloud
    local = np.array([
        [np.dot(p - p0, e1), np.dot(p - p0, -e2)]
        for p in cloud_xyz
    ])

    x = local[:, 0]
    z = local[:, 1]

    # LE / TE detection 
    i_le = np.argmin(x)
    i_te = np.argmax(x)

    x_le = x[i_le]
    x_te = x[i_te]
    
    chord = x_te - x_le

    if chord <= 1e-8:
        return np.zeros((2, 0)), 0.0

    # Normalize ONCE
    x = (x - x_le) / chord
    z = z / chord
    
    # Split using camber line
    if DEBUG_AIRFOIL:
        plt.plot(x, z, '.')
        plt.xlabel("x/c")   
        plt.ylabel("z/c")
        plt.title("Raw Airfoil Points")
        plt.axis("equal")
        plt.grid()
        plt.show()
    n = 10 # number of bins for camber line, it is divided by 6 to have when len(x) is small a reasonable number of bins.
    print(f'numenr o fbins {n} with len(x) = {len(x)}')
    airfoil = split_upper_lower_by_camber(x, z,n, 0.1)
    
    return airfoil, chord

def split_upper_lower_by_camber(x_raw, z_raw, n_bins, te_cut):
    """
     upper/lower split using camber line only where reliable.
    The TE zone is not split to avoid sharp-edge issues.
    """

    x, z = fix_airfoil_cpacs(x_raw, z_raw, 1e-4)

    # Sort by x
    idx = np.argsort(x)
    x = x[idx]
    z = z[idx]

    # Detect LE / TE
    i_le = np.argmin(x)
    i_te = np.argmax(x)

    x_le, z_le = x[i_le], z[i_le]
    x_te, z_te = x[i_te], z[i_te]

    # Define camber-valid zone
    camber_mask = x < (x_te - te_cut)
    x_camber = x[camber_mask]
    z_camber = z[camber_mask]

    # Build coarse camber line  
    bins = np.linspace(x_le, x_te - te_cut, n_bins + 1)

    camber_x = [x_le]
    camber_z = [z_le]

    for i in range(n_bins):
        mask = (x_camber >= bins[i]) & (x_camber < bins[i + 1])
        if np.count_nonzero(mask) < 2:
            continue

        x_bin = x_camber[mask]
        z_bin = z_camber[mask]
        # inside every bin, the camber point is done using the point with the maximum z and an other one wiht the minimum z
        i_up = np.argmax(z_bin)
        i_lo = np.argmin(z_bin)
        camber_x.append(0.5 * (x_bin[i_up] + x_bin[i_lo]))
        camber_z.append(0.5 * (z_bin[i_up] + z_bin[i_lo]))
    
    camber_x = np.array(camber_x)
    camber_z = np.array(camber_z)

    # Interpolate camber on camber zone
    zc = np.interp(x_camber, camber_x, camber_z)

    # Classification 
    upper_mask = np.zeros_like(x, dtype=bool)
    lower_mask = np.zeros_like(x, dtype=bool)

    upper_mask[camber_mask] = z_camber > zc
    lower_mask[camber_mask] = z_camber < zc
    if DEBUG_AIRFOIL:
        plt.plot(x[upper_mask], z[upper_mask], '.', color='red', label='Upper')
        plt.plot(x[lower_mask], z[lower_mask], '.', color='blue', label='Lower')
        plt.plot(x_camber, zc, '-k', label='Camber Line')
        plt.xlabel("x/c")
        plt.ylabel("z/c")
        plt.title("Airfoil Points Classification")
        plt.legend()
        plt.axis("equal")
        plt.grid()
        plt.show()
        
    # Resample
    return resample_airfoil_cpacs(
        x[upper_mask], z[upper_mask],
        x[lower_mask], z[lower_mask],
        x_te=x_te,
        z_te=z_te,
        n_points=80
    )


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
        if abs(d2) < tol: # One vertex above, one below. There is a parametric line equation P(t)=  p1 + t*(p2 - p1)
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



def slice_mesh_rotated_YZ(
    pts,
    tris,
    p0,
    dihedral_deg,
    sweep_deg,
    tol=INTERSECT_TOL,
    debug=False,
):
    """
    Slice mesh with a plane orthogonal to local span direction
    defined by dihedral.
    """

    # Build span direction
    a = np.deg2rad(dihedral_deg)
    b = np.deg2rad(sweep_deg)

    Rx = np.array([
        [1, 0,           0          ],
        [0, np.cos(a),  -np.sin(a)],
        [0, np.sin(a),   np.cos(a)]
    ])

    #  
    RR = Rx 

    e_span = RR @ np.array([0.0, 1.0, 0.0])
    e_span /= np.linalg.norm(e_span)

    # Signed distances
    dverts = (pts - p0) @ e_span
    dtri = dverts[tris]

    tri_min = dtri.min(axis=1)
    tri_max = dtri.max(axis=1)

    hits = np.where((tri_min <= tol) & (tri_max >= -tol))[0]
    if hits.size == 0:
        return np.zeros((0, 3)), e_span

    # -------------------------------------------------
    # Intersections
    # -------------------------------------------------
    inter = []
    for ti in hits:
        i0, i1, i2 = tris[ti]
        ip = intersect_triangle_with_plane_point_normal(
            p0, e_span,
            pts[i0], pts[i1], pts[i2],
            tol=tol
        )
        if ip:
            inter.extend(ip)

    if not inter:
        return np.zeros((0, 3)), e_span

    arr = np.vstack(inter)

    # Deduplicate
    rtol = 1e-8
    key = np.round(arr / rtol).astype(np.int64)
    dtype = np.dtype((np.void, key.dtype.itemsize * key.shape[1]))
    _, idx = np.unique(key.view(dtype), return_index=True)
    arr = arr[np.sort(idx)]

    # -------------------------------------------------
    # DEBUG PLOT
    # -------------------------------------------------
    if debug:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=(9, 7))
        ax = fig.add_subplot(111, projection="3d")

        # Mesh 
        ax.scatter(
            pts[:, 0], pts[:, 1], pts[:, 2],
            s=1, alpha=0.1, color="gray", label="Mesh"
        )

        # Intersection points
        ax.scatter(
            arr[:, 0], arr[:, 1], arr[:, 2],
            s=20, color="red", label="Slice points"
        )

        # Plane normal
        L = np.linalg.norm(arr.max(axis=0) - arr.min(axis=0))
        ax.quiver(
            p0[0], p0[1], p0[2],
            e_span[0], e_span[1], e_span[2],
            length=0.3 * L,
            color="blue",
            linewidth=3,
            label="Plane normal"
        )

        # Plane visualization
        u = np.linspace(-0.3 * L, 0.3 * L, 10)
        v = np.linspace(-0.3 * L, 0.3 * L, 10)
        U, V = np.meshgrid(u, v)

        # Two orthogonal vectors in plane
        t1 = np.cross(e_span, [1, 0, 0])
        if np.linalg.norm(t1) < 1e-6:
            t1 = np.cross(e_span, [0, 0, 1])
        t1 /= np.linalg.norm(t1)
        t2 = np.cross(e_span, t1)

        Xp = p0[0] + U * t1[0] + V * t2[0]
        Yp = p0[1] + U * t1[1] + V * t2[1]
        Zp = p0[2] + U * t1[2] + V * t2[2]

        ax.plot_surface(Xp, Yp, Zp, alpha=0.25, color="cyan")

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(
            f"Slice plane\nDihedral={dihedral_deg:.1f}°, Sweep={sweep_deg:.1f}°"
        )
        ax.legend()
        ax.set_box_aspect([1, 1, 1])
        plt.tight_layout()
        plt.show()

    return arr, e_span


def slice_mesh_at_Y(pts, tris, x_plane, tol):
    """
    slicing with plane Y = y_plane
    """
    p0 = np.array([x_plane, 0.0, 0.0])
    n  = np.array([1.0, 0.0, 0.0])  
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
            sweep[i] = int(np.rint(np.degrees(np.arctan(dy / np.sqrt(dz**2 + dx**2)))))  
        # ---- DIHEDRAL: YZ projection ----
        if abs(dy) < 1e-12:
            dihedral[i] = 0
        else:
            dihedral[i] = int(np.rint(np.degrees(np.arctan(dz / dx))))

    # copy last value 
    sweep[-1] = sweep[-2]
    dihedral[-1] = dihedral[-2]

    return sweep, dihedral

def filter_and_insert(y_vals, sweep_deg, dihedral_deg, le_pts, n_insert):
    """
    Refine wing sections for CPACS generation.

    - Keep first slice
    - Keep one slice before each transition
    - Insert interpolated slices in transitions
    - Skip slices in constant-angle regions after the first slice
    - Always keep last slice
    """

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
    le_x = []
    summary_rows = []
    vi = 0
    per_slice_clouds_rotate = []

    
    # build Y sampling positions
    xmin, xmax = float(np.min(pts[:,0])), float(np.max(pts[:,0]))
    EXTREME_TOL_start = EXTREME_TOL_perc_start * (xmax - xmin)
    EXTREME_TOL_end = EXTREME_TOL_perc_end * (xmax - xmin)
    x_vals = np.linspace(xmin + EXTREME_TOL_start, xmax - EXTREME_TOL_end, N_Y_SLICES)

    
    # First slicing to get the LE points,
    for i, x0 in enumerate(x_vals):
        cloud = slice_mesh_at_Y(pts, tris, x0, INTERSECT_TOL)

        
        # if still empty, skip and record None
        if cloud.shape[0] == 0:
            print(f"Slice {i}: no points found at y={y0:.6g}")
            per_slice_clouds.append(np.zeros((0,3)))
            le_points.append(None)
            le_x.append(x0)
            continue

        # find LE: point with minimum X
        min_idx = int(np.argmin(cloud[:,0]))
        le_pt = cloud[min_idx].copy()

        per_slice_clouds.append(cloud)
        le_points.append(le_pt)
        le_x.append(x0)

        

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
                "X_Trasl": le_pts[0],
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

    # =========================================================
    # DEBUG PLOT 
    # =========================================================

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    # --- Plot original mesh vertices (light background)
    ax.scatter(
        pts[:, 0], pts[:, 1], pts[:, 2],
        s=0.5, c="lightgray", alpha=0.2, label="Mesh vertices"
    )

    # --- Plot slice clouds
    colors = cm.viridis(np.linspace(0, 1, len(per_slice_clouds)))

    for i, cloud in enumerate(per_slice_clouds):
        if cloud.shape[0] == 0:
            continue
        ax.scatter(
            cloud[:, 0], cloud[:, 1], cloud[:, 2],
            s=6, color=colors[i], alpha=0.8
        )

    # --- Plot detected LE points
    le_valid = [(i, p) for i, p in enumerate(le_points) if p is not None]
    if le_valid:
        le_pts_dbg = np.vstack([p for _, p in le_valid])
        ax.plot(
            le_pts_dbg[:, 0],
            le_pts_dbg[:, 1],
            le_pts_dbg[:, 2],
            '-k',
            lw=2,
            label="Detected LE"
            
        )

    # --- Axis labels
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("DEBUG: Raw mesh slices before filtering")

    # --- Equal axis scaling
    all_dbg_pts = np.vstack(
        [pts] +
        [c for c in per_slice_clouds if c.shape[0] > 0]
    )
    X, Y, Z = all_dbg_pts[:, 0], all_dbg_pts[:, 1], all_dbg_pts[:, 2]
    max_range = max(
        np.ptp(X),
        np.ptp(Y),
        np.ptp(Z)
    ) / 2
    mid_x, mid_y, mid_z = X.mean(), Y.mean(), Z.mean()
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    ax.legend()
    plt.tight_layout()
    plt.show()
    


    # =========================================================
    y_vals = le_pts[:,1].copy()
    # filter y_vals . 
    y_vals,sweep_deg,dihedral_deg,le_pts,is_inserted = filter_and_insert(y_vals, sweep_deg, dihedral_deg,le_pts, N_SLICE_ADDING)
    # slice with plane that are rotated by the dihedral angle.
    airfoil_profiles = []

    for i, y0 in enumerate(y_vals):
        if le_pts[i] is None:
            per_slice_clouds_rotate.append(np.zeros((0,3)))
            continue

        lep = le_pts[i]
        dihedral = dihedral_deg[i]

        # slice and rotate mesh
        cloud_rot, n_rot = slice_mesh_rotated_YZ(
            pts,
            tris,
            p0=lep,
            dihedral_deg=dihedral,
            sweep_deg=sweep_deg[i],
            tol=INTERSECT_TOL
        )
        per_slice_clouds_rotate.append(cloud_rot)
        print('slice', i, 'at y =', y0, 'is inserted?', is_inserted[i])
        airfoil_xz, chord = extract_airfoil_surface_local(
            cloud_rot,
            p0=lep,
            n=n_rot,
        )
        

 

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
    plt.legend()
    plt.show()
    
    
    

if __name__ == "__main__":
    main()
