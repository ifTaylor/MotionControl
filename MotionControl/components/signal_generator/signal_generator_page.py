from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services import generate_signal_csv
from models.signal_generator import RampHoldProfile


class SignalGeneratorPage(ttk.Frame):
    def __init__(self, parent, *, on_back: Callable[[], None]):
        super().__init__(parent, padding=0)

        # Debounce handle for auto-preview
        self._preview_job = None
        self._suppress_preview = False

        # =========================
        # Header
        # =========================
        header = ttk.Frame(self, padding=8)
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(header, text="← Back", command=on_back).pack(side=tk.LEFT)
        ttk.Label(header, text="Signal Generator", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=10)

        # =========================
        # Body
        # =========================
        body = ttk.Frame(self, padding=16)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)  # preview box expands

        # =========================
        # Vars
        # =========================
        self.out_filename = tk.StringVar(value="signal.csv")
        self.dt_ms = tk.StringVar(value="50")
        self.seconds = tk.StringVar(value="20")
        self.noise_amp = tk.StringVar(value="10.0")
        self.rng_seed = tk.StringVar(value="12345")
        self.time_unit_seconds = tk.BooleanVar(value=True)

        self.x_lo = tk.StringVar(value="0.0")
        self.x_hi = tk.StringVar(value="100.0")
        self.t_up = tk.StringVar(value="2000")
        self.t_hold_hi = tk.StringVar(value="4000")
        self.t_down = tk.StringVar(value="2000")
        self.t_hold_lo = tk.StringVar(value="4000")

        # =========================
        # Helpers
        # =========================
        def config_grid_2col(frame: ttk.Frame):
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)

        def add_row(parent_frame: ttk.Frame, row: int, label: str, var: tk.Variable, *, width: int = 18) -> int:
            ttk.Label(parent_frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            e = ttk.Entry(parent_frame, textvariable=var, width=width)
            e.grid(row=row, column=1, sticky="w", pady=3)

            # Immediate preview when finishing edit
            e.bind("<Return>", lambda _e: self._schedule_preview(0))
            e.bind("<FocusOut>", lambda _e: self._schedule_preview(0))
            return row + 1

        # =========================
        # Section: Output settings
        # =========================
        out_box = ttk.LabelFrame(body, text="Output / Noise / Timing", padding=12)
        out_box.grid(row=0, column=0, sticky="ew")
        config_grid_2col(out_box)

        r = 0
        r = add_row(out_box, r, "Output filename (app dir):", self.out_filename, width=28)
        r = add_row(out_box, r, "DT_MS:", self.dt_ms)
        r = add_row(out_box, r, "SECONDS:", self.seconds)
        r = add_row(out_box, r, "NOISE_AMP:", self.noise_amp)
        r = add_row(out_box, r, "RNG_SEED:", self.rng_seed)

        ttk.Checkbutton(
            out_box,
            text="Time column in seconds (unchecked = milliseconds)",
            variable=self.time_unit_seconds,
            command=lambda: self._schedule_preview(0),
        ).grid(row=r, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # =========================
        # Section: Profile settings
        # =========================
        prof_box = ttk.LabelFrame(body, text="Ramp/Hold Profile", padding=12)
        prof_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        config_grid_2col(prof_box)

        rr = 0
        rr = add_row(prof_box, rr, "X_LO:", self.x_lo)
        rr = add_row(prof_box, rr, "X_HI:", self.x_hi)
        rr = add_row(prof_box, rr, "T_UP_MS:", self.t_up)
        rr = add_row(prof_box, rr, "T_HOLD_HI_MS:", self.t_hold_hi)
        rr = add_row(prof_box, rr, "T_DOWN_MS:", self.t_down)
        rr = add_row(prof_box, rr, "T_HOLD_LO_MS:", self.t_hold_lo)

        # =========================
        # Section: Preview plot
        # =========================
        preview_box = ttk.LabelFrame(body, text="Preview", padding=8)
        preview_box.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        preview_box.rowconfigure(0, weight=1)
        preview_box.columnconfigure(0, weight=1)

        self._fig = Figure(figsize=(9.0, 3.0), dpi=100)
        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.grid(True)
        self._ax.set_title("Generated signal preview")
        self._ax.set_xlabel("time")
        self._ax.set_ylabel("x")

        self._canvas = FigureCanvasTkAgg(self._fig, master=preview_box)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # =========================
        # Bottom controls
        # =========================
        controls = ttk.Frame(body)
        controls.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        controls.columnconfigure(2, weight=1)

        ttk.Button(controls, text="Preview now", command=self._on_preview).grid(row=0, column=0, sticky="w")
        ttk.Button(controls, text="Generate signal.csv", command=self._on_generate).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.status = ttk.Label(controls, text="", foreground="gray")
        self.status.grid(row=0, column=2, sticky="w", padx=(12, 0))

        # =========================
        # Auto-preview on ANY change (debounced)
        # =========================
        def _trace(*_args):
            self._schedule_preview(200)

        for v in [
            self.out_filename, self.dt_ms, self.seconds, self.noise_amp, self.rng_seed,
            self.x_lo, self.x_hi, self.t_up, self.t_hold_hi, self.t_down, self.t_hold_lo,
        ]:
            v.trace_add("write", _trace)

        # BooleanVar doesn’t use trace reliably across all ttk widgets; we already use command= above.

        # Initial preview
        self._schedule_preview(0)

    # -------------------------
    # Debounced preview
    # -------------------------
    def _schedule_preview(self, delay_ms: int = 200) -> None:
        if self._suppress_preview:
            return

        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None

        self._preview_job = self.after(delay_ms, self._safe_preview)

    def _safe_preview(self) -> None:
        self._preview_job = None
        try:
            self._on_preview()
        except Exception:
            # Ignore invalid partial input while typing (e.g., empty string)
            pass

    # -------------------------
    # Internal math for preview
    # -------------------------
    def _build_profile(self) -> RampHoldProfile:
        return RampHoldProfile(
            X_LO=float(self.x_lo.get()),
            X_HI=float(self.x_hi.get()),
            T_UP_MS=int(self.t_up.get()),
            T_HOLD_HI_MS=int(self.t_hold_hi.get()),
            T_DOWN_MS=int(self.t_down.get()),
            T_HOLD_LO_MS=int(self.t_hold_lo.get()),
        )

    @staticmethod
    def _ramp_hold_value(profile: RampHoldProfile, t_ms: int) -> float:
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

    def _preview_series(self) -> tuple[np.ndarray, np.ndarray]:
        dt_ms = int(self.dt_ms.get())
        seconds = int(self.seconds.get())
        noise_amp = float(self.noise_amp.get())
        rng_seed = int(self.rng_seed.get())

        profile = self._build_profile()

        n = int((seconds * 1000) / dt_ms)
        if n <= 1:
            raise ValueError("SECONDS must be long enough for at least 2 samples.")

        t_ms = np.arange(n) * dt_ms
        t = (t_ms / 1000.0) if self.time_unit_seconds.get() else t_ms.astype(float)

        sigma = noise_amp / 3.0
        rng = np.random.default_rng(rng_seed)

        x_true = np.array([self._ramp_hold_value(profile, int(tm)) for tm in t_ms], dtype=float)
        x = x_true + rng.normal(0.0, sigma, size=n)
        return t, x

    # -------------------------
    # UI actions
    # -------------------------
    def _on_preview(self) -> None:
        t, x = self._preview_series()

        self._ax.clear()
        self._ax.grid(True)
        self._ax.plot(t, x)

        self._ax.set_title("Generated signal preview")
        self._ax.set_xlabel("time (s)" if self.time_unit_seconds.get() else "time (ms)")
        self._ax.set_ylabel("x")

        self._canvas.draw_idle()

    def _on_generate(self) -> None:
        try:
            profile = self._build_profile()

            out_path = generate_signal_csv(
                out_filename=self.out_filename.get().strip() or "signal.csv",
                dt_ms=int(self.dt_ms.get()),
                seconds=int(self.seconds.get()),
                profile=profile,
                noise_amp=float(self.noise_amp.get()),
                rng_seed=int(self.rng_seed.get()),
                time_unit_seconds=bool(self.time_unit_seconds.get()),
            )

            self.status.configure(text=f"Wrote: {out_path}")

            # Auto-refresh preview after generate
            self._schedule_preview(0)

            messagebox.showinfo("Signal Generator", f"Wrote CSV:\n{out_path}")

        except Exception as e:
            messagebox.showerror("Generate error", str(e))
