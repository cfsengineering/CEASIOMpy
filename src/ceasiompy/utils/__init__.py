"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for UTILS.

| Author: Leon Deligny
| Creation: 18-Mar-2025

Notes
-----
`ceasiompy.utils` is part of the public import surface and is frequently imported
by both the CLI and the Streamlit app. Keep this `__init__` lightweight:

- Do not import heavy/optional dependencies at import time (e.g. `streamlit`).
- Prefer lazy wrappers that import the implementation on first use.

"""

from __future__ import annotations

from ceasiompy.utils.commonpaths import get_wkdir


def get_module_status(*args, **kwargs):
    """Lazy wrapper to avoid importing heavy deps at import time."""

    from ceasiompy.utils.ceasiompyutils import get_module_status as _get_module_status

    return _get_module_status(*args, **kwargs)


__all__ = ["get_wkdir", "get_module_status"]
