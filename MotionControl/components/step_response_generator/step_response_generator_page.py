from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.step_response_generator import (
    StepSpec,
    ActuatorParams,
    FOPDTParams,
    IPDTParams,
    SOPDTUnderdampedParams,
)

from services import (
    simulate_step_response,
    export_step_csv,
)


class StepResponsePage(ttk.Frame):
    def __init__(self, parent, *, on_back: Callable[[], None]):
        super().__init__(parent, padding=0)
        self._preview_job = None

        header = ttk.Frame(self, padding=8)
        header.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(header, text="← Back", command=on_back).pack(side=tk.LEFT)
        ttk.Label(header, text="Step Response Generator", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=10)

        body = ttk.Frame(self, padding=16)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # -------- Vars --------
        self.out_filename = tk.StringVar(value="step_response.csv")
        self.time_unit_seconds = tk.BooleanVar(value=True)

        # Step spec
        self.dt_s = tk.StringVar(value="0.05")
        self.duration_s = tk.StringVar(value="5.0")
        self.t_step_s = tk.StringVar(value="1.0")
        self.cv0 = tk.StringVar(value="0.0")
        self.cv_step = tk.StringVar(value="10.0")

        # Model
        self.model = tk.StringVar(value="FOPDT")

        # Actuator
        self.pv0 = tk.StringVar(value="0.0")
        self.pv_min = tk.StringVar(value="0")
        self.pv_max = tk.StringVar(value="9")
        self.rate_limit = tk.StringVar(value="0.0")
        self.act_tau = tk.StringVar(value="0.0")

        # FOPDT params
        self.f_k = tk.StringVar(value="1.0")
        self.f_tau = tk.StringVar(value="0.3")
        self.f_theta = tk.StringVar(value="0.2")

        # IPDT params
        self.i_k = tk.StringVar(value="0.4")
        self.i_theta = tk.StringVar(value="0.3")
        self.i_leak_tau = tk.StringVar(value="0.0")

        # Underamped params
        self.s_k = tk.StringVar(value="1.0")
        self.s_zeta = tk.StringVar(value="0.45")
        self.s_wn = tk.StringVar(value="6.0")
        self.s_theta = tk.StringVar(value="0.3")

        # -------- Helpers --------
        def add_row(frame: ttk.Frame, row: int, label: str, var: tk.Variable, *, width: int = 16) -> int:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            e = ttk.Entry(frame, textvariable=var, width=width)
            e.grid(row=row, column=1, sticky="w", pady=3)
            e.bind("<Return>", lambda _e: self._schedule_preview(0))
            e.bind("<FocusOut>", lambda _e: self._schedule_preview(0))
            return row + 1

        def trace_all(*_):
            self._schedule_preview(200)

        # -------- Export --------
        out_box = ttk.LabelFrame(left, text="Export", padding=10)
        out_box.pack(fill="x")
        r = 0
        r = add_row(out_box, r, "CSV filename:", self.out_filename, width=22)
        ttk.Checkbutton(
            out_box, text="Time in seconds (else ms)",
            variable=self.time_unit_seconds,
            command=lambda: self._schedule_preview(0),
        ).grid(row=r, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # -------- Step --------
        step_box = ttk.LabelFrame(left, text="CV Command", padding=10)
        step_box.pack(fill="x", pady=(10, 0))
        r = 0
        r = add_row(step_box, r, "dt (s):", self.dt_s)
        r = add_row(step_box, r, "duration (s):", self.duration_s)
        r = add_row(step_box, r, "t_step (s):", self.t_step_s)
        r = add_row(step_box, r, "CV0:", self.cv0)
        r = add_row(step_box, r, "CV_STEP:", self.cv_step)

        # -------- Actuator --------
        act_box = ttk.LabelFrame(left, text="Actuator (system does something else)", padding=10)
        act_box.pack(fill="x", pady=(10, 0))
        r = 0
        r = add_row(act_box, r, "PV0:", self.pv0)
        r = add_row(act_box, r, "PV_MIN:", self.pv_min)
        r = add_row(act_box, r, "PV_MAX:", self.pv_max)
        r = add_row(act_box, r, "Rate limit (CV/s):", self.rate_limit)
        r = add_row(act_box, r, "Actuator tau (s):", self.act_tau)

        # -------- Model selection --------
        model_box = ttk.LabelFrame(left, text="Transfer Function", padding=10)
        model_box.pack(fill="x", pady=(10, 0))

        ttk.Label(model_box, text="Select function:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        cmb = ttk.Combobox(
            model_box, textvariable=self.model, state="readonly",
            values=["FOPDT", "IPDT", "SOPDT_UNDERDAMPED"], width=18
        )
        cmb.grid(row=0, column=1, sticky="w")
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._on_model_changed())

        self._fopdt_frame = ttk.Frame(model_box)
        self._sopdt_frame = ttk.Frame(model_box)
        self._ipdt_frame = ttk.Frame(model_box)
        for f in (self._fopdt_frame, self._ipdt_frame, self._sopdt_frame):
            f.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        rr = 0
        rr = add_row(self._fopdt_frame, rr, "K:", self.f_k)
        rr = add_row(self._fopdt_frame, rr, "tau (s):", self.f_tau)
        rr = add_row(self._fopdt_frame, rr, "theta (s):", self.f_theta)

        rr = 0
        rr = add_row(self._ipdt_frame, rr, "K:", self.i_k)
        rr = add_row(self._ipdt_frame, rr, "theta (s):", self.i_theta)
        rr = add_row(self._ipdt_frame, rr, "leak_tau (s) (0=pure):", self.i_leak_tau)

        rr = 0
        rr = add_row(self._sopdt_frame, rr, "K:", self.s_k)
        rr = add_row(self._sopdt_frame, rr, "zeta:", self.s_zeta)
        rr = add_row(self._sopdt_frame, rr, "wn (rad/s):", self.s_wn)
        rr = add_row(self._sopdt_frame, rr, "theta (s):", self.s_theta)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Preview now", command=self._on_preview).pack(side=tk.LEFT)
        ttk.Button(btns, text="Export CSV", command=self._on_export).pack(side=tk.LEFT, padx=(8, 0))

        self.status = ttk.Label(left, text="", foreground="gray")
        self.status.pack(anchor="w", pady=(8, 0))

        # -------- Plot --------
        self._fig = Figure(figsize=(9.0, 6.0), dpi=100)
        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.grid(True)
        self._ax.set_title("Step Response Preview")
        self._ax.set_xlabel("time (s)")
        self._ax.set_ylabel("PV")

        self._canvas = FigureCanvasTkAgg(self._fig, master=right)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # traces -> auto preview
        for v in [
            self.out_filename, self.dt_s, self.duration_s, self.t_step_s, self.cv0, self.cv_step,
            self.pv0, self.pv_min, self.pv_max, self.rate_limit, self.act_tau,
            self.f_k, self.f_tau, self.f_theta,
            self.i_k, self.i_theta, self.i_leak_tau,
            self.s_k, self.s_zeta, self.s_wn, self.s_theta,
        ]:
            v.trace_add("write", trace_all)

        self._on_model_changed()
        self._schedule_preview(0)

    def _on_model_changed(self) -> None:
        m = self.model.get()
        self._fopdt_frame.grid_remove()
        self._ipdt_frame.grid_remove()
        self._sopdt_frame.grid_remove()
        if m == "FOPDT":
            self._fopdt_frame.grid()
        elif m == "IPDT":
            self._ipdt_frame.grid()
        elif m == "SOPDT_UNDERDAMPED":
            self._sopdt_frame.grid()
        self._schedule_preview(0)

    def _schedule_preview(self, delay_ms: int = 200) -> None:
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
            pass

    def _build_spec(self) -> StepSpec:
        return StepSpec(
            dt_s=float(self.dt_s.get()),
            duration_s=float(self.duration_s.get()),
            t_step_s=float(self.t_step_s.get()),
            cv0=float(self.cv0.get()),
            cv_step=float(self.cv_step.get()),
        )

    def _build_actuator(self) -> ActuatorParams:
        return ActuatorParams(
            pv0=float(self.pv0.get()),
            pv_min=float(self.pv_min.get()),
            pv_max=float(self.pv_max.get()),
            rate_limit=float(self.rate_limit.get()),
            tau_s=float(self.act_tau.get()),
        )

    def _simulate(self):
        spec = self._build_spec()
        actuator = self._build_actuator()
        m = self.model.get()

        if m == "FOPDT":
            p = FOPDTParams(
                K=float(self.f_k.get()),
                tau_s=float(self.f_tau.get()),
                theta_s=float(self.f_theta.get()),
            )
            return simulate_step_response(spec=spec, actuator=actuator, model="FOPDT", fopdt=p)
        elif m == "IPDT":
            i = IPDTParams(
                K=float(self.i_k.get()),
                theta_s=float(self.i_theta.get()),
                leak_tau_s=float(self.i_leak_tau.get()),
            )
            return simulate_step_response(spec=spec, actuator=actuator, model="IPDT", ipdt=i)
        elif m == "SOPDT_UNDERDAMPED":
            p = SOPDTUnderdampedParams(
                K=float(self.s_k.get()),
                zeta=float(self.s_zeta.get()),
                wn=float(self.s_wn.get()),
                theta_s=float(self.s_theta.get()),
            )
            return simulate_step_response(spec=spec, actuator=actuator, model="SOPDT_UNDERDAMPED", sopdt=p)

    def _on_preview(self) -> None:
        t, cv_cmd, pv, cv_eff = self._simulate()

        self._ax.clear()
        self._ax.grid(True)

        # Plot raw signals
        self._ax.plot(t, pv, label="PV")
        self._ax.plot(t, cv_cmd, "--", label="CV_cmd")

        self._ax.set_title(f"Step Response Preview — {self.model.get()}")
        self._ax.set_xlabel("time (s)")
        self._ax.set_ylabel("Value")
        self._ax.legend(loc="best")

        self._canvas.draw_idle()

    def _on_export(self) -> None:
        try:
            t, cv_cmd, pv, _cv_eff = self._simulate()
            out_name = (self.out_filename.get().strip() or "step_response.csv")
            out_path = export_step_csv(
                out_filename=out_name,
                t=t,
                cv_cmd=cv_cmd,
                pv=pv,
                time_unit_seconds=bool(self.time_unit_seconds.get()),
            )
            self.status.configure(text=f"Wrote: {out_path}")
            messagebox.showinfo("Export", f"Wrote CSV:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))