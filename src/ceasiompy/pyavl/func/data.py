# Imports

from pydantic import BaseModel


# Classes

class AVLData(BaseModel):
    # AeroMap
    altitude: float
    mach: float
    alpha: float
    beta: float

    # Rate Settings
    p: float = 0.0      # Roll Rate
    q: float = 0.0      # Pitch Rate
    r: float = 0.0      # Yaw Rate

    # Control Surface Settings (deflection in degrees)
    aileron: float = 0.0
    elevator: float = 0.0
    rudder: float = 0.0
