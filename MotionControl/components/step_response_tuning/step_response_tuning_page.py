from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional

import numpy as np

from .step_response_tuning_plot_panel import StepTuningPlotPanel
from .step_response_tuning_controls import StepTuningControls

from models.step_response_tuning import (
    StepTuneSelections,
    StepIdResult
)

from services import (
    load_step_csv,
    auto_detect_step_index,
    auto_detect_deadtime_index,
    identify,
    StepSeries,
)


class StepTuningPage(ttk.Frame):
    def __init__(self, parent, *, on_back: Callable[[], None]):
        super().__init__(parent, padding=0)

        self.ts: Optional[StepSeries] = None
        self.selections = StepTuneSelections()
        self.result: Optional[StepIdResult] = None
        self.pv_hat: Optional[np.ndarray] = None

        # ===== Header =====
        header = ttk.Frame(self, padding=8)
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(header, text="← Back", command=on_back).pack(side=tk.LEFT)
        ttk.Label(header, text="Step Response Tuner", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=10)

        # ===== Body (Paned) =====
        pan = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        pan.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(pan)
        right = ttk.Frame(pan)
        pan.add(left, weight=0)
        pan.add(right, weight=1)

        # Vars
        self.active_mode = tk.StringVar(value="baseline")
        self.model = tk.StringVar(value="FOPDT")

        # Controls
        self.controls = StepTuningControls(
            left,
            active_mode_var=self.active_mode,
            model_var=self.model,
            on_load=self._on_load,
            on_auto_step=self._on_auto_step,
            on_auto_deadtime=self._on_auto_deadtime,
            on_fit=self._on_fit,
            on_clear=self._on_clear,
        )
        self.controls.pack(fill="both", expand=True)

        # Plot panel
        self.plot = StepTuningPlotPanel(
            right,
            on_span_selected=self._on_span_selected,
            on_point_selected=self._on_point_selected,
            active_mode_var=self.active_mode,
        )
        self.plot.pack(fill="both", expand=True)

        self._refresh_ui()

    # ----------------------------
    # UI events
    # ----------------------------
    def _on_load(self) -> None:
        path = filedialog.askopenfilename(
            title="Select step response CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            # assumes time in seconds; change to "ms" if needed
            self.ts = load_step_csv(path, time_unit="s")
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            return

        self.selections.clear_all()
        self.result = None
        self.pv_hat = None

        self.plot.set_series(self.ts.t, self.ts.cv, self.ts.pv)
        self._refresh_ui()

    def _on_clear(self) -> None:
        self.selections.clear_all()
        self.result = None
        self.pv_hat = None
        self._refresh_plot_annotations()
        self._refresh_ui()

    def _on_span_selected(self, span_name: str, a: int, b: int) -> None:
        try:
            self.selections.set_span(span_name, a, b)
        except Exception as e:
            messagebox.showerror("Span error", str(e))
            return
        self.result = None
        self.pv_hat = None
        self._refresh_plot_annotations()
        self._refresh_ui()

    def _on_point_selected(self, point_name: str, i: int) -> None:
        try:
            self.selections.set_point(point_name, i)
        except Exception as e:
            messagebox.showerror("Point error", str(e))
            return
        self.result = None
        self.pv_hat = None
        self._refresh_plot_annotations()
        self._refresh_ui()

    def _on_auto_step(self) -> None:
        if self.ts is None:
            return
        i = auto_detect_step_index(self.ts)
        self.selections.t_step.set(i)
        self.result = None
        self.pv_hat = None
        self._refresh_plot_annotations()
        self._refresh_ui()

    def _on_auto_deadtime(self) -> None:
        if self.ts is None:
            return
        i = auto_detect_deadtime_index(self.ts, self.selections)
        if i is None:
            messagebox.showwarning("Deadtime", "Could not auto-detect deadtime. Ensure baseline span is selected.")
            return
        self.selections.t_dead.set(int(i))
        self.result = None
        self.pv_hat = None
        self._refresh_plot_annotations()
        self._refresh_ui()

    def _on_fit(self) -> None:
        if self.ts is None:
            return
        try:
            res, pv_hat = identify(self.ts, self.selections, self.model.get())
        except Exception as e:
            messagebox.showerror("Fit error", str(e))
            return

        self.result = res
        self.pv_hat = pv_hat
        self.plot.set_overlay(self.pv_hat)
        self._refresh_ui()

    # ----------------------------
    # refresh
    # ----------------------------
    def _refresh_plot_annotations(self) -> None:
        base = self.selections.baseline.as_tuple()
        final = self.selections.final.as_tuple()
        fit = self.selections.fit.as_tuple()

        self.plot.set_spans(base, final, fit)
        self.plot.set_points(
            self.selections.t_step.get(),
            self.selections.t_dead.get(),
            self.selections.peak.get(),
        )
        self.plot.set_overlay(self.pv_hat)

    def _refresh_ui(self) -> None:
        if self.ts is None:
            self.controls.set_results_text("Load a CSV, then select baseline/final spans and fit.\n")
            self._refresh_plot_annotations()
            return

        lines = []
        lines.append(f"source: {self.ts.source_path}")
        lines.append(f"dt_s (median): {self.ts.dt_s:.9f}")
        lines.append("")
        lines.append("Selections:")

        def span_line(name, sp):
            if sp is None:
                return f"  {name}: (none)"
            a, b = sp
            return f"  {name}: [{a}:{b})  N={b-a}  t=[{self.ts.t[a]:.6f}..{self.ts.t[b-1]:.6f}]"

        lines.append(span_line("baseline", self.selections.baseline.as_tuple()))
        lines.append(span_line("final   ", self.selections.final.as_tuple()))
        lines.append(span_line("fit     ", self.selections.fit.as_tuple()))

        def point_line(name, i):
            if i is None:
                return f"  {name}: (none)"
            return f"  {name}: i={i}  t={self.ts.t[i]:.6f}"

        lines.append(point_line("t_step", self.selections.t_step.get()))
        lines.append(point_line("t_dead", self.selections.t_dead.get()))
        lines.append(point_line("peak  ", self.selections.peak.get()))

        lines.append("")
        lines.append(f"Model: {self.model.get()}")

        if self.result is not None:
            r = self.result
            lines.append("")
            lines.append("Identified:")
            lines.append(f"  cv0={r.cv0:.6g}  cv1={r.cv1:.6g}  du={r.du:.6g}")
            lines.append(f"  pv0={r.pv0:.6g}  pv1={r.pv1:.6g}  dy={r.dy:.6g}")
            lines.append(f"  t_step={r.t_step_s:.6g} s  theta={r.theta_s:.6g} s")
            for k, v in r.params.items():
                lines.append(f"  {k} = {v:.9g}")
            lines.append(f"  RMSE = {r.rmse:.6g}   (N_fit={r.n_fit})")
            if r.note:
                lines.append("")
                lines.append(f"Note: {r.note}")

        self.controls.set_results_text("\n".join(lines))
        self._refresh_plot_annotations()