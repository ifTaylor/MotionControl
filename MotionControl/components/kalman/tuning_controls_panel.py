from __future__ import annotations

import tkinter as tk
from tkinter import ttk

class TuningControlsPanel(ttk.LabelFrame):
    def __init__(self, parent, *, on_change):
        super().__init__(parent, text="Tuning Controls (Auto vs Manual)", padding=8)

        self._on_change = on_change

        # vars
        self.use_r = tk.BooleanVar(value=False)
        self.use_qx = tk.BooleanVar(value=False)
        self.use_qxd = tk.BooleanVar(value=False)

        self.r_x = tk.StringVar(value="1.0")
        self.q_x = tk.StringVar(value="0.0")
        self.q_x_dot = tk.StringVar(value="0.0")

        # layout
        grid = ttk.Frame(self)
        grid.pack(fill="x", expand=True)

        # row helper
        def row(i, label, use_var, val_var):
            ttk.Checkbutton(grid, text=f"Manual {label}", variable=use_var, command=self._on_change).grid(row=i, column=0, sticky="w", padx=(0, 8))
            e = ttk.Entry(grid, textvariable=val_var, width=18)
            e.grid(row=i, column=1, sticky="w")
            e.bind("<Return>", lambda _e: self._on_change())
            e.bind("<FocusOut>", lambda _e: self._on_change())

        row(0, "r_x", self.use_r, self.r_x)
        row(1, "q_x_dot", self.use_qxd, self.q_x_dot)
        row(2, "q_x", self.use_qx, self.q_x)

        # optional helper: set q_x = q_x_dot * dt^2 (useful for your mapping)
        self._btn_map = ttk.Button(grid, text="Set q_x = q_x_dot * dt²", command=self._on_map_qx)
        self._btn_map.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # store last dt for helper
        self._dt_s = None

    def set_dt(self, dt_s: float | None) -> None:
        self._dt_s = dt_s

    def _on_map_qx(self):
        try:
            qxd = float(self.q_x_dot.get())
            if self._dt_s is None:
                return
            self.q_x.set(str(qxd * (float(self._dt_s) ** 2)))
            self.use_qx.set(True)
        except Exception:
            pass
        self._on_change()

    def get_state(self) -> dict:
        # controller converts to model
        return {
            "use_manual_r_x": bool(self.use_r.get()),
            "use_manual_q_x": bool(self.use_qx.get()),
            "use_manual_q_x_dot": bool(self.use_qxd.get()),
            "manual_r_x": self.r_x.get(),
            "manual_q_x": self.q_x.get(),
            "manual_q_x_dot": self.q_x_dot.get(),
        }

    def set_suggested(self, *, r_x: float | None, q_x: float | None, q_x_dot: float | None):
        # only update text boxes if that field is NOT manual (so we don't overwrite user input)
        if not self.use_r.get() and r_x is not None:
            self.r_x.set(f"{r_x:.9g}")
        if not self.use_qx.get() and q_x is not None:
            self.q_x.set(f"{q_x:.9g}")
        if not self.use_qxd.get() and q_x_dot is not None:
            self.q_x_dot.set(f"{q_x_dot:.9g}")
