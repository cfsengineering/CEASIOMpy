

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import os
import matplotlib.pyplot as plt
import struct
import matplotlib.cm as cm
from scipy.interpolate import PchipInterpolator
from ceasiompy.stl2cpacs.stl2cpacs import export_mesh, parse_cart3d_tri, load_stl_auto
from pathlib import Path

# ---------------------------
# CONFIG
# ---------------------------

INTERSECT_TOL = 1e-6
SLAB_TOLS = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3]
WING_AIRFOIL_ROUND_DECIMALS = 5
WING_AIRFOIL_MAX_ROUND_DECIMALS = 8
WING_AIRFOIL_MIN_SEG = 1e-5
WING_CHORD_SCALE_DECIMALS = 4
WING_ANGLE_DECIMALS = 4

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def _save_debug_stl_and_slices_plot(
    pts: np.ndarray,
    tris: np.ndarray,
    per_slice_clouds: list[np.ndarray],
    le_points: list[np.ndarray | None],
    output_directory: str | Path,
    name: str,
) -> None:
    """
    Save a debug 3D figure with STL points, first slice clouds, and LE picks.
    """

    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_path = out_dir / f"{name}_debug_stl_first_slices.png"

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # STL as semi-transparent surface for better visibility than sparse points.
    if tris.shape[0] > 0:
        max_tris = 50000
        if tris.shape[0] > max_tris:
            tri_idx = np.linspace(0, tris.shape[0] - 1, max_tris, dtype=int)
            tris_plot = tris[tri_idx]
        else:
            tris_plot = tris
        ax.plot_trisurf(
            pts[:, 0],
            pts[:, 1],
            pts[:, 2],
            triangles=tris_plot,
            color="#4C78A8",
            alpha=0.24,
            linewidth=0.0,
            shade=False,
        )
        # Proxy handle so STL appears in legend.
        ax.plot([], [], [], color="#4C78A8", lw=4, alpha=0.85, label="STL mesh")

    cmap = cm.get_cmap("viridis", max(1, len(per_slice_clouds)))
    first_slice_label = True
    for i, cloud in enumerate(per_slice_clouds):
        if cloud.shape[0] == 0:
            continue
        ax.scatter(
            cloud[:, 0],
            cloud[:, 1],
            cloud[:, 2],
            s=5,
            color=cmap(i),
            alpha=0.8,
            label="Slice intersections" if first_slice_label else None,
        )
        first_slice_label = False

    

    ax.set_title("Wing slicing ")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right",fontsize = 18)
    ax.axis('equal')
    fig.savefig(debug_path, dpi=200)
    plt.close(fig)


def _remove_consecutive_duplicate_points(poly, tol=1e-12):
    """
    Remove consecutive duplicate points in a 2xN polyline while preserving closure.
    """

    if poly.shape[1] <= 2:
        return poly

    keep = [0]
    for i in range(1, poly.shape[1]):
        if np.hypot(poly[0, i] - poly[0, keep[-1]], poly[1, i] - poly[1, keep[-1]]) > tol:
            keep.append(i)

    out = poly[:, keep]
    if out.shape[1] >= 2 and np.hypot(out[0, 0] - out[0, -1], out[1, 0] - out[1, -1]) > tol:
        out = np.hstack([out, out[:, [0]]])
    return out


def _round_airfoil_safely(poly, pref_dec=4, max_dec=8, min_seg=1e-5):
    """
    Round airfoil coordinates for CPACS while avoiding degenerate thin geometries.
    """
    
    base = _remove_consecutive_duplicate_points(np.asarray(poly, dtype=float), tol=1e-12)
    if base.shape[1] < 5:
        return base

    for dec in range(pref_dec, max_dec + 1):
        cand = np.round(base, dec)
        cand = _remove_consecutive_duplicate_points(cand, tol=10 ** (-(dec + 2)))
        if cand.shape[1] < 5:
            continue
        seg = np.hypot(np.diff(cand[0]), np.diff(cand[1]))
        if seg.size == 0:
            continue
        if np.min(seg) >= min_seg:
            return cand

    # Fallback: keep original precision and only clean exact consecutive duplicates.
    return base


def fix_airfoil_cpacs(x, z, tol_x):
    """
    Remove duplicate / near-duplicate airfoil points.

    If two points have |x1 - x2| < tol_x → keep only one
    Keep the point that is farther from the local mean

    """

    x = np.asarray(x, dtype=float)
    z = np.asarray(z, dtype=float)
    if x.size == 0:
        return x, z

    # Preserve raw extrema references before any cleanup.
    x_te_raw = float(np.max(x))
    x_le_raw = float(np.min(x))
    z_te_raw = float(np.mean(z[np.isclose(x, x_te_raw, atol=tol_x)]))
    z_le_raw = float(np.mean(z[np.isclose(x, x_le_raw, atol=tol_x)]))

    # Sort by x for robust deduplication in profile parameter space.
    idx = np.argsort(x)
    x = x[idx]
    z = z[idx]

    x_clean = [x[0]]
    z_clean = [z[0]]
    for i in range(1, len(x)):
        dx = abs(x[i] - x_clean[-1])
        dz = abs(z[i] - z_clean[-1])

        # Keep TE/LE neighborhood points to avoid losing extrema.
        near_te = (abs(x[i] - x_te_raw) <= tol_x) or (abs(x_clean[-1] - x_te_raw) <= tol_x)
        near_le = (abs(x[i] - x_le_raw) <= tol_x) or (abs(x_clean[-1] - x_le_raw) <= tol_x)

        if dx < tol_x and dz < tol_x and not (near_te or near_le):
            # Skip near-duplicate interior point.
            continue

        x_clean.append(x[i])
        z_clean.append(z[i])

    x_clean = np.asarray(x_clean, dtype=float)
    z_clean = np.asarray(z_clean, dtype=float)

    # Enforce LE/TE presence explicitly.
    if not np.any(np.isclose(x_clean, x_te_raw, atol=tol_x)):
        x_clean = np.append(x_clean, x_te_raw)
        z_clean = np.append(z_clean, z_te_raw)
    if not np.any(np.isclose(x_clean, x_le_raw, atol=tol_x)):
        x_clean = np.append(x_clean, x_le_raw)
        z_clean = np.append(z_clean, z_le_raw)

    # Restore x-sorted order after possible appends.
    idx = np.argsort(x_clean)
    x_clean = x_clean[idx]
    z_clean = z_clean[idx]

    return np.array(x_clean), np.array(z_clean)


def resample_airfoil_cpacs(
    xu, zu,
    xl, zl,
    x_te, z_te,
    x_le, z_le,
    n_points,

):
    """
    Regularize an airfoil by spline-fitting upper/lower surfaces
    and resampling with either uniform or cosine spacing in x.

    xu, zu : array-like
        Upper surface points.
    xl, zl : array-like
        Lower surface points.
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

    x_u, z_u = x_dist, z_upper
    x_l, z_l = x_dist[::-1], z_lower[::-1]
    # CPACS order
    x_te = 1.0
    x_le = 0.0
    airfoil = np.hstack([
        np.array([[x_te], [z_te]]),
        np.vstack([x_l, z_l]),
        np.array([[x_le], [z_le]]),
        np.vstack([x_u, z_u]),
        np.array([[x_te], [z_te]])
    ])
    airfoil = _round_airfoil_safely(
        airfoil,
        pref_dec=WING_AIRFOIL_ROUND_DECIMALS,
        max_dec=WING_AIRFOIL_MAX_ROUND_DECIMALS,
        min_seg=WING_AIRFOIL_MIN_SEG,
    )

    if not hasattr(resample_airfoil_cpacs, "_debug_plot_saved"):
        plt.figure()
        plt.plot(airfoil[0,:np.shape(airfoil)[1]//2], airfoil[1,:np.shape(airfoil)[1]//2], ".", color="red", label="Input upper")
        plt.plot(airfoil[0,np.shape(airfoil)[1]//2:-1], airfoil[1,np.shape(airfoil)[1]//2:-1], ".", color="blue", label="Input lower")
        plt.plot(airfoil[0, :], airfoil[1, :], "-k", linewidth=1.2, label="Resampled profile")
        plt.xlabel("x/c")
        plt.ylabel("z/c")
        plt.title("Airfoil Resampling")
        plt.legend()
        plt.axis("equal")
        plt.grid()
        plt.savefig("airfoil resampling")
        plt.close()
        resample_airfoil_cpacs._debug_plot_saved = True

    return airfoil


def extract_airfoil_surface_local(cloud_xyz, p0, n, N_BIN, TE_CUT):

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

    chord = abs(x_te - x_le)

    if chord <= 1e-8:
        return np.zeros((2, 0)), 0.0

    # Normalize ONCE
    x = (x - x_le) / chord
    z = z / chord

    airfoil = split_upper_lower_by_camber(x, z, N_BIN, TE_CUT)

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
        # inside every bin, the camber point is done
        # using the point with the maximum z and an other one wiht the minimum z
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

    # Resample
    return resample_airfoil_cpacs(
        x[upper_mask], z[upper_mask],
        x[lower_mask], z[lower_mask],
        x_te=x_te,
        z_te=z_te,
        x_le=x_le,
        z_le=z_le,
        n_points=60
    )


def intersect_triangle_with_plane_point_normal(p0, n, a, b, c, tol=INTERSECT_TOL):
    da = np.dot(n, a - p0); db = np.dot(n, b - p0); dc = np.dot(n, c - p0)
    pts = []
    def edge_int(p1,d1,p2,d2):
        if abs(d1) < tol and abs(d2) < tol:
            #Both vertices lie on the plane
            return [p1, p2]
        if abs(d1) < tol:
            #One vertex on plane
            return [p1]
        if abs(d2) < tol:
            # One vertex above, one below. There is a parametric line equation P(t)=  p1 + t*(p2 - p1)
            return [p2]
        if d1 * d2 < 0:
            t = d1 / (d1 - d2)
            return [p1 + t * (p2 - p1)]
        # Edge does not intersect plane
        return []
    pts += edge_int(a,da,b,db)
    pts += edge_int(b,db,c,dc)
    pts += edge_int(c,dc,a,da)
    if not pts:
        return []
    uniq = []
    for p in pts:
        if not any(np.linalg.norm(p - q) < 1e-10 for q in uniq):
            # Sometimes the intersection produces duplicate points
            uniq.append(p)
    return uniq


def slice_mesh_rotated_YZ(
    pts,
    tris,
    p0,
    dihedral_deg,
    sweep_deg,
    tol=INTERSECT_TOL,
):
    """
    Slice mesh with a plane orthogonal to local span direction
    defined by dihedral.
    """

    # Build span direction
    a = np.deg2rad(dihedral_deg)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(a), -np.sin(a)],
        [0, np.sin(a), np.cos(a)]
    ])

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

    return arr, e_span


def slice_mesh_at_Y(pts, tris, y_plane, tol):
    """
    Slicing with plane Y = y_plane
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
            sweep[i] = np.round((np.rint(np.degrees(np.arctan(dx / np.sqrt(dy**2 + dz**2))))),WING_ANGLE_DECIMALS)
        # ---- DIHEDRAL: YZ projection ----
        if abs(dy) < 1e-12:
            dihedral[i] = 0
        else:
            dihedral[i] = np.round((np.rint(np.degrees(np.arctan(dz / dy)))),WING_ANGLE_DECIMALS)

    # copy last value
    sweep[-1] = sweep[-2]
    dihedral[-1] = dihedral[-2]

    return sweep, dihedral


def filter_and_insert(y_vals, sweep_deg, dihedral_deg, le_pts, n_insert):
    """
    Refine wing sections for CPACS generation.

    Behavior:
    - Keep first slice.
    - In constant-angle regions, keep only boundary slices (filter interior).
    - When angles change between i and i+1, insert n_insert interpolated slices.
    - Keep the slice at the middle to be sure that also symmetrical wings are well treated.
    - Keep last slice.
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

    for i in range(len(y_vals) - 1):
        boll_add_slice = (
            np.isclose(sweep_deg[i], sweep_deg[i + 1],atol=0.1, rtol=0.0) and
            np.isclose(dihedral_deg[i], dihedral_deg[i + 1],atol=0.1, rtol=0.0) and
            (i < len(y_vals) // 2 - 1 or i > len(y_vals) // 2 + 1)
        )

        if not boll_add_slice and n_insert > 0:
            # Interpolate transition slices with linear angle evolution.
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

        # Keep i+1 when:
        # - entering or leaving a transition region
        # - always for final slice
        is_last_pair = (i == len(y_vals) - 2)
        next_changes = False if is_last_pair else not (
            np.isclose(sweep_deg[i + 1], sweep_deg[i + 2]) and
            np.isclose(dihedral_deg[i + 1], dihedral_deg[i + 2])
        )
        keep_next = (not boll_add_slice) or next_changes or is_last_pair

        if keep_next:
            y_out.append(y_vals[i + 1])
            le_out.append(le_pts[i + 1])
            sweep_out.append(sweep_deg[i + 1])
            dihedral_out.append(dihedral_deg[i + 1])

    return (
        np.array(y_out),
        np.array(sweep_out, dtype=float),
        np.array(dihedral_out, dtype=float),
        np.array(le_out),
    )


def rotate_vertical_tail(stl_file):
    """Rotate STL 90 deg around X while keeping the lowest point fixed."""

    stl_path = Path(stl_file)
    if not stl_path.exists():
        raise FileNotFoundError(f"STL file not found: {stl_path}")

    tris = load_stl_auto(str(stl_path)).astype(float)
    if tris.size == 0:
        return str(stl_path)


    pts = tris.reshape(-1, 3)
    # Use the lowest point (minimum global Z) as rotation pivot
    # so the geometry does not drift in space after rotation.
    pivot = pts[int(np.argmin(pts[:, 2]))].copy()

    rot_x_neg_90 = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, -1.0, 0.0],
        ],
        dtype=float,
    )

    rotated_pts = (pts - pivot) @ rot_x_neg_90.T + pivot
    rotated_tris = rotated_pts.reshape(tris.shape)

    out_path = stl_path.with_name(f"{stl_path.stem}_rotated_vertical_tail.stl")
    with open(out_path, "wb") as f:
        header = b"CEASIOMpy rotated vertical tail"
        f.write(header.ljust(80, b"\0"))
        f.write(struct.pack("<I", rotated_tris.shape[0]))
        for tri in rotated_tris:
            v1 = tri[1] - tri[0]
            v2 = tri[2] - tri[0]
            n = np.cross(v1, v2)
            n_norm = np.linalg.norm(n)
            if n_norm > 0.0:
                n = n / n_norm
            else:
                n = np.array([0.0, 0.0, 0.0], dtype=float)

            f.write(struct.pack("<fff", float(n[0]), float(n[1]), float(n[2])))
            for v in tri:
                f.write(struct.pack("<fff", float(v[0]), float(v[1]), float(v[2])))
            f.write(struct.pack("<H", 0))

    return str(out_path)


# ---------------------------
# MAIN
# ---------------------------


def stl2wing_main(
    stl_file: str | Path,
    setting: dict,
    output_directory: str|Path,
    name: str):

    if setting['vertical_tail']:
        stl_file = rotate_vertical_tail(stl_file)
    tri_fname = export_mesh(output_directory,stl_file,name)
    pts, tris = parse_cart3d_tri(tri_fname)

    # some initialization
    airfoil_profiles = []
    Wing_Dict = {}
    per_slice_clouds = []
    per_slice_clouds_rotate = []
    le_points = []
    le_y = []
    summary_rows = []
    per_slice_clouds_rotate = []
    airfoil_profiles = []

    # extract the setting
    EXTREME_TOL_perc_start = setting['EXTREME_TOL_perc_start']
    EXTREME_TOL_perc_end = setting['EXTREME_TOL_perc_end']
    N_Y_SLICES = setting['N_Y_SLICES']
    N_SLICE_ADDING = setting['N_SLICE_ADDING']
    TE_CUT = setting['TE_CUT']
    N_BIN = setting['N_BIN']
    # build Y sampling positions
    ymin, ymax = float(np.min(pts[:,1])), float(np.max(pts[:,1]))
    EXTREME_TOL_start = EXTREME_TOL_perc_start * (ymax - ymin)
    EXTREME_TOL_end = EXTREME_TOL_perc_end * (ymax - ymin)
    y_vals = np.linspace(ymin + EXTREME_TOL_start, ymax - EXTREME_TOL_end, N_Y_SLICES)

    # First slicing to get the LE points
    for i, y0 in enumerate(y_vals):
        cloud = slice_mesh_at_Y(pts, tris, y0, INTERSECT_TOL)

        # if still empty, skip and record None
        if cloud.shape[0] == 0:
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

    _save_debug_stl_and_slices_plot(
        pts=pts,
        tris=tris,
        per_slice_clouds=per_slice_clouds,
        le_points=le_points,
        output_directory=output_directory,
        name=name,
    )

    # build LE array
    valid_idxs = [i for i, p in enumerate(le_points) if p is not None]
    if len(valid_idxs) < 2:
        raise RuntimeError("Too few LE points found. Check mesh and N_Y_SLICES.")

    le_pts = np.vstack([le_points[i] for i in valid_idxs])

    # start to build the dictionary to create all
    # the necessary informations to generate the corresponding CPACS file.

    Wing_Dict["Transformation"] = {
                "Name_type": "Wing",
                "Name": f"{name}", 
                "X_Rot": [90, 0, 0] if setting['vertical_tail'] else [0, 0, 0],
                "X_Trasl":le_pts[0],
                "Symmetry": "",
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
    y_vals = le_pts[:,1].copy()
    # filter y_vals
    y_vals,sweep_deg,dihedral_deg,le_pts = filter_and_insert(y_vals, sweep_deg, dihedral_deg,le_pts, N_SLICE_ADDING)
    # slice with plane that are rotated by the dihedral angle.

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

        airfoil_xz, chord = extract_airfoil_surface_local(
            cloud_rot,
            p0=lep,
            n=n_rot,
            N_BIN = N_BIN,
            TE_CUT= TE_CUT,
        )

        # Store in Wing_Dict
        if i==0:
            Wing_Dict[f'Section{i}'] = {
                'x_scal': round(chord, WING_CHORD_SCALE_DECIMALS),
                'y_scal': 1,
                'z_scal': round(chord, WING_CHORD_SCALE_DECIMALS),
                'x_trasl': 0,
                'Span': 0,
                'Airfoil': 'Airfoil',
                'Airfoil_coordinates': airfoil_xz,
                'Sweep_loc': 0,
                'Sweep_angle': round(float(sweep_deg[i]), WING_ANGLE_DECIMALS),
                'Dihedral_angle': round(float(dihedral_deg[i]), WING_ANGLE_DECIMALS)
            }

        else:
            Wing_Dict[f'Section{i}'] = {
                'x_scal': round(chord, WING_CHORD_SCALE_DECIMALS),
                'y_scal': 1,
                'z_scal': round(chord, WING_CHORD_SCALE_DECIMALS),
                'x_trasl': 0,
                'Span': abs((y_vals[i]-y_vals[i-1])/np.cos(np.deg2rad(dihedral_deg[i]))),
                'Airfoil': 'Airfoil',
                'Airfoil_coordinates': airfoil_xz,
                'Sweep_loc': 0,
                'Sweep_angle': round(float(sweep_deg[i]), WING_ANGLE_DECIMALS),
                'Dihedral_angle': round(float(dihedral_deg[i]), WING_ANGLE_DECIMALS)
            }

        airfoil_profiles.append(airfoil_xz)

    # eliminate the rotate vertical tail stl file if present
    if setting['vertical_tail']:
        os.remove(stl_file)

    return Wing_Dict

