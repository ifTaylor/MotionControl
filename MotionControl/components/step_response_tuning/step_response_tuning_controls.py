from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class StepTuningControls(ttk.Frame):
    """
    Left-side controls:
      - mode selector (Baseline/Final/Fit spans, Step/Deadtime/Peak points)
      - model dropdown
      - buttons: Load, Auto step, Auto deadtime, Fit
      - results text
    """

    def __init__(
        self,
        parent,
        *,
        active_mode_var: tk.StringVar,
        model_var: tk.StringVar,
        on_load: Callable[[], None],
        on_auto_step: Callable[[], None],
        on_auto_deadtime: Callable[[], None],
        on_fit: Callable[[], None],
        on_clear: Callable[[], None],
    ):
        super().__init__(parent, padding=10)

        self.active_mode_var = active_mode_var
        self.model_var = model_var

        # File actions
        file_box = ttk.LabelFrame(self, text="Data", padding=10)
        file_box.pack(fill="x")

        ttk.Button(file_box, text="Load step CSV", command=on_load).pack(fill="x")
        ttk.Button(file_box, text="Clear selections", command=on_clear).pack(fill="x", pady=(6, 0))

        # Mode selection
        mode_box = ttk.LabelFrame(self, text="Selection Mode", padding=10)
        mode_box.pack(fill="x", pady=(10, 0))

        def r(text, value):
            ttk.Radiobutton(mode_box, text=text, value=value, variable=self.active_mode_var).pack(anchor="w")

        ttk.Label(mode_box, text="Drag spans:").pack(anchor="w")
        r("Baseline span", "baseline")
        r("Final span (settled)", "final")
        r("Fit span (optional)", "fit")

        ttk.Separator(mode_box).pack(fill="x", pady=8)

        ttk.Label(mode_box, text="Click points:").pack(anchor="w")
        r("Step time (t_step)", "step")
        r("Deadtime start (t_dead)", "deadtime")
        r("Peak (underdamped)", "peak")

        # Model
        model_box = ttk.LabelFrame(self, text="Model", padding=10)
        model_box.pack(fill="x", pady=(10, 0))

        ttk.Label(model_box, text="PV model:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        cmb = ttk.Combobox(
            model_box,
            textvariable=self.model_var,
            state="readonly",
            values=["FOPDT", "IPDT", "SOPDT_UNDERDAMPED"],
            width=18,
        )
        cmb.grid(row=0, column=1, sticky="w")

        # Actions
        act = ttk.LabelFrame(self, text="Actions", padding=10)
        act.pack(fill="x", pady=(10, 0))

        ttk.Button(act, text="Auto-detect step time", command=on_auto_step).pack(fill="x")
        ttk.Button(act, text="Auto-detect deadtime", command=on_auto_deadtime).pack(fill="x", pady=(6, 0))
        ttk.Button(act, text="Fit / Identify model", command=on_fit).pack(fill="x", pady=(10, 0))

        # Results
        res = ttk.LabelFrame(self, text="Results", padding=10)
        res.pack(fill="both", expand=True, pady=(10, 0))

        self._txt = tk.Text(res, height=18, wrap="none")
        self._txt.pack(fill="both", expand=True)

        self.set_results_text("Load a CSV, then select baseline/final spans and fit.\n")

    def set_results_text(self, text: str) -> None:
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.insert("1.0", text)
        self._txt.configure(state="disabled")