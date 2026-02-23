"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for UTILS.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

__all__ = [
    "get_wkdir",
    "get_module_status",
]


def get_wkdir():
    # Lazy import to avoid package-level import cycles during app startup.
    from ceasiompy.utils.commonpaths import get_wkdir as _get_wkdir
    return _get_wkdir()


def get_module_status(default: bool, needs_soft_name: str | None = None) -> bool:
    # Lazy import to avoid loading ceasiompyutils while utils package is initializing.
    from ceasiompy.utils.ceasiompyutils import get_module_status as _get_module_status
    return _get_module_status(default=default, needs_soft_name=needs_soft_name)
