# components/main_view.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .toolbar_panel import ToolbarPanel
from .plot_panel import PlotPanel
from .results_panel import ResultsPanel
from .tuning_controls_panel import TuningControlsPanel


class MainView(ttk.Frame):
    def __init__(
        self,
        parent,
        *,
        on_load_csv: Callable[[], None],
        on_export_json: Callable[[], None],
        on_time_unit_changed: Callable[[], None],
        on_span_selected: Callable[[str, int, int], None],
        on_tuning_changed: Callable[[], None],
    ):
        super().__init__(parent, padding=0)

        self.time_unit_var = tk.StringVar(value="s")
        self.active_span_var = tk.StringVar(value="steady")

        # ---- toolbar at top ----
        self.toolbar = ToolbarPanel(
            self,
            on_load_csv=on_load_csv,
            on_export_json=on_export_json,
            on_time_unit_changed=on_time_unit_changed,
            time_unit_var=self.time_unit_var,
            active_span_var=self.active_span_var,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        content = ttk.Frame(self, padding=0)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        content.columnconfigure(0, weight=4)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # left: your existing paned window (plot + results)
        left = ttk.Frame(content)
        left.grid(row=0, column=0, sticky="nsew")

        # ---- PanedWindow: plot (top) + results (bottom) ----
        self.panes = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.panes.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Each pane should be a real Frame so it resizes cleanly
        self.plot_container = ttk.Frame(self.panes)
        self.results_container = ttk.Frame(self.panes)

        self.plot = PlotPanel(
            self.plot_container,
            on_span_selected=on_span_selected,
            active_span_var=self.active_span_var,
        )
        self.plot.pack(fill=tk.BOTH, expand=True)

        self.results = ResultsPanel(self.results_container)
        self.results.pack(fill=tk.BOTH, expand=True)

        # Add panes with initial sizing hints
        self.panes.add(self.plot_container, weight=4)    # plot gets more space
        self.panes.add(self.results_container, weight=1) # results still visible

        self.tuning_controls = TuningControlsPanel(content, on_change=on_tuning_changed)
        self.tuning_controls.grid(row=0, column=1, sticky="nsew", padx=(8, 8), pady=(8, 8))

        # Optional: set an initial sash position after layout
        self.after(50, self._set_initial_sash)

    def _set_initial_sash(self):
        # Put the divider so results get ~200px height initially
        try:
            total_h = self.winfo_height()
            if total_h > 300:
                self.panes.sashpos(0, int(total_h * 0.75))
        except Exception:
            pass

    def time_unit(self) -> str:
        return self.time_unit_var.get().strip().lower()
