from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Dict, Type


class Router(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._pages: Dict[str, ttk.Frame] = {}
        self._current: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def add_page(self, name: str, page: ttk.Frame) -> None:
        self._pages[name] = page
        page.grid(row=0, column=0, sticky="nsew")

    def show(self, name: str) -> None:
        if name not in self._pages:
            raise KeyError(f"Unknown page: {name}")
        self._pages[name].tkraise()
        self._current = name

    @property
    def current(self) -> str | None:
        return self._current
