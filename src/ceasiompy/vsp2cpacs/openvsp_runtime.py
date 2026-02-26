"""Runtime bootstrap and lazy loading for OpenVSP Python bindings."""

from __future__ import annotations

import importlib
import sys

from ceasiompy.utils.commonpaths import CEASIOMPY_PATH


def _prepend_if_exists(path) -> None:
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)


def ensure_openvsp_paths() -> None:
    """Ensure OpenVSP Python package roots are importable."""
    vsp_python_root = CEASIOMPY_PATH / "installdir/OpenVSP/python"
    vsp_openvsp_pkg = vsp_python_root / "openvsp"
    degen_geom_pkg = vsp_python_root / "degen_geom"
    vsp_config_pkg = vsp_python_root / "openvsp_config"
    utilities_pkg = vsp_python_root / "utilities"

    for p in (
        utilities_pkg,
        degen_geom_pkg,
        vsp_config_pkg,
        vsp_openvsp_pkg,
        vsp_python_root,
    ):
        _prepend_if_exists(p)


def _ensure_openvsp_config_flags() -> None:
    """Ensure openvsp_config provides the flags expected by some builds."""
    try:
        openvsp_config = importlib.import_module("openvsp_config")
    except Exception:
        return

    defaults = {
        "LOAD_GRAPHICS": False,
        "LOAD_FACADE": False,
        "LOAD_MULTI_FACADE": False,
        "_IGNORE_IMPORTS": False,
    }
    for key, value in defaults.items():
        if not hasattr(openvsp_config, key):
            setattr(openvsp_config, key, value)


def load_openvsp():
    """Import and return the OpenVSP module after runtime bootstrapping."""
    ensure_openvsp_paths()
    _ensure_openvsp_config_flags()
    return importlib.import_module("openvsp")


class _LazyVSP:
    """Proxy that loads OpenVSP on first attribute access."""

    _module = None

    def _get_module(self):
        if self._module is None:
            self._module = load_openvsp()
        return self._module

    def __getattr__(self, name):
        return getattr(self._get_module(), name)


vsp = _LazyVSP()
