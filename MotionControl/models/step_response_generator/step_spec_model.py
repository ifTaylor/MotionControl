from dataclasses import dataclass


@dataclass(frozen=True)
class StepSpec:
    dt_s: float = 0.05
    duration_s: float = 5.0
    t_step_s: float = 1.0
    cv0: float = 0.0
    cv_step: float = 10.0
