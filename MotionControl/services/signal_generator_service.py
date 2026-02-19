from __future__ import annotations

import csv
import os
import random

from models.signal_generator import RampHoldProfile


def ramp_hold_value(profile: RampHoldProfile, t_ms: int) -> float:
    period = profile.T_UP_MS + profile.T_HOLD_HI_MS + profile.T_DOWN_MS + profile.T_HOLD_LO_MS
    u = t_ms % period

    if u < profile.T_UP_MS:
        frac = u / max(profile.T_UP_MS, 1)
        return profile.X_LO + frac * (profile.X_HI - profile.X_LO)

    u -= profile.T_UP_MS
    if u < profile.T_HOLD_HI_MS:
        return profile.X_HI

    u -= profile.T_HOLD_HI_MS
    if u < profile.T_DOWN_MS:
        frac = u / max(profile.T_DOWN_MS, 1)
        return profile.X_HI - frac * (profile.X_HI - profile.X_LO)

    return profile.X_LO


def gaussian_noise(sigma: float, rng: random.Random) -> float:
    return rng.gauss(0.0, sigma)


def get_app_dir() -> str:
    # Directory where the running script/module resides
    return os.path.dirname(os.path.abspath(__file__ + "/.."))  # services/.. -> app dir


def generate_signal_csv(
    *,
    out_filename: str = "signal.csv",
    dt_ms: int = 50,
    seconds: int = 20,
    profile: RampHoldProfile = RampHoldProfile(),
    noise_amp: float = 10.0,
    rng_seed: int = 12345,
    time_unit_seconds: bool = True,
) -> str:
    """
    Writes CSV to the app dir (same directory that contains kalman_ui.py).
    Returns absolute path to the written file.
    """
    app_dir = get_app_dir()
    out_path = os.path.join(app_dir, out_filename)

    sigma_x = float(noise_amp) / 3.0  # 99.7% within +/- noise_amp
    rng = random.Random(int(rng_seed))

    total_samples = int((int(seconds) * 1000) / int(dt_ms))

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "x"])

        for i in range(total_samples):
            t_ms = i * int(dt_ms)
            x_true = ramp_hold_value(profile, t_ms)
            x_meas = x_true + gaussian_noise(sigma_x, rng)

            t_out = (t_ms / 1000.0) if time_unit_seconds else float(t_ms)
            w.writerow([f"{t_out:.6f}", f"{x_meas:.6f}"])

    return out_path
