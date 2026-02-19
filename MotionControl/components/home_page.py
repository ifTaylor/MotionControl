from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable


class HomePage(ttk.Frame):
    def __init__(
        self,
        parent, *,
        on_open_kalman: Callable[[], None],
        on_open_generator: Callable[[], None],
        on_open_step_response_generator: Callable[[], None],
        on_open_step_response_identification: Callable[[], None],
    ):
        super().__init__(parent, padding=24)

        title = ttk.Label(self, text="MotionControl Toolkit", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(self, text="Choose a tool:", font=("Segoe UI", 11))
        subtitle.pack(anchor="w", pady=(6, 18))

        card = ttk.Frame(self, padding=16, relief="ridge")
        card.pack(anchor="nw", fill="x")
        ttk.Label(card, text="Kalman Tuning", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text="Load a signal CSV, select steady + ramp spans, compute tuning, and overlay AOI Kalman.", wraplength=700)\
            .pack(anchor="w", pady=(4, 10))
        ttk.Button(card, text="Open Kalman Tuning", command=on_open_kalman).pack(anchor="w")

        card2 = ttk.Frame(self, padding=16, relief="ridge")
        card2.pack(anchor="nw", fill="x", pady=(12, 0))
        ttk.Label(card2, text="Signal Generator", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card2, text="Generate a ramp/hold signal with Gaussian noise and write signal.csv to the app directory.", wraplength=700)\
            .pack(anchor="w", pady=(4, 10))
        ttk.Button(card2, text="Open Signal Generator", command=on_open_generator).pack(anchor="w")

        card3 = ttk.Frame(self, padding=16, relief="ridge")
        card3.pack(anchor="nw", fill="x", pady=(12, 0))
        ttk.Label(card3, text="Step Response Generator", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card3, text="Generate a step response from selected transfer functions.", wraplength=700)\
            .pack(anchor="w", pady=(4, 10))
        ttk.Button(card3, text="Open Step Response Generator", command=on_open_step_response_generator).pack(anchor="w")

        card4 = ttk.Frame(self, padding=16, relief="ridge")
        card4.pack(anchor="nw", fill="x", pady=(12, 0))
        ttk.Label(card4, text="Step Response Identification", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card4, text="Tune a step response from selected transfer functions.", wraplength=700)\
            .pack(anchor="w", pady=(4, 10))
        ttk.Button(card4, text="Open Step Response Identification", command=on_open_step_response_identification).pack(anchor="w")

        # Placeholder for future tools
        ttk.Separator(self).pack(fill="x", pady=18)
        ttk.Label(self, text="More tools can be added here later (PID, filters, etc.)", foreground="gray")\
            .pack(anchor="w")
