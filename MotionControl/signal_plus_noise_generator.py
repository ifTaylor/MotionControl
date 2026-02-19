#!/usr/bin/env python3
"""
Generate a ramp/hold/ramp/hold signal with Gaussian noise and write signal.csv.

CSV headers:
  time, x

This matches the generator style we used earlier:
- Ideal pattern: ramp up -> hold high -> ramp down -> hold low -> repeat
- Add zero-mean Gaussian noise (sensor jitter)

Edit constants in main() as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import csv


@dataclass
class RampHoldProfile:
    X_LO: float = 0.0
    X_HI: float = 100.0
    T_UP_MS: int = 2000
    T_HOLD_HI_MS: int = 4000
    T_DOWN_MS: int = 2000
    T_HOLD_LO_MS: int = 4000


def ramp_hold_value(profile: RampHoldProfile, t_ms: int) -> float:
    """Noise-free ramp/hold/ramp/hold waveform."""
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
    """Zero-mean Gaussian noise with standard deviation sigma."""
    return rng.gauss(0.0, sigma)


def main():
    # ==========================
    # USER EDIT SECTION
    # ==========================
    OUT_CSV = "./MotionControl/signal.csv"

    DT_MS = 50
    SECONDS = 20

    profile = RampHoldProfile(
        X_LO=0.0,
        X_HI=100.0,
        T_UP_MS=2000,
        T_HOLD_HI_MS=4000,
        T_DOWN_MS=2000,
        T_HOLD_LO_MS=4000,
    )

    # "Noise amplitude" intuition:
    # If you used uniform +/- NOISE_AMP before, a comparable Gaussian sigma is ~ NOISE_AMP/3
    # (so ~99.7% of samples fall within +/- NOISE_AMP).
    NOISE_AMP = 10.0
    SIGMA_X = NOISE_AMP / 3.0

    RNG_SEED = 12345

    # time column in seconds (float)
    TIME_UNIT_SECONDS = True
    # ==========================

    rng = random.Random(RNG_SEED)

    total_samples = int((SECONDS * 1000) / DT_MS)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "x"])

        for i in range(total_samples):
            t_ms = i * DT_MS
            x_true = ramp_hold_value(profile, t_ms)
            x_meas = x_true + gaussian_noise(SIGMA_X, rng)

            if TIME_UNIT_SECONDS:
                t_out = t_ms / 1000.0
            else:
                t_out = float(t_ms)

            w.writerow([f"{t_out:.6f}", f"{x_meas:.6f}"])

    print(f"Wrote {OUT_CSV} with {total_samples} samples (dt={DT_MS} ms, duration={SECONDS} s).")


if __name__ == "__main__":
    main()
