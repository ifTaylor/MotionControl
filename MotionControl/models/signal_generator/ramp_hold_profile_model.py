from dataclasses import dataclass


@dataclass(frozen=True)
class RampHoldProfile:
    X_LO: float = 0.0
    X_HI: float = 100.0
    T_UP_MS: int = 2000
    T_HOLD_HI_MS: int = 4000
    T_DOWN_MS: int = 2000
    T_HOLD_LO_MS: int = 4000