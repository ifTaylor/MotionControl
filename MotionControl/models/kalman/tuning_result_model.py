from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TuningResult:
    # steady
    r_x: float
    sigma_x: float

    # ramp
    q_x_dot: float
    dv_count: int

    # mappings
    q_x_user: float
    q_x_consistent: float
    q_xv_consistent: float

    # bookkeeping
    steady_span: Optional[Tuple[int, int]]
    ramp_span: Optional[Tuple[int, int]]
