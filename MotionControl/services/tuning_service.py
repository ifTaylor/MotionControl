from __future__ import annotations

from models.kalman import (
    TimeSeriesData,
    SpanSelections,
    TuningResult,
)
from .helpers import (
    rx_from_steady_span,
    qx_dot_from_ramp_span_excel_like
)
import numpy as np


def compute_tuning(ts: TimeSeriesData, spans: SpanSelections) -> TuningResult:
    """
    Compute tuning values from currently selected spans.

    - r_x computed from STEADY span (demeaned)
    - q_x_dot computed from RAMP span (Excel-like on 2nd diff of x)
    - q_x_user = q_x_dot * dt^2 (your mapping)
    - also provides "consistent" references
    """
    steady_span = spans.steady.as_tuple()
    ramp_span = spans.ramp.as_tuple()

    r_x = float("nan")
    sigma_x = float("nan")

    if steady_span is not None:
        a, b = steady_span
        r_x, sigma_x = rx_from_steady_span(ts.x, a, b)

    q_x_dot = float("nan")
    dv_count = 0

    if ramp_span is not None:
        a, b = ramp_span
        q_x_dot, dv_count = qx_dot_from_ramp_span_excel_like(ts.x, a, b)

    dt = ts.dt_s

    if np.isfinite(q_x_dot) and np.isfinite(dt):
        q_x_user = q_x_dot * (dt ** 2)
        q_x_consistent = 0.25 * q_x_dot * (dt ** 2)
        q_xv_consistent = 0.5 * q_x_dot * dt
    else:
        q_x_user = float("nan")
        q_x_consistent = float("nan")
        q_xv_consistent = float("nan")

    return TuningResult(
        r_x=float(r_x),
        sigma_x=float(sigma_x),
        q_x_dot=float(q_x_dot),
        dv_count=int(dv_count),
        q_x_user=float(q_x_user),
        q_x_consistent=float(q_x_consistent),
        q_xv_consistent=float(q_xv_consistent),
        steady_span=steady_span,
        ramp_span=ramp_span,
    )
