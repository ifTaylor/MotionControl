from __future__ import annotations

from typing import Literal, Tuple
import os
import csv
import numpy as np

from models.step_response_generator import (
    FOPDTParams,
    IPDTParams,
    SOPDTUnderdampedParams,
    StepSpec,
    ActuatorParams,
)

PVModelType = Literal["FOPDT", "IPDT", "SOPDT_UNDERDAMPED"]


def get_app_dir() -> str:
    # services/.. => MotionControl/MotionControl
    return os.path.dirname(os.path.abspath(__file__ + "/.."))


def make_step_cv(t: np.ndarray, spec: StepSpec) -> np.ndarray:
    cv = np.full_like(t, float(spec.cv0), dtype=float)
    cv[t >= float(spec.t_step_s)] = float(spec.cv_step)
    return cv


def apply_deadtime(u: np.ndarray, dt_s: float, theta_s: float) -> np.ndarray:
    n_delay = int(round(max(theta_s, 0.0) / max(dt_s, 1e-12)))
    if n_delay <= 0:
        return u.copy()
    out = np.empty_like(u)
    out[:n_delay] = u[0]
    out[n_delay:] = u[:-n_delay]
    return out


# ----------------------------
# Actuator (CV_cmd -> CV_eff)
# ----------------------------

def actuator_block(cv_cmd: np.ndarray, dt_s: float, p: ActuatorParams) -> np.ndarray:
    """
    Applies (in order):
      1) saturation
      2) rate limit
      3) first-order lag
    """
    # 1) saturation
    u = np.clip(cv_cmd, float(p.pv_min), float(p.pv_max))

    # 2) rate limiting
    if float(p.rate_limit) > 0.0:
        r = float(p.rate_limit)
        out = np.empty_like(u)
        out[0] = u[0]
        max_step = r * dt_s
        for k in range(1, len(u)):
            du = u[k] - out[k - 1]
            if du > max_step:
                du = max_step
            elif du < -max_step:
                du = -max_step
            out[k] = out[k - 1] + du
        u = out

    # 3) first-order lag
    tau = float(p.tau_s)
    if tau > 0.0:
        out = np.empty_like(u)
        out[0] = u[0]
        a = dt_s / max(tau, 1e-12)
        # stable Euler: y += a*(u - y)
        for k in range(1, len(u)):
            out[k] = out[k - 1] + a * (u[k] - out[k - 1])
        u = out

    return u


def simulate_fopdt(t: np.ndarray, u: np.ndarray, dt_s: float, p: FOPDTParams) -> np.ndarray:
    tau = max(float(p.tau_s), 1e-9)
    K = float(p.K)
    y = np.zeros_like(t, dtype=float)
    for k in range(1, len(t)):
        ydot = (K * u[k - 1] - y[k - 1]) / tau
        y[k] = y[k - 1] + dt_s * ydot
    return y

def simulate_ipdt(t: np.ndarray, u: np.ndarray, dt_s: float, p: IPDTParams) -> np.ndarray:
    K = float(p.K)
    leak_tau = float(p.leak_tau_s)

    y = np.zeros_like(t, dtype=float)
    for k in range(1, len(t)):
        if leak_tau > 1e-9:
            ydot = K * u[k-1] - (y[k-1] / leak_tau)
        else:
            ydot = K * u[k-1]
        y[k] = y[k-1] + dt_s * ydot
    return y

def simulate_sopdt_underdamped(t: np.ndarray, u: np.ndarray, dt_s: float, p: SOPDTUnderdampedParams) -> np.ndarray:
    zeta = float(p.zeta)
    wn = max(float(p.wn), 1e-6)
    K = float(p.K)

    y = np.zeros_like(t, dtype=float)
    ydot = 0.0

    for k in range(1, len(t)):
        u_k = float(u[k - 1])
        yddot = (-2.0 * zeta * wn) * ydot - (wn * wn) * y[k - 1] + (K * wn * wn) * u_k
        ydot = ydot + dt_s * yddot
        y[k] = y[k - 1] + dt_s * ydot

    return y


def simulate_step_response(
    *,
    spec: StepSpec,
    actuator: ActuatorParams,
    model: PVModelType,
    fopdt: FOPDTParams | None = None,
    ipdt: IPDTParams | None = None,
    sopdt: SOPDTUnderdampedParams | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
      t, cv_cmd (export), pv, cv_eff (internal, optional for plot)
    """
    dt_s = max(float(spec.dt_s), 1e-6)
    n = int(round(float(spec.duration_s) / dt_s)) + 1
    if n < 2:
        raise ValueError("duration_s must be >= dt_s")

    t = np.linspace(0.0, float(spec.duration_s), n)

    cv_cmd = make_step_cv(t, spec)
    cv_eff = actuator_block(cv_cmd, dt_s, actuator)

    # Drive PV with delta input about operating point
    u = cv_eff - float(spec.cv0)

    if model == "FOPDT":
        p = fopdt or FOPDTParams()
        u_d = apply_deadtime(u, dt_s, float(p.theta_s))
        y = simulate_fopdt(t, u_d, dt_s, p)
    elif model == "IPDT":
        p = ipdt or IPDTParams()
        u_d = apply_deadtime(u, dt_s, float(p.theta_s))
        y = simulate_ipdt(t, u_d, dt_s, p)
    elif model == "SOPDT_UNDERDAMPED":
        p = sopdt or SOPDTUnderdampedParams()
        u_d = apply_deadtime(u, dt_s, float(p.theta_s))
        y = simulate_sopdt_underdamped(t, u_d, dt_s, p)
    else:
        raise ValueError(f"Unknown model: {model}")

    pv = float(actuator.pv0) + y
    return t, cv_cmd, pv, cv_eff


def export_step_csv(
    *,
    out_filename: str,
    t: np.ndarray,
    cv_cmd: np.ndarray,
    pv: np.ndarray,
    time_unit_seconds: bool = True,
) -> str:
    out_path = os.path.join(get_app_dir(), out_filename)

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "CV", "PV"])
        for i in range(len(t)):
            t_out = float(t[i]) if time_unit_seconds else float(t[i] * 1000.0)
            w.writerow([f"{t_out:.6f}", f"{cv_cmd[i]:.6f}", f"{pv[i]:.6f}"])

    return out_path
