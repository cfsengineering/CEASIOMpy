# Futures

from __future__ import annotations

# Imports
import json

from ceasiompy.pyavl.func.utils import get_atmospheric_cond
from ceasiompy.utils.mathsfunctions import non_dimensionalize_rate

from pathlib import Path

from ceasiompy import log


# Classes

class AVLData:
    _INIT_FIELDS = (
        "ref_area",
        "ref_length",
        "altitude",
        "mach",
        "alpha",
        "beta",
        "p",
        "q",
        "r",
        "aileron",
        "elevator",
        "rudder",
    )

    def __init__(
        self: AVLData,
        # Geometry Specific
        ref_area: float,
        ref_length: float,

        # AeroMap
        altitude: float,    # Meters
        mach: float,
        alpha: float,       # Degrees
        beta: float,        # Degrees

        # Rate Settings
        p: float = 0.0,      # Roll Rate
        q: float = 0.0,      # Pitch Rate
        r: float = 0.0,      # Yaw Rate

        # Control Surface Settings
        aileron: float = 0.0,   # Degrees
        elevator: float = 0.0,  # Degrees
        rudder: float = 0.0,    # Degrees
    ) -> None:
        # Geometry Specific
        self.ref_area: float = ref_area
        self.ref_length: float = ref_length

        # AeroMap
        self.altitude: float = altitude
        self.mach: float = mach
        self.alpha: float = alpha
        self.beta: float = beta

        # Rate Settings
        self.p: float = p      # Roll Rate
        self.q: float = q      # Pitch Rate
        self.r: float = r      # Yaw Rate

        # Control Surface Settings (deflection in degrees)
        self.rudder: float = rudder
        self.aileron: float = aileron
        self.elevator: float = elevator

        (
            self.p_star,
            self.q_star,
            self.r_star,
            self.ref_density,
            self.g_acceleration,
            self.ref_velocity,
        ) = _get_physics_conditions(
            ref_area=self.ref_area,
            ref_length=self.ref_length,
            alt=self.altitude,
            mach=self.mach,
            p=self.p,
            q=self.q,
            r=self.r,
        )

    def case_key(self: AVLData) -> dict:
        """Key Identifier for AVL case."""
        return {
            "altitude": self.altitude,
            "mach": self.mach,
            "alpha": self.alpha,
            "beta": self.beta,
            "p": self.p,
            "q": self.q,
            "r": self.r,
            "aileron": self.aileron,
            "elevator": self.elevator,
            "rudder": self.rudder,
        }

    def to_dict(self: AVLData) -> dict:
        return {
            # Init fields
            "ref_area": self.ref_area,
            "ref_length": self.ref_length,
            "altitude": self.altitude,
            "mach": self.mach,
            "alpha": self.alpha,
            "beta": self.beta,
            "p": self.p,
            "q": self.q,
            "r": self.r,
            "aileron": self.aileron,
            "elevator": self.elevator,
            "rudder": self.rudder,
            # Computed fields
            "p_star": self.p_star,
            "q_star": self.q_star,
            "r_star": self.r_star,
            "ref_density": self.ref_density,
            "g_acceleration": self.g_acceleration,
            "ref_velocity": self.ref_velocity,
        }

    def to_json(self: AVLData, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self: AVLData, json_path: Path) -> Path:
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(self.to_json(indent=2), encoding="utf-8")
        return json_path

    @classmethod
    def from_dict(cls, data: dict) -> AVLData:
        init_data = {key: data[key] for key in cls._INIT_FIELDS if key in data}
        missing = [key for key in cls._INIT_FIELDS if key not in init_data]
        if missing:
            raise ValueError(f"Missing AVLData fields in JSON payload: {missing}")
        return cls(**init_data)

    @classmethod
    def from_json(cls, json_payload: str) -> AVLData:
        data = json.loads(json_payload)
        if not isinstance(data, dict):
            raise ValueError("AVLData JSON payload must decode to an object/dict.")
        return cls.from_dict(data)

    @classmethod
    def load_json(cls, json_path: Path) -> AVLData:
        json_path = Path(json_path)
        return cls.from_json(json_path.read_text(encoding="utf-8"))


# Methods

def _get_physics_conditions(
    ref_area: float,
    ref_length: float,
    alt: float,
    mach: float,
    p: float,
    q: float,
    r: float,
) -> tuple[
    float, float, float,
    float, float, float,
]:
    # Get the reference dimensions
    b = ref_area / ref_length

    ref_density, g_acceleration, ref_velocity = get_atmospheric_cond(
        alt=alt,
        mach=mach,
    )

    # See https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf
    # for how he non-dimensionalize the rates
    p_star, q_star, r_star = non_dimensionalize_rate(
        p=p,
        q=q,
        r=r,
        v=ref_velocity,
        b=b,
        c=ref_length,
    )

    return (
        p_star, q_star, r_star,
        ref_density, g_acceleration, ref_velocity,
    )


# Functions
def create_case_dir(
    i_case: int,
    avl_data: AVLData,
    results_dir: Path,
    **params: float,
) -> Path:
    # Log the parameters
    param_log = ", ".join(f"{key}: {value}" for key, value in params.items())
    if param_log != "":
        param_log = "with " + param_log
    param_log += ")"
    log.info(
        f"Running Case {i_case}: "
        f"(altitude={avl_data.altitude}, mach={avl_data.mach}, "
        f"alpha={avl_data.alpha}, beta={avl_data.beta} "
        f"{param_log} ---"
    )

    # Create the case directory name dynamically
    case_base = (
        f"case{str(i_case).zfill(2)}_alt{avl_data.altitude}_mach{avl_data.mach}"
        f"_alpha{avl_data.alpha}_beta{avl_data.beta}"
    )

    case_dir_name = case_base + "".join(
        f"_{key}{round(value, 2) if isinstance(value, float) else value}"
        for key, value in params.items()
    )

    # Create the directory
    case_dir_path = Path(results_dir, case_dir_name)
    case_dir_path.mkdir(exist_ok=True)

    return case_dir_path
