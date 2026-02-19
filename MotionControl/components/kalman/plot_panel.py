from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import SpanSelector
import numpy as np

from services.kalman_service import run_procedural_kalman, KalmanRunConfig


class PlotPanel(ttk.Frame):
    def __init__(self, parent, *, on_span_selected: Callable[[str, int, int], None], active_span_var: tk.StringVar):
        super().__init__(parent, padding=8)

        self._on_span_selected = on_span_selected
        self._active_span_var = active_span_var

        self._t: Optional[np.ndarray] = None
        self._x: Optional[np.ndarray] = None
        self._steady_span: Optional[Tuple[int, int]] = None
        self._ramp_span: Optional[Tuple[int, int]] = None

        self._kalman_cfg: Optional[KalmanRunConfig] = None
        self._show_kalman: bool = True

        self.fig = Figure(figsize=(11.5, 7.5), dpi=100)
        self.ax_full = self.fig.add_subplot(1, 1, 1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        self._span_selector = SpanSelector(
            self.ax_full,
            onselect=self._on_span_select,
            direction="horizontal",
            useblit=True,
            interactive=True,
            drag_from_anywhere=True,
        )

        self.redraw()

    def set_series(self, t: np.ndarray, x: np.ndarray) -> None:
        self._t = t
        self._x = x
        self.redraw()

    def set_spans(self, steady_span: Optional[Tuple[int, int]], ramp_span: Optional[Tuple[int, int]]) -> None:
        self._steady_span = steady_span
        self._ramp_span = ramp_span
        self.redraw()

    def set_kalman(self, cfg: Optional[KalmanRunConfig], *, show: bool = True) -> None:
        self._kalman_cfg = cfg
        self._show_kalman = show
        self.redraw()

    def _on_span_select(self, xmin: float, xmax: float) -> None:
        if self._t is None or self._x is None:
            return
        if xmax < xmin:
            xmin, xmax = xmax, xmin

        a = int(np.searchsorted(self._t, xmin, side="left"))
        b = int(np.searchsorted(self._t, xmax, side="right"))

        a = max(0, min(a, len(self._t) - 1))
        b = max(a + 1, min(b, len(self._t)))

        span_type = self._active_span_var.get().strip().lower()
        self._on_span_selected(span_type, a, b)

    def redraw(self) -> None:
        self._draw_full()
        self.canvas.draw_idle()

    def _draw_full(self) -> None:
        self.ax_full.clear()
        self.ax_full.grid(True)

        if self._t is None or self._x is None:
            self.ax_full.set_title("Full signal (drag to select span)")
            self.ax_full.set_xlabel("time")
            self.ax_full.set_ylabel("x")
            return

        self.ax_full.plot(self._t, self._x, label="x (measured)")

        # spans
        if self._steady_span is not None:
            a, b = self._steady_span
            self.ax_full.axvspan(self._t[a], self._t[b - 1], alpha=0.20, label="STEADY span")
        if self._ramp_span is not None:
            a, b = self._ramp_span
            self.ax_full.axvspan(self._t[a], self._t[b - 1], alpha=0.20, label="RAMP span")

        # procedural kalman overlay
        if self._show_kalman and self._kalman_cfg is not None:
            y, y_dot = run_procedural_kalman(self._t, self._x, self._kalman_cfg)
            self.ax_full.plot(self._t, y, label="kalman y (x̂)")
            # optional: velocity on 2nd axis if you want later

        self.ax_full.set_title("Signal + spans + procedural Kalman overlay")
        self.ax_full.set_xlabel("time (s)")
        self.ax_full.set_ylabel("x")
        self.ax_full.legend(loc="upper right")
