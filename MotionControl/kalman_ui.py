from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

from components import (
    Router,
    HomePage,
    KalmanPage,
    SignalGeneratorPage,
    StepResponsePage,
    StepTuningPage,
)
from models.kalman import (
    SpanSelections,
    TimeSeriesData,
    TuningResult,
    TuningOverrides,
    KalmanRunConfig,
)

from services import (
    load_csv,
    compute_tuning,
    export_spans_json,
)


class Ctrl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MotionControl")
        self.root.geometry("1200x900")

        # Router
        self.router = Router(self.root)
        self.router.pack(fill=tk.BOTH, expand=True)

        # ---- Kalman state (same as before) ----
        self.ts: TimeSeriesData | None = None
        self.spans = SpanSelections()
        self.result: TuningResult | None = None
        self.overrides = TuningOverrides()

        # Pages
        self.home_page = HomePage(
            self.router,
            on_open_kalman=lambda: self.router.show("kalman"),
            on_open_generator=lambda: self.router.show("signal_generator"),
            on_open_step_response_generator=lambda: self.router.show("step_response_generator"),
            on_open_step_response_identification=lambda: self.router.show("step_response_identification"),
        )

        self.kalman_page = KalmanPage(
            self.router,
            on_back=lambda: self.router.show("home"),
            on_load_csv=self.on_load_csv,
            on_export_json=self.on_export_json,
            on_time_unit_changed=self.on_time_unit_changed,
            on_span_selected=self.on_span_selected,
            on_tuning_changed=self.on_tuning_changed,
        )

        self.signal_generator_page = SignalGeneratorPage(
            self.router,
            on_back=lambda: self.router.show("home"),
        )

        self.step_page = StepResponsePage(
            self.router,
            on_back=lambda: self.router.show("home")
        )

        self.step_response_id_page = StepTuningPage(
            self.router,
            on_back=lambda: self.router.show("home"),
        )

        self.router.add_page("home", self.home_page)
        self.router.add_page("kalman", self.kalman_page)
        self.router.add_page("signal_generator", self.signal_generator_page)
        self.router.add_page("step_response_generator", self.step_page)
        self.router.add_page("step_response_identification", self.step_response_id_page)

        self.router.show("home")

    @property
    def view(self):
        return self.kalman_page.view

    def on_load_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            self.ts = load_csv(path, time_unit=self.view.time_unit())
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            return

        self.spans.clear()
        self.result = None

        self.view.plot.set_series(self.ts.t, self.ts.x)
        self.view.plot.set_spans(self.spans.steady.as_tuple(), self.spans.ramp.as_tuple())

        self.recompute()

    def on_time_unit_changed(self) -> None:
        # If we already loaded a CSV, re-load it with the new time unit.
        if self.ts is None:
            return
        try:
            self.ts = load_csv(self.ts.source_path, time_unit=self.view.time_unit())
        except Exception as e:
            messagebox.showerror("Time unit error", str(e))
            return

        self.view.plot.set_series(self.ts.t, self.ts.x)
        self.recompute()

    def on_span_selected(self, span_type: str, a: int, b: int) -> None:
        try:
            self.spans.set_span(span_type, a, b)
        except Exception as e:
            messagebox.showerror("Span error", str(e))
            return

        self.view.plot.set_spans(self.spans.steady.as_tuple(), self.spans.ramp.as_tuple())
        self.recompute()

    def on_tuning_changed(self) -> None:
        # read UI state into self.overrides
        st = self.view.tuning_controls.get_state()
        try:
            self.overrides.use_manual_r_x = st["use_manual_r_x"]
            self.overrides.use_manual_q_x = st["use_manual_q_x"]
            self.overrides.use_manual_q_x_dot = st["use_manual_q_x_dot"]

            self.overrides.manual_r_x = float(st["manual_r_x"])
            self.overrides.manual_q_x = float(st["manual_q_x"])
            self.overrides.manual_q_x_dot = float(st["manual_q_x_dot"])
        except Exception as e:
            # don't throw modal dialogs on every keystroke; just ignore until valid
            return

        self.recompute()

    def on_export_json(self) -> None:
        if self.ts is None:
            messagebox.showinfo("Nothing to export", "Load a CSV first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save spans JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            export_spans_json(path, self.ts, self.spans)
        except Exception as e:
            messagebox.showerror("Export error", str(e))
            return

        messagebox.showinfo("Exported", f"Saved: {path}")

    def recompute(self) -> None:
        if self.ts is None:
            self.result = None
            self.view.results.render(self.ts, self.spans, self.result)
            self.view.plot.set_kalman(None)
            return

        self.result = compute_tuning(self.ts, self.spans)
        self.view.results.render(self.ts, self.spans, self.result)

        # let tuning panel know dt for helper button
        self.view.tuning_controls.set_dt(self.ts.dt_s)

        # suggested values (from spans)
        suggested_r = self.result.r_x if self.result is not None else float("nan")
        suggested_qxd = self.result.q_x_dot if self.result is not None else float("nan")
        suggested_qx = self.result.q_x_user if self.result is not None else float("nan")

        # push suggested into UI fields (only if not manual)
        self.view.tuning_controls.set_suggested(r_x=suggested_r, q_x=suggested_qx, q_x_dot=suggested_qxd)

        # active values (manual overrides win)
        r_x = self.overrides.active_r_x(suggested_r)
        q_x = self.overrides.active_q_x(suggested_qx)
        q_x_dot = self.overrides.active_q_x_dot(suggested_qxd)

        # Only plot kalman if numbers are finite
        if np.isfinite(r_x) and np.isfinite(q_x) and np.isfinite(q_x_dot):
            cfg = KalmanRunConfig(r_x=r_x, q_x=q_x, q_x_dot=q_x_dot)
            self.view.plot.set_kalman(cfg, show=True)
        else:
            self.view.plot.set_kalman(None)

    def run(self):
        self.root.mainloop()


def main():
    Ctrl().run()


if __name__ == "__main__":
    main()
