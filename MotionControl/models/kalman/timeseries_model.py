from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class TimeSeriesData:
    t: np.ndarray           # seconds, shape (N,)
    x: np.ndarray           # signal, shape (N,)
    dt_s: float             # median dt in seconds
    source_path: str        # csv path for display
