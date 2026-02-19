from __future__ import annotations

import numpy as np
import pandas as pd

from models.kalman import TimeSeriesData
from .helpers import median_dt_seconds


def load_csv(path: str, *, time_unit: str = "s") -> TimeSeriesData:
    """
    Load CSV with headers: time, x

    time_unit:
      - "s"  : time column is seconds
      - "ms" : time column is milliseconds

    Returns a TimeSeriesData with time in seconds.
    """
    df = pd.read_csv(path)

    if "time" not in df.columns or "x" not in df.columns:
        raise ValueError("CSV must contain headers: time, x")

    t = df["time"].to_numpy(dtype=float)
    x = df["x"].to_numpy(dtype=float)

    ok = np.isfinite(t) & np.isfinite(x)
    t = t[ok]
    x = x[ok]

    if t.size < 10:
        raise ValueError("Not enough valid samples after filtering NaNs/Infs")

    if time_unit == "ms":
        t = t / 1000.0
    elif time_unit != "s":
        raise ValueError("time_unit must be 's' or 'ms'")

    dt_s = median_dt_seconds(t)
    if not np.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("Could not determine a positive dt from time column")

    return TimeSeriesData(t=t, x=x, dt_s=float(dt_s), source_path=path)
