from dataclasses import dataclass, field
from typing import Optional, Tuple

@dataclass
class SpanSelection:
    a: Optional[int] = None
    b: Optional[int] = None

    def is_valid(self) -> bool:
        return self.a is not None and self.b is not None and self.b > self.a

    def as_tuple(self) -> Optional[Tuple[int, int]]:
        return (int(self.a), int(self.b)) if self.is_valid() else None

    def clear(self) -> None:
        self.a = None
        self.b = None

    def set(self, a: int, b: int) -> None:
        a = int(a); b = int(b)
        if b <= a:
            raise ValueError("SpanSelection requires b > a")
        self.a, self.b = a, b


@dataclass
class SpanSelections:
    steady: SpanSelection = field(default_factory=SpanSelection)
    ramp: SpanSelection = field(default_factory=SpanSelection)

    def clear(self) -> None:
        self.steady.clear()
        self.ramp.clear()

    def set_span(self, span_type: str, a: int, b: int) -> None:
        st = span_type.strip().lower()
        if st in ("steady", "rx", "r_x"):
            self.steady.set(a, b)
        elif st in ("ramp", "q", "q_x_dot", "qx"):
            self.ramp.set(a, b)
        else:
            raise ValueError(f"Unknown span_type: {span_type!r}")
