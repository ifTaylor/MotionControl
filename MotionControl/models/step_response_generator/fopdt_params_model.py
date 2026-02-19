from dataclasses import dataclass


@dataclass(frozen=True)
class FOPDTParams:
    K: float = 1.0
    tau_s: float = 0.3
    theta_s: float = 0.2