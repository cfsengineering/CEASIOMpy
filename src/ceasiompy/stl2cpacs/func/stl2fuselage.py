
# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.interpolate import PchipInterpolator
from ceasiompy.stl2cpacs.stl2cpacs import export_mesh, parse_cart3d_tri
from pathlib import Path

# ---------------------------
# CONFIG
# ---------------------------

INTERSECT_TOL = 1e-6
SLAB_TOLS = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3]
DUPLICATE_YZ_TOL = 1e-8
# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def _save_debug_stl_and_slices_plot(
    pts: np.ndarray,
    tris: np.ndarray,
    per_slice_clouds: list[np.ndarray],
    ref_points: list[np.ndarray | None],
    output_directory: str | Path,
    name: str,
    view_elev: float = 0,
    view_azim: float = 0.0,
    interactive: bool = False,
) -> None:
    """
    Save a debug 3D figure with STL surface, first slice clouds and reference picks.
    """

    out_dir = Path(output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_path = out_dir / f"{name}_debug_stl_first_slices.png"

    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")

    if tris.shape[0] > 0:

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

    ref_valid = [pt for pt in ref_points if pt is not None]
    if ref_valid:
        ref_arr = np.vstack(ref_valid)
        ax.scatter(
            ref_arr[:, 0],
            ref_arr[:, 1],
            ref_arr[:, 2],
            s=24,
            c="red",
            alpha=0.95,
            label="Reference points",
        )

    # Camera setup: azim=0 gives a front view aligned with X direction.
    ax.view_init(elev=view_elev, azim=view_azim)
    ax.set_title("Fuselage slicing")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(debug_path, dpi=200)
    if interactive:
        plt.show()
    plt.close(fig)


def resample_fuselage_cpacs(
    yr, zr,
    yl, zl,
    y_bot, z_bot,
    y_top, z_top,
    n_points,
    use_cosine_spacing=False,
):
    """
    Regularize a fuselage cross-section using PCHIP interpolation.

    CPACS order:
    bottom → right side → top → left side → bottom
    """

    yr = np.asarray(yr)
    zr = np.asarray(zr)
    yl = np.asarray(yl)
    zl = np.asarray(zl)

    def _prepare_strictly_increasing(z_in, y_in, tol=1e-9):
        """
        Sort by z (bottom -> top) and enforce strict increase with a tiny epsilon.
        This keeps the original side curvature, even for complex shapes.
        """

        z_in = np.asarray(z_in, dtype=float)
        y_in = np.asarray(y_in, dtype=float)

        # Stable sort preserves relative ordering for equal z values.
        order = np.argsort(z_in, kind="mergesort")
        z_sorted = z_in[order]
        y_sorted = y_in[order]

        # Final strict-increase pass (numerical safety).
        for i in range(1, z_sorted.size):
            if z_sorted[i] <= z_sorted[i - 1]:
                z_sorted[i] = z_sorted[i - 1] + tol

        return z_sorted, y_sorted

    # -------------------------------------------------
    # 1) Augment splines with extrema (CRITICAL)
    # -------------------------------------------------
    zr_s = np.hstack([z_bot, zr, z_top])
    yr_s = np.hstack([y_bot, yr, y_top])

    zl_s = np.hstack([z_bot, zl, z_top])
    yl_s = np.hstack([y_bot, yl, y_top])

    # Ensure strict monotonicity for PCHIP while preserving original side curvature.
    zr_s, yr_s = _prepare_strictly_increasing(zr_s, yr_s)
    zl_s, yl_s = _prepare_strictly_increasing(zl_s, yl_s)

    # -------------------------------------------------
    # 2) Build splines
    # -------------------------------------------------
    pchip_right = PchipInterpolator(zr_s, yr_s, extrapolate=False)
    pchip_left = PchipInterpolator(zl_s, yl_s, extrapolate=False)

    # -------------------------------------------------
    # 3) Build z distribution
    # -------------------------------------------------
    n_half = n_points // 2

    if use_cosine_spacing:
        beta = np.linspace(0.0, np.pi, n_half)
        z_dist = z_bot + (z_top - z_bot) * 0.5 * (1 - np.cos(beta))
    else:
        z_dist = np.linspace(z_bot, z_top, n_half, endpoint=True)

    # Remove extrema (added explicitly later)
    z_mid = z_dist[1:-1]

    # -------------------------------------------------
    # 4) Evaluate splines
    # -------------------------------------------------
    y_right = pchip_right(z_mid)
    y_left = pchip_left(z_mid)

    # Enforce strict side ordering at each z:
    # first branch is always +y side, second branch always -y side.
    y_pos = np.maximum(y_right, y_left)
    y_neg = np.minimum(y_right, y_left)

    # -------------------------------------------------
    # 5) Assemble CPACS closed loop
    # -------------------------------------------------
    Airfoil = np.hstack([
        np.array([[y_bot], [z_bot]]),
        np.vstack([y_pos, z_mid]),
        np.array([[y_top], [z_top]]),
        np.vstack([y_neg[::-1], z_mid[::-1]]),
        np.array([[y_bot], [z_bot]])
    ])
    Airfoil = np.round(Airfoil, 3)

    if not hasattr(resample_fuselage_cpacs, "_debug_plot_saved"):
        plt.figure()
        plt.plot(yr, zr, ".", color="red", label="Input right (+y)")
        plt.plot(yl, zl, ".", color="blue", label="Input left (-y)")
        plt.plot(Airfoil[0, :], Airfoil[1, :], "-k", linewidth=1.2, label="Resampled profile")
        plt.xlabel("y")
        plt.ylabel("z")
        plt.title("Fuselage Resampling")
        plt.legend()
        plt.axis("equal")
        plt.grid()
        plt.savefig("fuselage resampling")
        plt.close()
        resample_fuselage_cpacs._debug_plot_saved = True

    return Airfoil


def deduplicate_yz_points(y, z, tol=DUPLICATE_YZ_TOL):
    """Remove duplicate/near-duplicate points in (y, z) with a tolerance grid."""

    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    if y.size == 0:
        return y, z

    q = np.round(np.column_stack((y, z)) / tol).astype(np.int64)
    _, idx = np.unique(q, axis=0, return_index=True)
    idx = np.sort(idx)
    return y[idx], z[idx]


def find_top_bottom_near_centerline(y, z, y_tol_frac=0.08, z_band_frac=0.02):
    """
    Find top and bottom points using only points close to symmetry plane (y ~= 0).

    Steps:
    1) Select points with |y| <= y_tol.
    2) Find highest and lowest z inside that subset.
    3) If multiple points are close to those extrema (z band), average them.
    4) Return indices of original points closest to these averaged top/bottom points.
    """

    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)

    if y.size == 0:
        return 0, 0

    y_span = max(float(np.ptp(y)), 1e-12)
    z_span = max(float(np.ptp(z)), 1e-12)

    y_tol = y_tol_frac * y_span
    z_band = max(z_band_frac * z_span, 1e-12)

    # 1) points near y == 0
    center_mask = np.abs(y) <= y_tol

    # If too few points, enlarge tolerance.
    if np.count_nonzero(center_mask) < 3:
        center_mask = np.abs(y) <= (2.0 * y_tol)

    # If still too few, fall back to all points.
    if np.count_nonzero(center_mask) < 2:
        center_mask = np.ones_like(y, dtype=bool)

    zc = z[center_mask]

    # 2) raw top and bottom in center subset
    z_top_raw = float(np.max(zc))
    z_bot_raw = float(np.min(zc))

    # 3) average all points close to those extrema
    top_group = center_mask & (np.abs(z - z_top_raw) <= z_band)
    bot_group = center_mask & (np.abs(z - z_bot_raw) <= z_band)

    if np.count_nonzero(top_group) == 0:
        top_group = center_mask & np.isclose(z, z_top_raw)
    if np.count_nonzero(bot_group) == 0:
        bot_group = center_mask & np.isclose(z, z_bot_raw)

    y_top = 0.0
    z_top = float(np.mean(z[top_group]))
    y_bot = 0.0
    z_bot = float(np.mean(z[bot_group]))

    # 4) pick nearest original points (indices) to constrained centerline extrema
    i_top = int(np.argmin((y - y_top) ** 2 + (z - z_top) ** 2))
    i_bot = int(np.argmin((y - y_bot) ** 2 + (z - z_bot) ** 2))

    return i_top, i_bot


def extract_airfoil_surface_local(cloud_xyz, p0, n):
    if cloud_xyz.shape[0] < 10:
        return np.zeros((2, 0)), 0.0

    # -------------------------------------------------
    # Define local in-plane basis (Y, Z)
    # -------------------------------------------------
    e1 = np.array([0.0, 1.0, 0.0])
    e2 = np.array([0.0, 0.0, 1.0])

    # -------------------------------------------------
    # Project cloud into slicing plane
    # -------------------------------------------------
    local = np.array([
        [
            np.dot(p - p0, e1),
            np.dot(p - p0, e2),
        ]
        for p in cloud_xyz
    ])

    y = local[:, 0]
    z = local[:, 1]
    # Left/right and top/bottom extrema detection
    i_le = np.argmin(y)
    i_te = np.argmax(y)
    i_up, i_low = find_top_bottom_near_centerline(
        y, z, y_tol_frac=0.08, z_band_frac=0.02
    )
    z_up = z[i_up]
    z_low = z[i_low]
    y_le = y[i_le]
    y_te = y[i_te]

    width = y_te - y_le
    height = z_up - z_low

    if width <= 1e-8 or height <= 1e-8:
        return np.zeros((2, 0)), 0.0

    # Normalize around section center so profile is centered at origin.
    y_center = 0.5 * (y_le + y_te)
    z_center = 0.5 * (z_up + z_low)
    y = (y - y_center) / width
    z = (z - z_center) / height

    # Enforce exact lateral normalization: min(y)=-0.5 and max(y)=+0.5
    y_min = float(np.min(y))
    y_max = float(np.max(y))
    y_span = y_max - y_min
    if y_span > 1e-12:
        y = (y - 0.5 * (y_max + y_min)) / y_span

    # Enforce exact extrema after normalization:
    # bottom -> (y=0, z=-0.5), top -> (y=0, z=+0.5)
    i_up, i_low = find_top_bottom_near_centerline(
        y, z, y_tol_frac=0.08, z_band_frac=0.02
    )
    i_ymax = int(np.argmax(y))
    i_ymin = int(np.argmin(y))
    y[i_ymax] = 0.5
    y[i_ymin] = -0.5
    y[i_up] = 0.0
    y[i_low] = 0.0

    # Remove duplicate points before splitting the surface.
    y, z = deduplicate_yz_points(y, z, tol=DUPLICATE_YZ_TOL)
    if y.size < 10:
        return np.zeros((2, 0)), 0.0

    # Recompute extrema after deduplication.
    i_up, i_low = find_top_bottom_near_centerline(
        y, z, y_tol_frac=0.08, z_band_frac=0.02
    )
    y_top_n, z_top_n = y[i_up], z[i_up]
    y_bot_n, z_bot_n = y[i_low], z[i_low]

    n = 10  # number of bins for camber line
    airfoil = split_fuselage_left_right_by_centerline(
        y, z, y_bot_n, z_bot_n, y_top_n, z_top_n, n
    )
    return airfoil, [width, height]


def split_fuselage_left_right_by_centerline(
    y_raw,
    z_raw,
    y_bot,
    z_bot,
    y_top,
    z_top,
    n_bins
):
    """
    Split fuselage cross-section into right (+y) and left (-y) sides
    using a centerline computed from max/min y per z-bin.

    Top and bottom extrema are excluded from left/right classification.
    """

    y = np.asarray(y_raw)
    z = np.asarray(z_raw)

    # Sort by z (vertical)
    idx = np.argsort(z)
    y = y[idx]
    z = z[idx]

    # --- Detect bottom / top on symmetry plane (y ~= 0) ---
    i_top, i_bot = find_top_bottom_near_centerline(
        y, z, y_tol_frac=0.08, z_band_frac=0.02
    )
    z_top, y_top = z[i_top], y[i_top]
    z_bot, y_bot = z[i_bot], y[i_bot]

    # --- Remove top & bottom from processing ---
    mask_mid = np.ones(len(z), dtype=bool)
    mask_mid[[i_bot, i_top]] = False

    y_mid = y[mask_mid]
    z_mid = z[mask_mid]

    # --- Build bins only in interior ---
    bins = np.linspace(z_bot, z_top, n_bins + 1)

    center_z = []
    center_y = []

    for i in range(n_bins):
        mask = (z_mid >= bins[i]) & (z_mid < bins[i + 1])
        if np.count_nonzero(mask) < 2:
            continue

        y_bin = y_mid[mask]
        z_bin = z_mid[mask]

        i_r = np.argmax(y_bin)
        i_l = np.argmin(y_bin)

        center_y.append(0.5 * (y_bin[i_r] + y_bin[i_l]))
        center_z.append(0.5 * (z_bin[i_r] + z_bin[i_l]))

    center_y = np.asarray(center_y)
    center_z = np.asarray(center_z)

    # --- Interpolate centerline over interior points only ---
    y_center_mid = np.interp(z_mid, center_z, center_y)

    # --- Classification (excluding extrema) ---
    right_mask_mid = y_mid > y_center_mid
    left_mask_mid = y_mid < y_center_mid

    # --- Rebuild full masks ---
    right_mask = np.zeros(len(y), dtype=bool)
    left_mask = np.zeros(len(y), dtype=bool)

    right_mask[np.where(mask_mid)[0][right_mask_mid]] = True
    left_mask[np.where(mask_mid)[0][left_mask_mid]] = True

    if not hasattr(split_fuselage_left_right_by_centerline, "_debug_plot_saved"):
        plt.figure()
        for i, zb in enumerate(bins):
            plt.hlines(
                zb,
                -0.6,
                0.6,
                colors="black",
                linestyles="--",
                linewidth=1.2,
                alpha=1,
                label="Bin limits" if i == 0 else None,
            )
        plt.plot(y[right_mask], z[right_mask], ".", color="red", label="Right (+y)")
        plt.plot(y[left_mask], z[left_mask], ".", color="blue", label="Left (-y)")
        plt.plot(center_y, center_z, "o", color="orange", ms=4, label="Center points")
        plt.plot(y_center_mid, z_mid, "-k", label="Center line")
        plt.xlabel("y")
        plt.ylabel("z")
        plt.title("Fuselage Points Classification")
        plt.legend()
        plt.axis("equal")
        plt.grid()
        plt.savefig("fuselage splitting")
        plt.close()
        split_fuselage_left_right_by_centerline._debug_plot_saved = True

    N_RESAMPLE_POINTS = 60
    return resample_fuselage_cpacs(
        y[right_mask], z[right_mask],
        y[left_mask],  z[left_mask],
        y_bot, z_bot,
        y_top, z_top,
        N_RESAMPLE_POINTS,
        use_cosine_spacing=True,
    )


def intersect_triangle_with_plane_point_normal(p0, n, a, b, c, tol=INTERSECT_TOL):
    da = np.dot(n, a - p0)
    db = np.dot(n, b - p0)
    dc = np.dot(n, c - p0)
    pts = []

    def edge_int(p1, d1, p2, d2):
        if abs(d1) < tol and abs(d2) < tol:
            # Both vertices lie on the plane
            return [p1, p2]
        if abs(d1) < tol:
            # One vertex on plane
            return [p1]
        if abs(d2) < tol:
            # One vertex above, one below.
            # There is a parametric line equation P(t)=  p1 + t*(p2 - p1)
            return [p2]
        if d1 * d2 < 0:
            t = d1 / (d1 - d2)
            return [p1 + t * (p2 - p1)]
        # Edge does not intersect plane
        return []

    pts += edge_int(a, da, b, db)
    pts += edge_int(b, db, c, dc)
    pts += edge_int(c, dc, a, da)
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
    debug=False,
):
    """
    Slice mesh with a plane orthogonal to local direction
    defined by dihedral.
    """

    # Build local direction
    a = np.deg2rad(dihedral_deg)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(a), -np.sin(a)],
        [0, np.sin(a), np.cos(a)]
    ])

    RR = Rx

    e_span = RR @ np.array([1.0, 0.0, 0.0])
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
            f"Rotated slice plane (dihedral={dihedral_deg:.2f} deg)"
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
    n = np.array([1.0, 0.0, 0.0])
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


def compute_local_angles_from_ref(ref_pts):
    """
    Compute sweep and dihedral from section reference points.
    Sweep is defined in the XY plane.
    Dihedral is defined in the XZ plane.
    """

    ref_pts = np.asarray(ref_pts)
    M = ref_pts.shape[0]
    if M < 2:
        return np.array([]), np.array([])

    sweep = np.zeros(M, dtype=int)
    dihedral = np.zeros(M, dtype=int)

    for i in range(M - 1):
        dx = ref_pts[i+1, 0] - ref_pts[i, 0]
        dy = ref_pts[i+1, 1] - ref_pts[i, 1]
        dz = ref_pts[i+1, 2] - ref_pts[i, 2]

        # ---- SWEEP: XY projection ----
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            sweep[i] = 0
        else:
            sweep[i] = int(np.rint(np.degrees(np.arctan2(dy, dx))))

        # ---- DIHEDRAL: XZ projection ----
        if abs(dx) < 1e-12 and abs(dz) < 1e-12:
            dihedral[i] = 0
        else:
            dihedral[i] = int(np.rint(np.degrees(np.arctan2(dz, dx))))

    # copy last value
    sweep[-1] = sweep[-2]
    dihedral[-1] = dihedral[-2]

    return sweep, dihedral


def insert_slices(y_vals, sweep_deg, dihedral_deg, ref_pts, n_insert):
    """
    Keep all original slices and only insert new slices at angle transitions.
    """

    y_vals = np.asarray(y_vals, dtype=float)
    sweep_deg = np.asarray(sweep_deg, dtype=float)
    dihedral_deg = np.asarray(dihedral_deg, dtype=float)
    ref_pts = np.asarray(ref_pts, dtype=float)

    # Initialize output arrays with the first slice
    y_out = [y_vals[0]]
    sweep_out = [sweep_deg[0]]
    dihedral_out = [dihedral_deg[0]]
    ref_out = [ref_pts[0]]
    is_inserted = [False]

    for i in range(len(y_vals) - 1):
        # Transition if either sweep OR dihedral changes.
        sweep_changed = not np.isclose(sweep_deg[i], sweep_deg[i + 1], atol=1e-9)
        dihedral_changed = not np.isclose(dihedral_deg[i], dihedral_deg[i + 1], atol=1e-9)
        has_transition = sweep_changed or dihedral_changed

        # Insert interpolated slices only at transitions.
        if has_transition and n_insert > 0:

            for k in range(1, n_insert + 1):
                t = k / (n_insert + 1)
                y_new = (1 - t) * y_vals[i] + t * y_vals[i + 1]
                ref_new = (1 - t) * ref_pts[i] + t * ref_pts[i + 1]
                sweep_new = (1 - t) * sweep_deg[i] + t * sweep_deg[i + 1]
                dihedral_new = (1 - t) * dihedral_deg[i] + t * dihedral_deg[i + 1]
                y_out.append(y_new)
                ref_out.append(ref_new)
                sweep_out.append(sweep_new)
                dihedral_out.append(dihedral_new)
                is_inserted.append(True)

        # Always keep the next original slice.
        y_out.append(y_vals[i + 1])
        ref_out.append(ref_pts[i + 1])
        sweep_out.append(sweep_deg[i + 1])
        dihedral_out.append(dihedral_deg[i + 1])
        is_inserted.append(False)

    return (
        np.array(y_out),
        np.rint(sweep_out).astype(int),
        np.rint(dihedral_out).astype(int),
        np.array(ref_out),
        np.array(is_inserted, dtype=bool),
    )


def compute_section_centers(clouds):
    """Return per-slice geometric centers as Nx3 array."""

    centers = []
    for cloud in clouds:
        if cloud.shape[0] == 0:
            continue
        centers.append([
            np.mean(cloud[:, 0]),
            0.5 * (np.min(cloud[:, 1]) + np.max(cloud[:, 1])),
            0.5 * (np.min(cloud[:, 2]) + np.max(cloud[:, 2])),
        ])
    return np.asarray(centers, dtype=float)


def plot_profile_diagnostics(airfoil_profiles):
    """2D debug plots to identify section continuity anomalies."""

    if not airfoil_profiles:
        return

    n_sec = len(airfoil_profiles)
    idx = np.arange(n_sec)
    amp_y = np.array([np.max(np.abs(p[0])) for p in airfoil_profiles])
    amp_z = np.array([np.max(np.abs(p[1])) for p in airfoil_profiles])

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    colors = cm.viridis(np.linspace(0, 1, n_sec))
    for i, p in enumerate(airfoil_profiles):
        axes[0].plot(p[0], p[1], color=colors[i], lw=1.2, alpha=0.8, label=f"S{i}")
        axes[0].plot(p[0][0], p[1][0], "o", color=colors[i], ms=2)
    axes[0].set_title("Section Profiles Overlay")
    axes[0].set_xlabel("y")
    axes[0].set_ylabel("z")
    axes[0].axis("equal")
    axes[0].grid(True)
    if n_sec <= 12:
        axes[0].legend(fontsize=7, ncol=2)

    axes[1].plot(idx, amp_y, "-o", label="max |y|")
    axes[1].plot(idx, amp_z, "-o", label="max |z|")
    axes[1].set_title("Section Trend Check")
    axes[1].set_xlabel("Section index")
    axes[1].set_ylabel("Amplitude")
    axes[1].grid(True)
    axes[1].legend()

    plt.tight_layout()
    plt.show()


# ---------------------------
# MAIN
# ---------------------------


def stl2fuselage_main(stl_file: str | Path,
                      setting: dict,
                      output_directory: str | Path,
                      name: str
                      ):

    tri_fname = export_mesh(output_directory, stl_file, name)
    pts, tris = parse_cart3d_tri(tri_fname)

    # some initialization
    airfoil_profiles = []
    Fuse_Dict = {}
    per_slice_clouds = []
    bottom_points = []
    slice_x = []
    airfoil_profiles = []
    center_prev = None
    per_slice_clouds_used = []
    base_idx = 0

    # extract the setting
    EXTREME_TOL_perc_start = setting['EXTREME_TOL_perc_start']
    EXTREME_TOL_perc_end = setting['EXTREME_TOL_perc_end']
    N_X_SLICES = setting['N_X_SLICES']
    N_SLICE_ADDING = setting['N_SLICE_ADDING']

    # build X sampling positions
    xmin, xmax = float(np.min(pts[:, 0])), float(np.max(pts[:, 0]))
    EXTREME_TOL_start = EXTREME_TOL_perc_start * (xmax - xmin)
    EXTREME_TOL_end = EXTREME_TOL_perc_end * (xmax - xmin)
    x_start = xmin + EXTREME_TOL_start
    x_end = xmax - EXTREME_TOL_end
    x_vals_base = np.linspace(x_start, x_end, N_X_SLICES, dtype=float)

    # refine in the nose and tail regions
    # Refine first and last 10% of effective fuselage length with +5 slices each.
    extra_slices = 5
    refine_frac = 0.1
    x_len = x_end - x_start
    nose_end = x_start + refine_frac * x_len
    tail_start = x_end - refine_frac * x_len

    # Internal points only: avoid duplicating x_start/x_end.
    x_nose_extra = np.linspace(x_start, nose_end, extra_slices + 2, dtype=float)[1:-1]
    x_tail_extra = np.linspace(tail_start, x_end, extra_slices + 2, dtype=float)[1:-1]

    x_vals = np.unique(np.concatenate([x_vals_base, x_nose_extra, x_tail_extra]))

    # First slicing to get one reference point per slice (bottom point)
    for i, x0 in enumerate(x_vals):
        cloud = slice_mesh_at_Y(pts, tris, x0, INTERSECT_TOL)

        # if still empty, skip and record None
        if cloud.shape[0] == 0:
            per_slice_clouds.append(np.zeros((0, 3)))
            bottom_points.append(None)
            slice_x.append(x0)
            continue

        # Bottom point: point with minimum Z in the slice
        min_idx = int(np.argmin(cloud[:, 2]))
        bottom_pt = cloud[min_idx].copy()

        per_slice_clouds.append(cloud)
        bottom_points.append(bottom_pt)
        slice_x.append(x0)

    _save_debug_stl_and_slices_plot(
        pts=pts,
        tris=tris,
        per_slice_clouds=per_slice_clouds,
        ref_points=bottom_points,
        output_directory=output_directory,
        name=name,
        view_elev=float(setting.get("DEBUG_PLOT_ELEV", 12.0)),
        view_azim=float(setting.get("DEBUG_PLOT_AZIM", 0.0)),
        interactive=bool(setting.get("DEBUG_PLOT_INTERACTIVE", False)),
    )

    # build reference-point array
    valid_idxs = [i for i, p in enumerate(bottom_points) if p is not None]
    if len(valid_idxs) < 2:
        raise RuntimeError("Too few bottom reference points found. Check mesh and N_X_SLICES.")

    per_slice_clouds_valid = [per_slice_clouds[i] for i in valid_idxs]
    center_pts = compute_section_centers(per_slice_clouds_valid)
    # start to build the dictionary.
    Fuse_Dict["Transformation"] = {
                "Name_type": "Fuselage",
                "Name": str(name),
                "X_Rot": [0, 0, 0],
                "Symmetry": "",
                "abs_system": True,
                "Relative_dih": 0,
                "Relative_Twist": 0,
                "ParentUid": 0,
                "reference_length": 0,
                "idx_engine": None,
                "Length": xmax - xmin
            }

    # compute sweep & dihedral along section centers
    sweep_deg, dihedral_deg = compute_local_angles_from_ref(center_pts)

    x_vals, sweep_deg, dihedral_deg, center_pts, is_inserted = insert_slices(
        center_pts[:, 0],
        sweep_deg,
        dihedral_deg,
        center_pts,
        N_SLICE_ADDING,
    )

    for i, x0 in enumerate(x_vals):
        center_ref = center_pts[i]

        if is_inserted[i]:
            cloud = slice_mesh_at_Y(pts, tris, x0, INTERSECT_TOL)
            if cloud.shape[0] == 0:
                fb = min(max(base_idx - 1, 0), len(per_slice_clouds_valid) - 1)
                cloud = per_slice_clouds_valid[fb]
        else:
            cloud = per_slice_clouds_valid[base_idx]
            base_idx += 1

        per_slice_clouds_used.append(cloud)

        # slice and rotate mesh
        cloud_rot, n_rot = slice_mesh_rotated_YZ(
            pts,
            tris,
            p0=center_ref,
            dihedral_deg=dihedral_deg[i],
            sweep_deg=sweep_deg[i],
            tol=INTERSECT_TOL
        )

        airfoil_xz, Scaling = extract_airfoil_surface_local(
            cloud_rot,
            p0=center_ref,
            n=n_rot,
        )

        # Section center in the slice plane (global coordinates)
        y_center = center_ref[1]
        z_center = center_ref[2]

        # Store in Fuse_Dict
        if i == 0:
            Fuse_Dict[f'Section{i}'] = {
                'x_scal': 1,
                'y_scal': round(Scaling[0], 2),
                'z_scal': round(Scaling[1], 2),
                'x_loc': x0,
                'y_trasl': 0.0,
                'z_trasl': 0.0,
                'x_rot': 0,
                'y_rot': 0,
                'z_rot': 0,
                'Span': 0,
                'Airfoil': 'Airfoil',
                'Airfoil_coordinates': airfoil_xz,
                'Sweep_loc': 0,
                'Sweep_angle': 0,
                'Dihedral_angle': 0
            }
            Fuse_Dict["Transformation"]["X_Trasl"] = [
                x0,
                y_center,
                z_center,
            ]
            center_prev = (y_center, z_center)

        else:
            Fuse_Dict[f'Section{i}'] = {
                'x_scal': 1,
                'y_scal': round(Scaling[0], 2),
                'z_scal': round(Scaling[1], 2),
                'x_loc': x0-x_start,
                'y_trasl': y_center - center_prev[0],
                'z_trasl': z_center - center_prev[1],
                'x_rot': 0,
                'y_rot': 0,
                'z_rot': 0,
                'Airfoil': 'Airfoil',
                'Airfoil_coordinates': airfoil_xz,
                'Sweep_loc': 0,
                'Sweep_angle': 0,
                'Dihedral_angle': 0
            }

        airfoil_profiles.append(airfoil_xz)

    return Fuse_Dict
