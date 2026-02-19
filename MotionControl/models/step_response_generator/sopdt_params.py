from dataclasses import dataclass


@dataclass(frozen=True)
class SOPDTUnderdampedParams:
    # y'' + 2ζωn y' + ωn^2 y = K ωn^2 u
    K: float = 1.0
    zeta: float = 0.45
    wn: float = 6.0
    theta_s: float = 0.0
