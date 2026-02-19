from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Literal

import numpy as np

from models.step_response_tuning import (
    StepTuneSelections,
    StepIdResult
)

PVModelType = Literal["FOPDT", "IPDT", "SOPDT_UNDERDAMPED"]


@dataclass(frozen=True)
class StepSeries:
    t: np.ndarray
    cv: np.ndarray
    pv: np.ndarray
    dt_s: float
    source_path: str = ""


# ----------------------------
# CSV loader (expects time, CV, PV)
# ----------------------------

def load_step_csv(path: str, *, time_unit: str = "s") -> StepSeries:
    import pandas as pd

    df = pd.read_csv(path)
    cols = [c.strip() for c in df.columns]

    if "time" not in cols:
        raise ValueError("CSV must include a 'time' column")
    if "PV" not in cols and "pv" not in cols:
        raise ValueError("CSV must include 'PV' column (case sensitive preferred)")
    if "CV" not in cols and "cv" not in cols:
        # allow missing CV (assume it steps 0->1 at detected time)
        cv = None
    else:
        cv = df["CV" if "CV" in df.columns else "cv"].to_numpy(dtype=float)

    t = df["time"].to_numpy(dtype=float)
    pv = df["PV" if "PV" in df.columns else "pv"].to_numpy(dtype=float)

    if time_unit.lower() == "ms":
        t = t / 1000.0

    ok = np.isfinite(t) & np.isfinite(pv)
    if cv is not None:
        ok = ok & np.isfinite(cv)

    t = t[ok]
    pv = pv[ok]
    if cv is None:
        cv = np.zeros_like(pv)
    else:
        cv = cv[ok]

    if t.size < 5:
        raise ValueError("Not enough samples after cleaning")

    dt = np.diff(t)
    dt = dt[np.isfinite(dt) & (dt > 0)]
    dt_s = float(np.median(dt)) if dt.size else 0.0
    if dt_s <= 0:
        dt_s = float((t[-1] - t[0]) / max(len(t) - 1, 1))

    return StepSeries(t=t, cv=cv, pv=pv, dt_s=dt_s, source_path=path)


# ----------------------------
# helpers
# ----------------------------

def _span_mean(x: np.ndarray, span: Tuple[int, int]) -> float:
    a, b = span
    seg = x[a:b]
    seg = seg[np.isfinite(seg)]
    if seg.size == 0:
        return float("nan")
    return float(np.mean(seg))

def _rmse(y: np.ndarray, yhat: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
    if mask is None:
        e = y - yhat
        e = e[np.isfinite(e)]
    else:
        e = (y - yhat)[mask]
        e = e[np.isfinite(e)]
    if e.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean(e * e)))

def _fit_mask_from_span(n: int, span: Optional[Tuple[int, int]]) -> Optional[np.ndarray]:
    if span is None:
        return None
    a, b = span
    m = np.zeros(n, dtype=bool)
    m[a:b] = True
    return m


# ----------------------------
# auto detection
# ----------------------------

def auto_detect_step_index(ts: StepSeries) -> int:
    """
    Detect step time primarily from CV edge; fallback to PV derivative if CV is flat.
    """
    cv = ts.cv
    t = ts.t
    if np.nanmax(cv) - np.nanmin(cv) > 1e-9:
        d = np.diff(cv)
        i = int(np.argmax(np.abs(d))) + 1
        return max(0, min(i, len(t) - 1))

    # fallback: PV derivative
    pv = ts.pv
    dp = np.diff(pv)
    i = int(np.argmax(np.abs(dp))) + 1
    return max(0, min(i, len(t) - 1))


def auto_detect_deadtime_index(ts: StepSeries, selections: StepTuneSelections) -> Optional[int]:
    """
    Find first index after t_step where PV derivative exceeds baseline noise threshold.
    Needs baseline span selected.
    """
    base = selections.baseline.as_tuple()
    step_i = selections.t_step.get() or auto_detect_step_index(ts)
    if base is None:
        return None

    a, b = base
    pv = ts.pv
    t = ts.t

    # baseline derivative stats
    dp = np.diff(pv)
    dp_base = dp[max(a, 0):max(b - 1, 0)]
    dp_base = dp_base[np.isfinite(dp_base)]
    if dp_base.size < 5:
        return None

    sigma = float(np.std(dp_base, ddof=1))
    thr = max(5.0 * sigma, 1e-12)

    for k in range(max(step_i, 1), len(pv) - 1):
        if not np.isfinite(dp[k]):
            continue
        if abs(dp[k]) >= thr:
            return k + 1

    return None


# ----------------------------
# simulation (for overlays)
# ----------------------------

def simulate_fopdt_overlay(t: np.ndarray, *, pv0: float, du: float, K: float, tau: float, theta: float, t_step: float) -> np.ndarray:
    tau = max(float(tau), 1e-9)
    y = np.full_like(t, pv0, dtype=float)

    t_on = float(t_step + theta)
    idx = t >= t_on
    tt = t[idx] - t_on
    y[idx] = pv0 + (K * du) * (1.0 - np.exp(-tt / tau))
    return y


def simulate_ipdt_overlay(t: np.ndarray, *, pv0: float, du: float, K: float, theta: float, t_step: float) -> np.ndarray:
    # PV ramps after (t_step + theta) with slope = K*du
    y = np.full_like(t, pv0, dtype=float)
    t_on = float(t_step + theta)
    idx = t >= t_on
    tt = t[idx] - t_on
    y[idx] = pv0 + (K * du) * tt
    return y


def simulate_sopdt_underdamped_overlay(t: np.ndarray, *, pv0: float, du: float, K: float, zeta: float, wn: float, theta: float, t_step: float) -> np.ndarray:
    """
    Standard underdamped 2nd-order step response (unit step), scaled by K*du and offset by pv0.
    y_unit = 1 - exp(-ζωn t) / sqrt(1-ζ^2) * sin(ωd t + φ)
    """
    zeta = float(zeta)
    wn = max(float(wn), 1e-6)
    if zeta >= 1.0:
        zeta = 0.999

    wd = wn * np.sqrt(1.0 - zeta * zeta)
    phi = np.arctan2(np.sqrt(1.0 - zeta * zeta), zeta)

    y = np.full_like(t, pv0, dtype=float)
    t_on = float(t_step + theta)
    idx = t >= t_on
    tt = t[idx] - t_on

    # unit-step response of 2nd-order underdamped
    y_unit = 1.0 - (np.exp(-zeta * wn * tt) / np.sqrt(1.0 - zeta * zeta)) * np.sin(wd * tt + phi)

    y[idx] = pv0 + (K * du) * y_unit
    return y


# ----------------------------
# Identification
# ----------------------------

def identify(
    ts: StepSeries,
    selections: StepTuneSelections,
    model: PVModelType,
) -> Tuple[StepIdResult, np.ndarray]:
    """
    Returns (result, pv_hat) for overlay.
    Requires:
      - baseline span for pv0/cv0
      - for FOPDT/SOPDT: final span for pv1/cv1
      - step point recommended (auto ok)
      - deadtime and peak optional (model-dependent)
    """
    base = selections.baseline.as_tuple()
    if base is None:
        raise ValueError("Select a BASELINE span first.")

    final = selections.final.as_tuple()
    step_i = selections.t_step.get()
    if step_i is None:
        step_i = auto_detect_step_index(ts)
        selections.t_step.set(step_i)

    t_step_s = float(ts.t[step_i])

    cv0 = _span_mean(ts.cv, base)
    pv0 = _span_mean(ts.pv, base)

    if model in ("FOPDT", "SOPDT_UNDERDAMPED"):
        if final is None:
            raise ValueError("Select a FINAL span (settled window) for this model.")
        cv1 = _span_mean(ts.cv, final)
        pv1 = _span_mean(ts.pv, final)
    else:
        # IPDT doesn't settle; use "final" if provided, else use last sample for display only
        cv1 = _span_mean(ts.cv, final) if final is not None else float(ts.cv[-1])
        pv1 = _span_mean(ts.pv, final) if final is not None else float(ts.pv[-1])

    du = float(cv1 - cv0)
    dy = float(pv1 - pv0)
    if abs(du) < 1e-12:
        raise ValueError("CV step size (du) is ~0. Check baseline/final spans or CSV CV column.")

    # deadtime
    dead_i = selections.t_dead.get()
    if dead_i is None:
        di = auto_detect_deadtime_index(ts, selections)
        if di is not None:
            selections.t_dead.set(di)
            dead_i = di

    theta_s = 0.0
    if dead_i is not None:
        theta_s = float(ts.t[int(dead_i)] - t_step_s)
        theta_s = max(theta_s, 0.0)

    fit_mask = _fit_mask_from_span(len(ts.t), selections.fit.as_tuple())

    if model == "FOPDT":
        # K from steady-state
        K = dy / du

        # tau from 63% point after t_step+theta
        target = pv0 + 0.6321205588 * dy
        t_on = t_step_s + theta_s

        idx = np.where(ts.t >= t_on)[0]
        tau_s = 1.0
        if idx.size > 0:
            # first crossing of target
            k0 = idx[0]
            kk = None
            for k in range(k0, len(ts.pv)):
                if np.isfinite(ts.pv[k]) and ((dy >= 0 and ts.pv[k] >= target) or (dy < 0 and ts.pv[k] <= target)):
                    kk = k
                    break
            if kk is not None:
                tau_s = float(ts.t[kk] - t_on)
                tau_s = max(tau_s, ts.dt_s)

        pv_hat = simulate_fopdt_overlay(ts.t, pv0=pv0, du=du, K=K, tau=tau_s, theta=theta_s, t_step=t_step_s)

        res = StepIdResult(
            model="FOPDT",
            cv0=cv0, cv1=cv1, pv0=pv0, pv1=pv1, du=du, dy=dy,
            t_step_s=t_step_s, theta_s=theta_s,
            params={"K": float(K), "tau_s": float(tau_s)},
        )
        res.rmse = _rmse(ts.pv, pv_hat, mask=fit_mask)
        res.n_fit = int(np.sum(fit_mask)) if fit_mask is not None else int(len(ts.t))
        return res, pv_hat

    if model == "IPDT":
        # Need a ramp/fit span for slope
        ramp_span = selections.fit.as_tuple() or selections.final.as_tuple()
        if ramp_span is None:
            raise ValueError("For IPDT, select a FIT span over the ramp region (post-deadtime).")

        a, b = ramp_span
        # linear regression PV vs time on the selected span
        tt = ts.t[a:b]
        yy = ts.pv[a:b]
        m = np.isfinite(tt) & np.isfinite(yy)
        tt = tt[m]
        yy = yy[m]
        if tt.size < 5:
            raise ValueError("Selected ramp span too small for IPDT slope fit.")

        # y = m*t + c
        A = np.vstack([tt, np.ones_like(tt)]).T
        slope, intercept = np.linalg.lstsq(A, yy, rcond=None)[0]

        # IPDT: slope ≈ K*du
        K = float(slope / du)

        pv_hat = simulate_ipdt_overlay(ts.t, pv0=pv0, du=du, K=K, theta=theta_s, t_step=t_step_s)

        res = StepIdResult(
            model="IPDT",
            cv0=cv0, cv1=cv1, pv0=pv0, pv1=pv1, du=du, dy=dy,
            t_step_s=t_step_s, theta_s=theta_s,
            params={"K": float(K)},
            note="IPDT fits slope on FIT span; PV does not settle.",
        )
        res.rmse = _rmse(ts.pv, pv_hat, mask=fit_mask)
        res.n_fit = int(np.sum(fit_mask)) if fit_mask is not None else int(len(ts.t))
        return res, pv_hat

    if model == "SOPDT_UNDERDAMPED":
        # K from steady-state
        K = dy / du

        # Need a peak point (recommended)
        peak_i = selections.peak.get()
        if peak_i is None:
            raise ValueError("For SOPDT_UNDERDAMPED, click to set a PEAK point (first overshoot peak).")

        t_peak = float(ts.t[int(peak_i)])
        pv_peak = float(ts.pv[int(peak_i)])

        # Mp = (peak - final) / dy
        if abs(dy) < 1e-12:
            raise ValueError("dy ~ 0; cannot compute overshoot ratio.")

        Mp = float((pv_peak - pv1) / dy)
        Mp = abs(Mp)

        if Mp <= 1e-6:
            raise ValueError("Peak overshoot too small; cannot identify underdamped parameters.")

        # ζ from Mp
        lnMp = np.log(Mp)
        zeta = float(-lnMp / np.sqrt(np.pi * np.pi + lnMp * lnMp))
        zeta = min(max(zeta, 0.01), 0.99)

        # Tp from peak time relative to response start (t_step+theta)
        t_on = t_step_s + theta_s
        Tp = float(t_peak - t_on)
        if Tp <= ts.dt_s:
            raise ValueError("Peak is too close to step/deadtime; check PEAK and DEADTIME selections.")
        wd = float(2.0 * np.pi / Tp)
        wn = float(wd / np.sqrt(1.0 - zeta * zeta))

        pv_hat = simulate_sopdt_underdamped_overlay(ts.t, pv0=pv0, du=du, K=K, zeta=zeta, wn=wn, theta=theta_s, t_step=t_step_s)

        res = StepIdResult(
            model="SOPDT_UNDERDAMPED",
            cv0=cv0, cv1=cv1, pv0=pv0, pv1=pv1, du=du, dy=dy,
            t_step_s=t_step_s, theta_s=theta_s,
            params={"K": float(K), "zeta": float(zeta), "wn": float(wn)},
        )
        res.rmse = _rmse(ts.pv, pv_hat, mask=fit_mask)
        res.n_fit = int(np.sum(fit_mask)) if fit_mask is not None else int(len(ts.t))
        return res, pv_hat

    raise ValueError(f"Unknown model: {model}")