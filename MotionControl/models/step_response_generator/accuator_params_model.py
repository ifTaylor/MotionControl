from dataclasses import dataclass


@dataclass(frozen=True)
class ActuatorParams:
    pv0: float = 0.0
    pv_min: float = 9
    pv_max: float = 9
    rate_limit: float = 0.0
    tau_s: float = 0.0