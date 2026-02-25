"""Helpers to import the OpenVSP Python binding robustly."""

from importlib import import_module
from types import ModuleType
import sys


def _ensure_openvsp_config_flags() -> None:
    """Ensure openvsp_config exists and exposes required feature flags."""

    try:
        openvsp_config = import_module("openvsp_config")
    except ModuleNotFoundError:
        openvsp_config = ModuleType("openvsp_config")
        sys.modules["openvsp_config"] = openvsp_config

    if not hasattr(openvsp_config, "LOAD_GRAPHICS"):
        openvsp_config.LOAD_GRAPHICS = False
    if not hasattr(openvsp_config, "LOAD_FACADE"):
        openvsp_config.LOAD_FACADE = False


def get_openvsp_module():
    """Return the OpenVSP API module exposing constants like XS_UNDEFINED."""

    _ensure_openvsp_config_flags()
    try:
        vsp = import_module("openvsp")
    except AttributeError as exc:
        # Some builds fail during import when openvsp_config misses flags.
        if "LOAD_GRAPHICS" not in str(exc):
            raise
        _ensure_openvsp_config_flags()
        sys.modules.pop("openvsp", None)
        vsp = import_module("openvsp")

    if hasattr(vsp, "XS_UNDEFINED"):
        return vsp

    # Some OpenVSP distributions expose `openvsp` as a namespace package and
    # keep sibling modules (e.g. `openvsp_config`) under the same directory.
    # Add those paths to sys.path so importing `openvsp.openvsp` can resolve
    # its absolute imports.
    for path_entry in getattr(vsp, "__path__", []):
        if path_entry not in sys.path:
            sys.path.insert(0, path_entry)

    # Re-ensure flags before importing nested bindings module.
    _ensure_openvsp_config_flags()

    try:
        nested_vsp = import_module("openvsp.openvsp")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "OpenVSP Python bindings were found, but no API module with XS_UNDEFINED "
            "is available. Ensure OpenVSP bindings are installed correctly."
        ) from exc

    if hasattr(nested_vsp, "XS_UNDEFINED"):
        return nested_vsp

    raise ImportError(
        "OpenVSP module imported, but XS_UNDEFINED is missing on both "
        "'openvsp' and 'openvsp.openvsp'."
    )


vsp = get_openvsp_module()
