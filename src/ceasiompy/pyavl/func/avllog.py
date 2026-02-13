# Imports

from pathlib import Path


# Methods

def _tail_file(path: Path, *, max_lines: int = 60, max_chars: int = 8000) -> str:
    if not path.exists():
        return ""
    try:
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(size - 65536, 0))
            text = handle.read().decode(errors="ignore")
    except OSError:
        return ""
    lines = text.splitlines()[-max_lines:]
    tail = "\n".join(lines)
    if len(tail) > max_chars:
        tail = tail[-max_chars:]
    return tail


# Functions

def estimate_case_progress_from_log(log_path: Path) -> tuple[float, str]:
    """Best-effort estimate of case completion from AVL stdout log."""

    tail = _tail_file(log_path)
    if not tail.strip():
        return 0.0, "starting"

    stages: list[tuple[float, str, tuple[str, ...]]] = [
        (0.10, "reading geometry", ("Reading file:",)),
        (0.25, "building surfaces", ("Building surface:", "Building duplicate image-surface:")),
        (0.35, "initializing run cases", ("Initializing run cases",)),
        (0.45, "reading mass distribution", ("Mass distribution read",)),
        (0.60, "setting up run case", ("Operation of run case",)),
        (0.70, "operating point", (".OPER",)),
        (0.85, "writing results", ("Enter filename, or <return> for screen output",)),
    ]

    best_progress = 0.05
    best_label = "running"
    for progress, label, needles in stages:
        if any(needle in tail for needle in needles):
            if progress > best_progress:
                best_progress = progress
                best_label = label

    return best_progress, best_label
