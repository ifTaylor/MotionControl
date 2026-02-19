from dataclasses import dataclass


@dataclass(frozen=True)
class KalmanRunConfig:
    r_x: float
    q_x: float
    q_x_dot: float

    bleed_enable: bool = False
    bleed_thresh: float = 0.0
    bleed_factor: float = 1.0

    # initial covariance
    p00: float = 1.0
    p01: float = 0.0
    p11: float = 10.0