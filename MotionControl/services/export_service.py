from __future__ import annotations

import json

from models.kalman import (
    TimeSeriesData,
    SpanSelections,
)


def export_spans_json(path: str, ts: TimeSeriesData, spans: SpanSelections) -> None:
    payload = {
        "source_path": ts.source_path,
        "dt_s": ts.dt_s,
        "steady": None if spans.steady.as_tuple() is None else {"a": spans.steady.a, "b": spans.steady.b},
        "ramp": None if spans.ramp.as_tuple() is None else {"a": spans.ramp.a, "b": spans.ramp.b},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
