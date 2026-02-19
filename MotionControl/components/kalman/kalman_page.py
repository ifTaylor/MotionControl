from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .main_view import MainView


class KalmanPage(ttk.Frame):
    def __init__(
        self,
        parent,
        *,
        on_back: Callable[[], None],
        on_load_csv: Callable[[], None],
        on_export_json: Callable[[], None],
        on_time_unit_changed: Callable[[], None],
        on_span_selected: Callable[[str, int, int], None],
        on_tuning_changed: Callable[[], None],
    ):
        super().__init__(parent, padding=0)

        header = ttk.Frame(self, padding=8)
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(header, text="← Back", command=on_back).pack(side=tk.LEFT)
        ttk.Label(header, text="Kalman Tuning", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=10)

        # Your existing view goes under the header
        self.view = MainView(
            self,
            on_load_csv=on_load_csv,
            on_export_json=on_export_json,
            on_time_unit_changed=on_time_unit_changed,
            on_span_selected=on_span_selected,
            on_tuning_changed=on_tuning_changed,
        )
        self.view.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
