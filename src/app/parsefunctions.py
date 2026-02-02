# Imports
import re

import pandas as pd
import streamlit as st

from pathlib import Path
from pandas import DataFrame

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def display_avl_table_file(path: Path) -> None:
    text = path.read_text()
    with st.container(border=True):
        show_dir = st.checkbox(
            f"**{path.stem}**",
            value=False,
            key=f"{path}_dir_toggle",
        )
        if show_dir:
            _display_spiral_stability(text)
            if _display_surface_forces(text, path):
                return
            if _display_vortex_lattice_output(text, path):
                return
            if _display_surface_strip_forces(text, path):
                return
            _display_avl_fe_data(text, path)


def _display_spiral_stability(text: str) -> None:
    if "Clb Cnr / Clr Cnb" not in text:
        return
    value, is_stable = _parse_st_spiral(text)
    if value is not None:
        st.metric(
            "Spiral stability ratio",
            f"{value:.6f}",
            "stable" if is_stable else "not stable",
        )


def _display_surface_forces(text: str, path: Path) -> bool:
    if "Surface Forces (referred to Sref" not in text:
        return False
    refs = _parse_fn_refs(text)
    if refs:
        ref_df = DataFrame(
            {
                "Sref": [refs.get("Sref")],
                "Cref": [refs.get("Cref")],
                "Bref": [refs.get("Bref")],
                "Xref": [refs.get("Xref")],
                "Yref": [refs.get("Yref")],
                "Zref": [refs.get("Zref")],
            }
        )
        st.markdown("**Reference Values**")
        _display_compact_dataframe(ref_df)
    table1_df, table2_df = _parse_fn_tables(text)
    if not table1_df.empty:
        st.markdown("**Surface Forces (Sref/Cref/Bref)**")
        _display_compact_dataframe(table1_df)
    if not table2_df.empty:
        st.markdown("**Surface Forces (Ssurf/Cave)**")
        _display_compact_dataframe(table2_df)
    if table1_df.empty and table2_df.empty:
        st.text_area(path.stem, text, height=200, key=str(path))
    return True


def _display_vortex_lattice_output(text: str, path: Path) -> bool:
    if "Vortex Lattice Output -- Total Forces" not in text:
        return False
    config, refs, summary, tables = _parse_sb_data(text)
    config_df = _dict_to_table(config)
    summary_df = _dict_to_table(summary)
    ref_df = DataFrame(
        {
            "Sref": [refs.get("Sref")],
            "Cref": [refs.get("Cref")],
            "Bref": [refs.get("Bref")],
            "Xref": [refs.get("Xref")],
            "Yref": [refs.get("Yref")],
            "Zref": [refs.get("Zref")],
        }
    )
    if not config_df.empty:
        st.markdown("**Configuration**")
        _display_compact_dataframe(config_df)
    if not ref_df.empty and not ref_df.isna().all(axis=None):
        st.markdown("**Reference Values**")
        _display_compact_dataframe(ref_df)
    if not summary_df.empty:
        st.markdown("**Run Case Summary**")
        _display_compact_dataframe(summary_df)
    for title, df in tables:
        st.markdown(f"**{title}**")
        _display_compact_dataframe(df)
    if config_df.empty and summary_df.empty and not tables:
        st.text_area(path.stem, text, height=200, key=str(path))
    return True


def _display_surface_strip_forces(text: str, path: Path) -> bool:
    if "Surface and Strip Forces by surface" not in text:
        return False
    surfaces_df, strip_tables = _parse_fs_tables(text)
    if not surfaces_df.empty:
        st.markdown("**Surface Summary**")
        _display_compact_dataframe(surfaces_df)
    for surface_id, surface_name, _coeffs, strip_df in strip_tables:
        with st.expander(f"Surface {surface_id} - {surface_name}", expanded=False):
            if not strip_df.empty:
                st.markdown("**Strip Forces**")
                _display_compact_dataframe(strip_df)
    if surfaces_df.empty:
        st.text_area(path.stem, text, height=200, key=str(path))
    return True


def _display_avl_fe_data(text: str, path: Path) -> None:
    try:
        surfaces_df, strips_df, strip_tables = _parse_avl_fe(text)
    except BaseException:
        st.text_area(path.stem, text, height=200, key=str(path))
        return

    if not surfaces_df.empty:
        st.markdown("**Surface Summary**")
        _display_compact_dataframe(surfaces_df)

    if not strips_df.empty:
        st.markdown("**Strip Summary**")
        _display_compact_dataframe(strips_df)

    for strip_id, df in strip_tables:
        with st.expander(f"Strip {strip_id} details", expanded=False):
            _display_compact_dataframe(df)


# =================================================================================================
#    METHODS
# =================================================================================================


def _parse_fs_tables(
    text: str,
) -> tuple[DataFrame, list[tuple[int, str, dict[str, float], DataFrame]]]:
    surfaces: list[dict] = []
    strip_tables: list[tuple[int, str, dict[str, float], DataFrame]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        surface_match = re.match(r"^\s*Surface\s+#\s*(\d+)\s+(.+?)\s*$", line)
        if surface_match:
            surface_id = int(surface_match.group(1))
            surface_name = surface_match.group(2).strip()
            surface: dict[str, float | int | str] = {
                "surface_id": surface_id,
                "surface_name": surface_name,
            }
            surface_coeffs: dict[str, float] = {}
            i += 1
            while i < len(lines):
                line = lines[i]
                if re.match(r"^\s*Surface\s+#", line) or line.strip().startswith(
                    "Strip Forces"
                ):
                    break
                chord_span = re.search(
                    r"#\s*Chordwise\s*=\s*(\d+).+#\s*Spanwise\s*=\s*(\d+).+"
                    r"First strip\s*=\s*(\d+)",
                    line,
                )
                if chord_span:
                    surface["chordwise"] = int(chord_span.group(1))
                    surface["spanwise"] = int(chord_span.group(2))
                    surface["first_strip"] = int(chord_span.group(3))
                area_pattern = (
                    r"Surface area Ssurf\s*=\s*([-+]?\d*\.?\d+)\s+"
                    r"Ave\. chord Cave\s*=\s*([-+]?\d*\.?\d+)"
                )
                area_match = re.search(area_pattern, line)
                if area_match:
                    surface["Ssurf"] = float(area_match.group(1))
                    surface["Cave"] = float(area_match.group(2))
                surface_coeffs.update(_parse_fe_key_values(line))
                i += 1

            strip_df = DataFrame()
            if i < len(lines) and lines[i].strip().startswith("Strip Forces"):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("j"):
                    i += 1
                if i < len(lines) and lines[i].strip().startswith("j"):
                    columns = lines[i].split()
                    i += 1
                    rows: list[list[str]] = []
                    while i < len(lines):
                        line = lines[i]
                        if not line.strip() or re.match(r"^\s*Surface\s+#", line):
                            break
                        values = line.split()
                        if len(values) == len(columns):
                            rows.append(values)
                        i += 1
                    if rows:
                        strip_df = DataFrame(rows, columns=columns)
                        for col in strip_df.columns:
                            strip_df[col] = pd.to_numeric(strip_df[col], errors="coerce")

            surfaces.append({**surface, **surface_coeffs})
            strip_tables.append((surface_id, surface_name, surface_coeffs, strip_df))
            continue
        i += 1

    return DataFrame(surfaces), strip_tables


def _parse_st_spiral(text: str) -> tuple[float | None, bool | None]:
    match = re.search(r"Clb\s*Cnr\s*/\s*Clr\s*Cnb\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", text)
    if not match:
        return None, None
    value = float(match.group(1))
    return value, value > 1.0


def _parse_avl_fe(text: str) -> tuple[DataFrame, DataFrame, list[tuple[int, DataFrame]]]:
    surfaces: list[dict] = []
    strips: list[dict] = []
    strip_tables: list[tuple[int, DataFrame]] = []

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        surface_match = re.match(r"^\s*Surface\s+#\s*(\d+)\s+(.+?)\s*$", line)
        if surface_match:
            surface = {
                "surface_id": int(surface_match.group(1)),
                "surface_name": surface_match.group(2).strip(),
            }
            i += 1
            while i < len(lines):
                line = lines[i]
                if re.match(r"^\s*(Strip\s+#|Surface\s+#|\*{3,})", line):
                    break
                surface.update(_parse_fe_key_values(line))
                i += 1
            surfaces.append(surface)
            continue

        strip_match = re.match(
            r"^\s*Strip\s+#\s*(\d+).*#\s*Chordwise\s*=\s*(\d+).*First\s+Vortex\s*=\s*(\d+)",
            line,
        )
        if strip_match:
            strip_id = int(strip_match.group(1))
            strip = {
                "strip_id": strip_id,
                "chordwise": int(strip_match.group(2)),
                "first_vortex": int(strip_match.group(3)),
            }
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.strip().startswith("I"):
                    break
                if re.match(r"^\s*(Strip\s+#|Surface\s+#|\*{3,})", line):
                    break
                strip.update(_parse_fe_key_values(line))
                i += 1

            if i < len(lines) and lines[i].strip().startswith("I"):
                columns = lines[i].split()
                i += 1
                rows: list[list[str]] = []
                while i < len(lines):
                    line = lines[i]
                    if not line.strip() or re.match(r"^\s*(Strip\s+#|Surface\s+#|\*{3,})", line):
                        break
                    values = line.split()
                    if len(values) == len(columns):
                        rows.append(values)
                    i += 1
                if rows:
                    df = DataFrame(rows, columns=columns)
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    strip_tables.append((strip_id, df))

            strips.append(strip)
            continue

        i += 1

    return DataFrame(surfaces), DataFrame(strips), strip_tables


def _display_compact_dataframe(df: DataFrame) -> None:
    if df.empty:
        return
    safe_df = df.copy()
    for col in safe_df.columns:
        if safe_df[col].dtype == "object":
            safe_df[col] = safe_df[col].apply(lambda value: "" if pd.isna(value) else str(value))
    column_config = {col: st.column_config.Column(width="content") for col in safe_df.columns}
    st.dataframe(safe_df, width="content", hide_index=True, column_config=column_config)


def _normalize_fe_key(key: str) -> str:
    return key.strip().replace(".", "").replace("/", "_").replace("-", "_")


def _parse_fe_key_values(line: str) -> dict[str, float]:
    sanitized = line.replace("cm c/4", "cm_c4").replace("wake dnwsh", "wake_dnwsh")
    matches = re.findall(r"([A-Za-z0-9._/]+)\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", sanitized)
    return {_normalize_fe_key(key): float(value) for key, value in matches}


def _parse_fn_tables(text: str) -> tuple[DataFrame, DataFrame]:
    def parse_table(lines: list[str], start_index: int, columns: list[str]) -> DataFrame:
        rows: list[list[str]] = []
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                if rows:
                    break
                i += 1
                continue
            if line.startswith("-") or line.startswith("Surface Forces"):
                break
            parts = line.split()
            if len(parts) < len(columns) or not re.match(r"^[-+]?\d", parts[0]):
                i += 1
                continue
            numeric = parts[: len(columns)]
            label = " ".join(parts[len(columns) :]).strip()
            row = numeric + ([label] if label else [""])
            rows.append(row)
            i += 1
        if not rows:
            return DataFrame()
        df = DataFrame(rows, columns=columns + ["surface_name"])
        for col in columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    lines = text.splitlines()
    table1_columns = ["n", "Area", "CL", "CD", "Cm", "CY", "Cn", "Cl", "CDi", "CDv"]
    table2_columns = ["n", "Ssurf", "Cave", "cl", "cd", "cdv"]
    table1_df = DataFrame()
    table2_df = DataFrame()
    for i, line in enumerate(lines):
        header = line.strip()
        if re.match(r"^n\s+Area\s+CL", header):
            table1_df = parse_table(lines, i, table1_columns)
        if re.match(r"^n\s+Ssurf\s+Cave", header):
            table2_df = parse_table(lines, i, table2_columns)
    return table1_df, table2_df


def _parse_fn_refs(text: str) -> dict[str, float]:
    refs: dict[str, float] = {}
    for line in text.splitlines():
        refs.update(_parse_fe_key_values(line))
        if all(key in refs for key in ("Sref", "Cref", "Bref", "Xref", "Yref", "Zref")):
            break
    return refs


def _dict_to_table(data: dict[str, float | str]) -> DataFrame:
    if not data:
        return DataFrame()
    return DataFrame({"key": list(data.keys()), "value": list(data.values())})


def _parse_sb_data(
    text: str,
) -> tuple[
    dict[str, str | float],
    dict[str, float],
    dict[str, float],
    list[tuple[str, DataFrame]],
]:
    refs = _parse_fn_refs(text)
    lines = text.splitlines()
    config = _parse_sb_config(lines)
    summary = _parse_sb_summary(lines)
    tables = _parse_sb_tables(lines)
    return config, refs, summary, tables


def _parse_sb_config(lines: list[str]) -> dict[str, str | float]:
    config: dict[str, str | float] = {}
    count_patterns = {
        "Surfaces": r"#\s*Surfaces\s*=\s*([-+]?\d+)",
        "Strips": r"#\s*Strips\s*=\s*([-+]?\d+)",
        "Vortices": r"#\s*Vortices\s*=\s*([-+]?\d+)",
    }
    for line in lines:
        config_match = re.search(r"Configuration:\s*(.+)$", line)
        if config_match:
            config["Configuration"] = config_match.group(1).strip()
        for key, pattern in count_patterns.items():
            count_match = re.search(pattern, line)
            if count_match:
                config[key] = float(count_match.group(1))
    return config


def _parse_sb_summary(lines: list[str]) -> dict[str, float]:
    summary: dict[str, float] = {}
    in_summary = False
    for line in lines:
        if line.strip().startswith("Run case:"):
            in_summary = True
            continue
        if "Geometry-axis derivatives" in line:
            in_summary = False
        if in_summary:
            summary.update(_parse_fe_key_values(line))
    return summary


def _parse_sb_tables(lines: list[str]) -> list[tuple[str, DataFrame]]:
    tables: list[tuple[str, DataFrame]] = []
    header_map = {
        "axial   vel. u": "Geometry-Axis Derivatives (u/v/w)",
        "roll rate  p": "Geometry-Axis Derivatives (p/q/r)",
        "flap         d01": "Control Derivatives (d01/d02/d03/d04)",
    }
    for i, line in enumerate(lines):
        for marker, title in header_map.items():
            if marker in line:
                df, _ = _parse_derivative_table(lines, i)
                if not df.empty:
                    tables.append((title, df))
    return tables


def _parse_derivative_table(lines: list[str], start_index: int) -> tuple[DataFrame, int]:
    rows: list[dict[str, float | str]] = []
    i = start_index + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            if rows:
                break
            i += 1
            continue
        if line.strip().startswith("-"):
            i += 1
            continue
        if "Geometry-axis derivatives" in line:
            break
        if "|" in line:
            label = line.split("|", 1)[0].strip()
            pairs = re.findall(
                r"([A-Za-z0-9']+)\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)",
                line,
            )
            row: dict[str, float | str] = {"label": label}
            for key, value in pairs:
                row[key] = float(value)
            rows.append(row)
        i += 1
    if not rows:
        return DataFrame(), i
    df = DataFrame(rows)
    return df, i
