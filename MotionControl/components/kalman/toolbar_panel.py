from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ToolbarPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        *,
        on_load_csv,
        on_export_json,
        on_time_unit_changed,
        time_unit_var: tk.StringVar,
        active_span_var: tk.StringVar,
    ):
        super().__init__(parent, padding=8)

        ttk.Button(self, text="Load CSV…", command=on_load_csv).pack(side=tk.LEFT)

        ttk.Label(self, text="Time unit:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Radiobutton(self, text="seconds", value="s", variable=time_unit_var, command=on_time_unit_changed).pack(side=tk.LEFT)
        ttk.Radiobutton(self, text="milliseconds", value="ms", variable=time_unit_var, command=on_time_unit_changed).pack(side=tk.LEFT)

        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(self, text="Active selection:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Radiobutton(self, text="STEADY (r_x)", value="steady", variable=active_span_var).pack(side=tk.LEFT)
        ttk.Radiobutton(self, text="RAMP (q_x_dot)", value="ramp", variable=active_span_var).pack(side=tk.LEFT)

        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(self, text="Export spans JSON…", command=on_export_json).pack(side=tk.LEFT, padx=(10, 0))
