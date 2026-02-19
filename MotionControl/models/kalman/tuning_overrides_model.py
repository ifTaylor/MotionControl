from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TuningOverrides:
    use_manual_r_x: bool = False
    use_manual_q_x: bool = False
    use_manual_q_x_dot: bool = False

    manual_r_x: float = 1.0
    manual_q_x: float = 0.0
    manual_q_x_dot: float = 0.0

    def active_r_x(self, suggested: float) -> float:
        return self.manual_r_x if self.use_manual_r_x else suggested

    def active_q_x(self, suggested: float) -> float:
        return self.manual_q_x if self.use_manual_q_x else suggested

    def active_q_x_dot(self, suggested: float) -> float:
        return self.manual_q_x_dot if self.use_manual_q_x_dot else suggested
