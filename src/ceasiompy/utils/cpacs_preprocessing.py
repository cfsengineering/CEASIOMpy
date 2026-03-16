from pathlib import Path
import xml.etree.ElementTree as ET
import math

from cpacspy.cpacspy import CPACS

def _strip_ns(tag: str) -> str:
    """Strip XML namespace from a tag name."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_child(parent: ET.Element, name: str):
    """Find direct child by local (namespace-free) tag name."""
    for child in parent:
        if _strip_ns(child.tag) == name:
            return child
    return None


def _find_path(root: ET.Element, parts: list[str]):
    """Follow a direct-child path, e.g. ['vehicles', 'profiles', 'wingAirfoils']."""
    cur = root
    for p in parts:
        cur = _find_child(cur, p)
        if cur is None:
            return None
    return cur


def _parse_vector(text: str | None) -> list[float]:
    """Parse CPACS mapType='vector' text into list[float]."""
    if not text:
        return []
    out = []
    for t in text.replace("\n", "").split(";"):
        t = t.strip()
        if t:
            out.append(float(t))
    return out


def _to_vector(values: list[float]) -> str:
    """Convert list[float] back to CPACS vector string format."""
    return ";".join(f"{v:.8g}" for v in values) + ";"


def _interp_at_x(x0, y0, z0, x1, y1, z1, x_target):
    if math.isclose(x1, x0, rel_tol=0.0, abs_tol=1e-15):
        return x_target, y0, z0
    t = (x_target - x0) / (x1 - x0)
    return x_target, y0 + t * (y1 - y0), z0 + t * (z1 - z0)


def _clip_lower_te_to_le(x_vals, y_vals, z_vals, x_cut):
    # Lower branch follows CPACS order TE -> LE.
    # Remove aft part (x > x_cut), then add one interpolated cut point at x_cut.
    i_in = next((i for i, x in enumerate(x_vals) if x <= x_cut), None)
    if i_in is None:
        return [x_cut], [y_vals[-1]], [z_vals[-1]]
    if i_in == 0:
        return x_vals[:], y_vals[:], z_vals[:]

    xi, yi, zi = _interp_at_x(
        x_vals[i_in - 1],
        y_vals[i_in - 1],
        z_vals[i_in - 1],
        x_vals[i_in],
        y_vals[i_in],
        z_vals[i_in],
        x_cut,
    )
    return [xi] + x_vals[i_in:], [yi] + y_vals[i_in:], [zi] + z_vals[i_in:]


def _clip_upper_le_to_te(x_vals, y_vals, z_vals, x_cut):
    # Upper branch follows CPACS order LE -> TE.
    # Remove aft part (x > x_cut), then add one interpolated cut point at x_cut.
    i_out = next((i for i, x in enumerate(x_vals) if x > x_cut), None)
    if i_out is None:
        return x_vals[:], y_vals[:], z_vals[:]
    if i_out == 0:
        return [x_cut], [y_vals[0]], [z_vals[0]]

    xi, yi, zi = _interp_at_x(
        x_vals[i_out - 1],
        y_vals[i_out - 1],
        z_vals[i_out - 1],
        x_vals[i_out],
        y_vals[i_out],
        z_vals[i_out],
        x_cut,
    )
    return x_vals[:i_out] + [xi], y_vals[:i_out] + [yi], z_vals[:i_out] + [zi]


def cut_trailing_edge_airfoils(airfoils, te_cut):
    """
    Cut trailing edge at x_cut = x_te - te_cut for each airfoil and rebuild
    each profile as:
    TE -> lower side -> LE -> upper side -> TE.

    Keep distinct lower/upper TE cut points and close the polyline by
    repeating TE-lower at the end.
    Coordinates are then renormalized so x_cut -> 1 for each profile.
    """
    tol = 1e-12

    def clip_lower(points, x_cut):
        """Clip lower branch ordered TE->LE to x <= x_cut."""
        i_in = next((i for i, (xp, _, _) in enumerate(points) if xp <= x_cut), None)
        if i_in is None:
            _, yp, zp = points[-1]
            return [(x_cut, yp, zp)]
        if i_in == 0:
            return points[:]
        cut = _interp_at_x(*points[i_in - 1], *points[i_in], x_cut)
        return [cut] + points[i_in:]

    def clip_upper(points, x_cut):
        """Clip upper branch ordered LE->TE to x <= x_cut."""
        i_out = next((i for i, (xp, _, _) in enumerate(points) if xp > x_cut), None)
        if i_out is None:
            return points[:]
        if i_out == 0:
            _, yp, zp = points[0]
            return [(x_cut, yp, zp)]
        cut = _interp_at_x(*points[i_out - 1], *points[i_out], x_cut)
        return points[:i_out] + [cut]

    out = []
    for airfoil in airfoils:
        points = list(zip(airfoil["x"], airfoil["y"], airfoil["z"]))
        if len(points) < 2:
            out.append(dict(airfoil))
            continue

        x_te = points[0][0]
        x_cut = x_te - te_cut
        if x_cut <= 0.0:
            raise ValueError(
                f"Invalid te_cut={te_cut} for airfoil {airfoil.get('uid')}: "
                f"x_te={x_te}, x_cut={x_cut}."
            )

        i_le = min(range(len(points)), key=lambda i: points[i][0])
        lower = clip_lower(points[: i_le + 1], x_cut)   # TE -> LE
        upper = clip_upper(points[i_le:], x_cut)        # LE -> TE

        same_le = (
            math.isclose(lower[-1][0], upper[0][0], rel_tol=0.0, abs_tol=tol)
            and math.isclose(lower[-1][1], upper[0][1], rel_tol=0.0, abs_tol=tol)
            and math.isclose(lower[-1][2], upper[0][2], rel_tol=0.0, abs_tol=tol)
        )
        merged = lower + (upper[1:] if same_le else upper)

        # Close polyline at the trailing edge:
        # ... -> TE_upper -> TE_lower
        te_lower = lower[0]
        merged.append(te_lower)

        scale = 1.0
        new_x = [xp * scale for xp, _, _ in merged]
        new_y = [yp * scale for _, yp, _ in merged]
        new_z = [zp * scale for _, _, zp in merged]
        import matplotlib.pyplot as plt
        plt.figure()
        for i in range(len(new_x) - 1):
            plt.plot(new_x[i : i + 2], new_z[i : i + 2], "-k", linewidth=1.0)
        plt.plot(new_x[0], new_z[0], "go", markersize=6, label="start")
        plt.plot(new_x[-1], new_z[-1], "ro", markersize=6, label="end")
        plt.title(f"Airfoil {airfoil.get('uid')} after TE cut")
        plt.xlabel('x-coordinate')
        plt.ylabel('z-coordinate')
        plt.grid()
        plt.axis('equal')
        plt.legend()
        plt.show()
        
        new_airfoil = dict(airfoil)
        new_airfoil["x"] = new_x
        new_airfoil["y"] = new_y
        new_airfoil["z"] = new_z
        new_airfoil["points"] = list(zip(new_x, new_y, new_z))
        out.append(new_airfoil)

    return out


def load_wing_airfoils(root: ET.Element):
    """Load wing airfoils from CPACS profile section into Python dictionaries."""
    airfoils_node = _find_path(root, ["vehicles", "profiles", "wingAirfoils"])
    if airfoils_node is None:
        return []

    data = []
    for wa in airfoils_node:
        if _strip_ns(wa.tag) != "wingAirfoil":
            continue

        uid = wa.attrib.get("uID")
        point_list = _find_child(wa, "pointList")
        if point_list is None:
            continue

        x_node = _find_child(point_list, "x")
        y_node = _find_child(point_list, "y")
        z_node = _find_child(point_list, "z")
        if x_node is None or y_node is None or z_node is None:
            continue

        x = _parse_vector(x_node.text)
        y = _parse_vector(y_node.text)
        z = _parse_vector(z_node.text)

        data.append(
            {
                "uid": uid,
                "x": x,
                "y": y,
                "z": z,
                "points": list(zip(x, y, z)),
                "x_node": x_node,
                "y_node": y_node,
                "z_node": z_node,
            }
        )
    return data


def write_airfoils_to_cpacs(tree: ET.ElementTree, airfoils_cut, cpacs_out: Path):
    """
    Update <pointList>/<x,y,z> in the XML tree and save a new CPACS file.
    Matching is done by wingAirfoil uID.
    """
    root = tree.getroot()
    airfoils_now = load_wing_airfoils(root)
    by_uid = {af["uid"]: af for af in airfoils_cut}
    updated = 0
    for af in airfoils_now:
        uid = af["uid"]
        if uid not in by_uid:
            continue
        new_airfoil = by_uid[uid]
        af["x_node"].text = _to_vector(new_airfoil["x"])
        af["y_node"].text = _to_vector(new_airfoil["y"])
        af["z_node"].text = _to_vector(new_airfoil["z"])
        updated += 1

    tree.write(cpacs_out, encoding="utf-8", xml_declaration=True)
    return updated


def truncate_trailing_edge(cpacs: CPACS, te_cut: float = 0.4) -> CPACS:
    tree = ET.parse(cpacs)
    root = tree.getroot()

    # import the airfoils
    airfoils = load_wing_airfoils(root)
    print(f"Loaded {len(airfoils)} airfoils")

    # te_cut -> fraction of chord removed at TE (x_cut = 1 - te_cut)
    airfoils_cut = cut_trailing_edge_airfoils(airfoils, te_cut)

    

    
    # save as a new CPACS
    cpacs_out = cpacs.with_name(f"{cpacs.stem}_tecut_straight_New.xml")
    n_updated = write_airfoils_to_cpacs(tree, airfoils_cut, cpacs_out)
    print(f"Updated {n_updated} airfoils in CPACS")
    print(f"Saved new CPACS: {cpacs_out}")
    return cpacs_out


if __name__ == "__main__":
    truncate_trailing_edge(Path(__file__).with_name("00_ToolInput(1).xml"))
