"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Unit tests for static stability status helpers.
"""

import numpy as np
import pandas as pd

from ceasiompy.staticstability.func.stabilitystatus import (
    check_stability_lr,
    check_stability_tangent,
)


def test_check_stability_lr_handles_nan_and_exports_tangent_columns() -> None:
    df = pd.DataFrame(
        [
            {"mach": 0.2, "alt": 1000.0, "alpha": 0.0, "beta": 0.0, "cms": 0.0, "cml": 0.0, "cmd": 0.0},
            {"mach": 0.2, "alt": 1000.0, "alpha": 1.0, "beta": 0.0, "cms": -0.1, "cml": 0.0, "cmd": 0.0},
            {"mach": 0.2, "alt": 1000.0, "alpha": 0.0, "beta": 1.0, "cms": np.nan, "cml": 0.1, "cmd": -0.1},
            {"mach": 0.2, "alt": 1000.0, "alpha": 1.0, "beta": 1.0, "cms": np.nan, "cml": 0.1, "cmd": -0.1},
        ]
    )

    out = check_stability_lr(df)

    for col in ("cma", "cnb", "clb", "longitudinal", "directional", "lateral"):
        assert col in out.columns

    beta_one = out[out["beta"] == 1.0]
    assert beta_one["cma"].isna().all()
    assert (beta_one["longitudinal"] == "Unstable").all()


def test_check_stability_tangent_nan_marks_axis_unstable() -> None:
    longitudinal, directional, lateral = check_stability_tangent(float("nan"), 0.1, -0.1)
    assert longitudinal == "Unstable"
    assert directional == "Stable"
    assert lateral == "Stable"

