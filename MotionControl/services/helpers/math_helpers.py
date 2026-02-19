from __future__ import annotations

import numpy as np


def sample_variance_excel(x: np.ndarray) -> float:
    """
    Sample variance using the same algebra as Excel:
      SUM(x^2)/(n-1) - (SUM(x)^2)/(n*(n-1))

    Equivalent to np.var(x, ddof=1) for finite values.
    """
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return float("nan")
    s1 = float(np.sum(x))
    s2 = float(np.sum(x * x))
    return (s2 / (n - 1)) - (s1 * s1) / (n * (n - 1))


def median_dt_seconds(t_s: np.ndarray) -> float:
    dt = np.diff(t_s)
    dt = dt[np.isfinite(dt) & (dt > 0)]
    if dt.size == 0:
        return float("nan")
    return float(np.median(dt))


def rx_from_steady_span(x: np.ndarray, a: int, b: int) -> tuple[float, float]:
    """
    r_x = Var(x) computed on demeaned steady segment.
    Returns (r_x, sigma_x).
    """
    seg = x[a:b]
    seg = seg[np.isfinite(seg)]
    if seg.size < 3:
        return float("nan"), float("nan")
    seg = seg - float(np.mean(seg))
    var = float(np.var(seg, ddof=1))
    sigma = float(np.sqrt(var)) if np.isfinite(var) and var >= 0 else float("nan")
    return var, sigma


def qx_dot_from_ramp_span_excel_like(x: np.ndarray, a: int, b: int) -> tuple[float, int]:
    """
    Excel-like q_x_dot from 2nd differences of x within [a:b):

      v_sample[k]  = x[k] - x[k-1]
      dv_sample[k] = v_sample[k] - v_sample[k-1]
      q_x_dot      = Var.S(dv_sample) (Excel sample variance)

    Returns (q_x_dot, dv_count).
    """
    seg = x[a:b]
    seg = seg[np.isfinite(seg)]
    if seg.size < 4:
        return float("nan"), 0
    v_s = np.diff(seg)          # x/sample
    dv_s = np.diff(v_s)         # x/sample^2
    dv_s = dv_s[np.isfinite(dv_s)]
    if dv_s.size < 2:
        return float("nan"), int(dv_s.size)
    return float(sample_variance_excel(dv_s)), int(dv_s.size)