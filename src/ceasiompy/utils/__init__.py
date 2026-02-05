"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for UTILS.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

from __future__ import annotations

from ceasiompy.utils.commonpaths import get_wkdir


def get_module_status(*args, **kwargs):
    """Lazy wrapper to avoid importing heavy deps at import time."""

    from ceasiompy.utils.ceasiompyutils import get_module_status as _get_module_status

    return _get_module_status(*args, **kwargs)


__all__ = ["get_wkdir", "get_module_status"]
