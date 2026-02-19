# components/results_panel.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import numpy as np

from models.kalman import TimeSeriesData, SpanSelections, TuningResult


class ResultsPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Computed Tuning (from selected spans)", padding=8)

        self._text = tk.Text(self, height=8, wrap="word")
        self._text.configure(font=("Courier New", 10), state="disabled")

        sb = ttk.Scrollbar(self, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=sb.set)

        self._text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def set_text(self, text: str) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._text.configure(state="disabled")

    def render(self, ts: TimeSeriesData | None, spans: SpanSelections, result: TuningResult | None) -> None:
        if ts is None:
            self.set_text("Load a CSV to begin.")
            return

        lines = []
        lines.append(f"source: {ts.source_path}")
        lines.append(f"dt_s (median): {ts.dt_s:.9f}")

        # STEADY
        if spans.steady.as_tuple() is not None:
            a, b = spans.steady.as_tuple()
            lines.append("")
            lines.append("STEADY span (for r_x):")
            lines.append(f"  indices: [{a}:{b})  (N={b-a})")
            lines.append(f"  time:    [{ts.t[a]:.6f} .. {ts.t[b-1]:.6f}] s")
            if result is not None:
                lines.append(f"  r_x = Var(x): {result.r_x:.9g}")
                lines.append(f"  sigma_x:      {result.sigma_x:.9g}")
        else:
            lines.append("")
            lines.append("STEADY span (for r_x): not selected")

        # RAMP
        if spans.ramp.as_tuple() is not None:
            a, b = spans.ramp.as_tuple()
            lines.append("")
            lines.append("RAMP span (for q_x_dot):")
            lines.append(f"  indices: [{a}:{b})  (N={b-a})")
            lines.append(f"  time:    [{ts.t[a]:.6f} .. {ts.t[b-1]:.6f}] s")
            if result is not None:
                lines.append(f"  dv samples used: {result.dv_count}")
                lines.append(f"  q_x_dot = Var.S(Δv): {result.q_x_dot:.9g}")
                lines.append(f"  q_x (user)        = q_x_dot*dt^2: {result.q_x_user:.9g}")
                lines.append(f"  q_x (consistent)  = 0.25*q_x_dot*dt^2: {result.q_x_consistent:.9g}")
                lines.append(f"  q_xv (consistent) = 0.5*q_x_dot*dt: {result.q_xv_consistent:.9g}")
        else:
            lines.append("")
            lines.append("RAMP span (for q_x_dot): not selected")

        self.set_text("\n".join(lines))
