from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class StepIdResult:
    model: str

    # basic derived “step” stats
    cv0: float
    cv1: float
    pv0: float
    pv1: float
    du: float
    dy: float

    # timing (seconds)
    t_step_s: float
    theta_s: float

    # model params (tau, K, zeta, wn, etc.)
    params: Dict[str, float] = field(default_factory=dict)

    # fit metrics (optional)
    rmse: float = float("nan")
    n_fit: int = 0

    note: str = ""

    def get(self, key: str, default: Optional[float] = None) -> Optional[float]:
        return self.params.get(key, default)