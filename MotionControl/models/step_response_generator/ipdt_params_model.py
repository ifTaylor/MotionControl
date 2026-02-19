from dataclasses import dataclass


@dataclass(frozen=True)
class IPDTParams:
    K: float = 0.4
    theta_s: float = 0.3
    leak_tau_s: float = 0.0