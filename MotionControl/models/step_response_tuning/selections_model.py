from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class Span:
    a: Optional[int] = None
    b: Optional[int] = None

    def is_valid(self) -> bool:
        return self.a is not None and self.b is not None and int(self.b) > int(self.a)

    def as_tuple(self) -> Optional[Tuple[int, int]]:
        return (int(self.a), int(self.b)) if self.is_valid() else None

    def set(self, a: int, b: int) -> None:
        a = int(a)
        b = int(b)
        if b <= a:
            raise ValueError("Span requires b > a")
        self.a, self.b = a, b

    def clear(self) -> None:
        self.a = None
        self.b = None


@dataclass
class Point:
    i: Optional[int] = None

    def is_valid(self) -> bool:
        return self.i is not None

    def get(self) -> Optional[int]:
        return int(self.i) if self.i is not None else None

    def set(self, i: int) -> None:
        self.i = int(i)

    def clear(self) -> None:
        self.i = None


@dataclass
class StepTuneSelections:
    # Spans
    baseline: Span = field(default_factory=Span)  # pre-step baseline (noise estimate, pv0/cv0)
    final: Span = field(default_factory=Span)     # post-step "settled" window (pv1/cv1) for settling models
    fit: Span = field(default_factory=Span)       # region to compute error / fit (optional)

    # Points
    t_step: Point = field(default_factory=Point)  # step time index (usually from CV edge)
    t_dead: Point = field(default_factory=Point)  # deadtime "start of response" index
    peak: Point = field(default_factory=Point)    # peak index (underdamped)

    def clear_all(self) -> None:
        self.baseline.clear()
        self.final.clear()
        self.fit.clear()
        self.t_step.clear()
        self.t_dead.clear()
        self.peak.clear()

    def set_span(self, span_name: str, a: int, b: int) -> None:
        k = span_name.strip().lower()
        if k in ("baseline", "base"):
            self.baseline.set(a, b)
        elif k in ("final", "settle", "post"):
            self.final.set(a, b)
        elif k in ("fit", "fitspan"):
            self.fit.set(a, b)
        else:
            raise ValueError(f"Unknown span_name: {span_name!r}")

    def set_point(self, point_name: str, i: int) -> None:
        k = point_name.strip().lower()
        if k in ("t_step", "step"):
            self.t_step.set(i)
        elif k in ("t_dead", "dead", "deadtime"):
            self.t_dead.set(i)
        elif k in ("peak", "t_peak"):
            self.peak.set(i)
        else:
            raise ValueError(f"Unknown point_name: {point_name!r}")