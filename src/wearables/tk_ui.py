"""Native Tkinter desktop UI for Android Bluetooth/Wi-Fi checks."""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .adapters import BleakWearableAdapter, FakeWearableAdapter
from .android_adb import AndroidAdbAdapter
from .cases import ConnectivityTestCase, bluetooth_cases, wifi_cases
from .models import TestCaseResult
from .runner import TestRunner


PRESETS: dict[str, tuple[str, ...]] = {
    "Quick smoke": (
        "bluetooth_discovery",
        "bluetooth_connect",
        "bluetooth_reconnect",
        "wifi_connected",
        "wifi_ip_configured",
        "wifi_gateway_configured",
        "wifi_dns_configured",
        "wifi_signal_quality",
    ),
    "BLE basics": (
        "bluetooth_discovery",
        "bluetooth_connect",
        "bluetooth_reconnect",
        "bluetooth_pairing_auth",
        "bluetooth_signal_quality",
        "bluetooth_connection_drop",
        "bluetooth_gatt_service_discovery",
        "bluetooth_gatt_read",
        "bluetooth_gatt_write",
        "bluetooth_gatt_notifications",
    ),
    "Wi-Fi basics": (
        "wifi_connected",
        "wifi_ip_configured",
        "wifi_ipv6_address",
        "wifi_gateway_configured",
        "wifi_dns_configured",
        "wifi_dns_resolution",
        "wifi_signal_quality",
        "wifi_internet_reachability",
        "wifi_network_probe",
        "wifi_reconnect",
    ),
}


class ConnectivityDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Android Connectivity Test Lab")
        self.root.geometry("1280x820")
        self.root.minsize(900, 620)
        self.root.configure(background="#eef3f5")
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._busy = False
        self._devices: dict[str, str] = {}
        self._cases = self._load_cases(FakeWearableAdapter())
        self._case_by_id = {case.name: case for case in self._cases}
        self._selected: set[str] = set()
        self._last_results: list[dict[str, Any]] = []

        self.adapter_var = tk.StringVar(value="Demo / fake")
        self.filter_var = tk.StringVar()
        self.serial_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.domain_var = tk.StringVar(value="All")
        self.category_var = tk.StringVar(value="All categories")
        self.device_var = tk.StringVar()
        self.probe_host_var = tk.StringVar()
        self.probe_port_var = tk.StringVar(value="443")
        self.status_var = tk.StringVar(value="Choose an adapter and select a test preset to begin.")
        self.summary_var = tk.StringVar(value="No test run yet")

        self._configure_style()
        self._build_layout()
        self._render_catalog()
        self.root.after(100, self._poll_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _load_cases(adapter: Any) -> list[ConnectivityTestCase]:
        return bluetooth_cases(adapter) + wifi_cases(adapter)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#eef3f5")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#eef3f5", foreground="#173141", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#153342")
        style.configure("Sub.TLabel", foreground="#5d707c")
        style.configure("TLabelframe", background="#ffffff", bordercolor="#d8e2e6")
        style.configure("TLabelframe.Label", background="#ffffff", foreground="#153342", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), padding=(12, 7))

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=(18, 14))
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Connectivity Test Lab", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Android Bluetooth and Wi-Fi validation · unknown capabilities are skipped, never guessed",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        adapter_frame = ttk.LabelFrame(outer, text="Device and adapter", padding=12)
        adapter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(adapter_frame, text="Adapter").grid(row=0, column=0, sticky="w", padx=(0, 8))
        adapter = ttk.Combobox(
            adapter_frame,
            textvariable=self.adapter_var,
            values=("Demo / fake", "Host BLE device", "Android phone via ADB"),
            state="readonly",
            width=24,
        )
        adapter.grid(row=0, column=1, sticky="w", padx=(0, 16))
        adapter.bind("<<ComboboxSelected>>", self._adapter_changed)

        ttk.Label(adapter_frame, text="Device name filter").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.filter_entry = ttk.Entry(adapter_frame, textvariable=self.filter_var, width=22)
        self.filter_entry.grid(row=0, column=3, sticky="ew", padx=(0, 16))
        ttk.Label(adapter_frame, text="ADB serial").grid(row=0, column=4, sticky="w", padx=(0, 8))
        self.serial_entry = ttk.Entry(adapter_frame, textvariable=self.serial_var, width=18)
        self.serial_entry.grid(row=0, column=5, sticky="ew", padx=(0, 16))
        self.discover_button = ttk.Button(adapter_frame, text="Discover BLE", command=self._discover)
        self.discover_button.grid(row=0, column=6, padx=(0, 14))
        self.device_combo = ttk.Combobox(adapter_frame, textvariable=self.device_var, state="readonly", width=34)
        self.device_combo.grid(row=0, column=7, sticky="ew")
        ttk.Label(adapter_frame, text="Optional TCP probe host").grid(row=1, column=0, sticky="w", pady=(9, 0), padx=(0, 8))
        ttk.Entry(adapter_frame, textvariable=self.probe_host_var, width=24).grid(row=1, column=1, sticky="ew", pady=(9, 0), padx=(0, 16))
        ttk.Label(adapter_frame, text="Port").grid(row=1, column=2, sticky="w", pady=(9, 0), padx=(0, 8))
        ttk.Entry(adapter_frame, textvariable=self.probe_port_var, width=8).grid(row=1, column=3, sticky="w", pady=(9, 0))
        adapter_frame.columnconfigure(3, weight=1)
        adapter_frame.columnconfigure(5, weight=1)
        adapter_frame.columnconfigure(7, weight=2)

        note = ttk.Label(
            outer,
            text="ADB mode is read-only. BLE scanning/GATT, Classic profiles, roaming, and RF scenarios may need Android instrumentation and lab fixtures.",
            style="Sub.TLabel",
            wraplength=1180,
        )
        note.pack(anchor="w", pady=(0, 10))

        panes = ttk.Panedwindow(outer, orient="vertical")
        panes.pack(fill="both", expand=True)
        catalog_frame = ttk.LabelFrame(panes, text="Test catalog", padding=10)
        result_frame = ttk.LabelFrame(panes, text="Run results", padding=10)
        panes.add(catalog_frame, weight=3)
        panes.add(result_frame, weight=2)

        toolbar = ttk.Frame(catalog_frame)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Filter").pack(side="left", padx=(0, 5))
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=26)
        search.pack(side="left", padx=(0, 10))
        search.bind("<KeyRelease>", lambda _event: self._render_catalog())
        self.domain_combo = ttk.Combobox(toolbar, textvariable=self.domain_var, values=("All", "Bluetooth", "Wi-Fi"), state="readonly", width=13)
        self.domain_combo.pack(side="left", padx=(0, 8))
        self.domain_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_categories())
        self.category_combo = ttk.Combobox(toolbar, textvariable=self.category_var, state="readonly", width=24)
        self.category_combo.pack(side="left", padx=(0, 12))
        self.category_combo.bind("<<ComboboxSelected>>", lambda _event: self._render_catalog())
        ttk.Button(toolbar, text="Quick smoke", command=lambda: self._apply_preset("Quick smoke")).pack(side="left", padx=3)
        ttk.Button(toolbar, text="BLE basics", command=lambda: self._apply_preset("BLE basics")).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Wi-Fi basics", command=lambda: self._apply_preset("Wi-Fi basics")).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Select visible", command=self._select_visible).pack(side="left", padx=(10, 3))
        ttk.Button(toolbar, text="Clear", command=self._clear_selection).pack(side="left", padx=3)

        columns = ("selected", "domain", "category", "title", "needs")
        self.catalog_tree = ttk.Treeview(catalog_frame, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("selected", "Run", 52),
            ("domain", "Type", 85),
            ("category", "Category", 155),
            ("title", "Scenario", 300),
            ("needs", "Requirements", 420),
        ):
            self.catalog_tree.heading(column, text=label)
            self.catalog_tree.column(column, width=width, minwidth=48, stretch=column in {"title", "needs"}, anchor="w")
        catalog_table = ttk.Frame(catalog_frame)
        catalog_table.pack(fill="both", expand=True)
        self.catalog_tree.grid(in_=catalog_table, row=0, column=0, sticky="nsew")
        catalog_y = ttk.Scrollbar(catalog_table, orient="vertical", command=self.catalog_tree.yview)
        catalog_y.grid(row=0, column=1, sticky="ns")
        catalog_x = ttk.Scrollbar(catalog_table, orient="horizontal", command=self.catalog_tree.xview)
        catalog_x.grid(row=1, column=0, sticky="ew")
        self.catalog_tree.configure(yscrollcommand=catalog_y.set, xscrollcommand=catalog_x.set)
        catalog_table.rowconfigure(0, weight=1)
        catalog_table.columnconfigure(0, weight=1)
        self.catalog_tree.bind("<Button-1>", self._toggle_catalog_row)

        bottom = ttk.Frame(catalog_frame)
        bottom.pack(fill="x", pady=(9, 0))
        self.catalog_count = ttk.Label(bottom, text="0 scenarios", style="Sub.TLabel")
        self.catalog_count.pack(side="left")
        self.run_selected_button = ttk.Button(bottom, text="Run selected (0)", style="Accent.TButton", command=self._run_selected)
        self.run_selected_button.pack(side="right", padx=(7, 0))
        self.run_all_button = ttk.Button(bottom, text="Run all scenarios", command=self._run_all)
        self.run_all_button.pack(side="right")

        results_toolbar = ttk.Frame(result_frame)
        results_toolbar.pack(fill="x", pady=(0, 7))
        ttk.Label(results_toolbar, textvariable=self.summary_var, style="Sub.TLabel").pack(side="left")
        ttk.Button(results_toolbar, text="Export JSON…", command=self._export_results).pack(side="right")
        result_columns = ("status", "scenario", "duration", "message")
        self.results_tree = ttk.Treeview(result_frame, columns=result_columns, show="headings")
        for column, label, width in (
            ("status", "Result", 90),
            ("scenario", "Scenario", 290),
            ("duration", "Time (ms)", 90),
            ("message", "Details", 620),
        ):
            self.results_tree.heading(column, text=label)
            self.results_tree.column(column, width=width, minwidth=55, stretch=column in {"scenario", "message"}, anchor="w")
        self.results_tree.tag_configure("passed", foreground="#18734b")
        self.results_tree.tag_configure("failed", foreground="#b3362d")
        self.results_tree.tag_configure("skipped", foreground="#946719")
        result_table = ttk.Frame(result_frame)
        result_table.pack(fill="both", expand=True)
        self.results_tree.grid(in_=result_table, row=0, column=0, sticky="nsew")
        result_y = ttk.Scrollbar(result_table, orient="vertical", command=self.results_tree.yview)
        result_y.grid(row=0, column=1, sticky="ns")
        result_x = ttk.Scrollbar(result_table, orient="horizontal", command=self.results_tree.xview)
        result_x.grid(row=1, column=0, sticky="ew")
        self.results_tree.configure(yscrollcommand=result_y.set, xscrollcommand=result_x.set)
        result_table.rowconfigure(0, weight=1)
        result_table.columnconfigure(0, weight=1)
        ttk.Label(outer, textvariable=self.status_var, style="Sub.TLabel").pack(fill="x", pady=(9, 0), anchor="w")

    def _adapter_changed(self, _event: tk.Event | None = None) -> None:
        kind = self.adapter_var.get()
        is_android = kind == "Android phone via ADB"
        is_host = kind == "Host BLE device"
        self.serial_entry.configure(state="normal" if is_android else "disabled")
        self.filter_entry.configure(state="normal" if is_host else "disabled")
        self.discover_button.configure(state="disabled" if is_android else "normal")
        self.device_combo.configure(state="readonly" if self._devices and is_host else "disabled")
        self.status_var.set(
            "Android ADB mode reads supported phone network/radio status; it does not toggle settings."
            if is_android
            else "Choose an adapter and select a test preset to begin."
        )

    def _new_adapter(self) -> Any:
        kind = self.adapter_var.get()
        if kind == "Host BLE device":
            return BleakWearableAdapter(self.filter_var.get().strip() or None)
        if kind == "Android phone via ADB":
            return AndroidAdbAdapter(self.serial_var.get().strip() or None)
        return FakeWearableAdapter()

    def _discover(self) -> None:
        if self._busy:
            return
        adapter = self._new_adapter()
        self._set_busy(True, "Scanning for Bluetooth devices…")

        def work() -> None:
            try:
                devices = adapter.discover()
                self._queue.put(("devices", devices))
            except Exception as error:
                self._queue.put(("error", str(error)))

        threading.Thread(target=work, daemon=True, name="connectivity-discovery").start()

    def _render_catalog(self) -> None:
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        query = self.search_var.get().strip().lower()
        domain = self.domain_var.get()
        category = self.category_var.get()
        visible = 0
        for case in self._cases:
            if domain != "All" and case.domain != domain:
                continue
            if category != "All categories" and case.category != category:
                continue
            title = case.title or case.name.replace("_", " ").title()
            haystack = f"{case.name} {title} {case.description} {case.requirement} {case.category}".lower()
            if query and query not in haystack:
                continue
            selected = case.name in self._selected
            self.catalog_tree.insert(
                "",
                "end",
                iid=case.name,
                values=("☑" if selected else "☐", case.domain, case.category, title, case.requirement),
            )
            visible += 1
        self.catalog_count.configure(text=f"{visible} shown · {len(self._selected)} selected · {len(self._cases)} total")
        self.run_selected_button.configure(text=f"Run selected ({len(self._selected)})", state="disabled" if self._busy or not self._selected else "normal")
        self.run_all_button.configure(state="disabled" if self._busy else "normal")

    def _update_categories(self) -> None:
        domain = self.domain_var.get()
        categories = sorted({case.category for case in self._cases if domain == "All" or case.domain == domain})
        self.category_combo.configure(values=("All categories", *categories))
        if self.category_var.get() not in {"All categories", *categories}:
            self.category_var.set("All categories")
        self._render_catalog()

    def _toggle_catalog_row(self, event: tk.Event) -> str | None:
        row = self.catalog_tree.identify_row(event.y)
        if not row:
            return None
        if self.catalog_tree.identify_column(event.x) == "#1":
            if row in self._selected:
                self._selected.remove(row)
            else:
                self._selected.add(row)
            self._render_catalog()
            return "break"
        return None

    def _apply_preset(self, name: str) -> None:
        self._selected = {case_id for case_id in PRESETS[name] if case_id in self._case_by_id}
        self._render_catalog()
        self.status_var.set(f"{name} preset selected {len(self._selected)} scenarios.")

    def _select_visible(self) -> None:
        self._selected.update(self.catalog_tree.get_children())
        self._render_catalog()

    def _clear_selection(self) -> None:
        self._selected.clear()
        self._render_catalog()

    def _run_selected(self) -> None:
        if self._selected:
            self._run_cases(sorted(self._selected))

    def _run_all(self) -> None:
        if len(self._cases) > 80 and not messagebox.askyesno(
            "Run full scenario catalog?",
            f"This runs {len(self._cases)} scenarios. Many need Android instrumentation or lab fixtures and will be skipped. Continue?",
            parent=self.root,
        ):
            return
        self._run_cases([case.name for case in self._cases])

    def _run_cases(self, ids: list[str]) -> None:
        if self._busy:
            return
        adapter_kind = self.adapter_var.get()
        adapter = self._new_adapter()
        probe_host = self.probe_host_var.get().strip()
        try:
            probe_port = int(self.probe_port_var.get().strip() or "443")
        except ValueError:
            messagebox.showerror("Invalid port", "The probe port must be a number.", parent=self.root)
            return
        cases = bluetooth_cases(adapter) + wifi_cases(adapter, probe_host or None, probe_port)
        selected_cases = [case for case in cases if case.name in set(ids)]
        selected_address = self._devices.get(self.device_var.get())
        self._set_busy(True, f"Running {len(selected_cases)} scenarios…")

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        def work() -> None:
            try:
                if adapter_kind == "Host BLE device" and selected_address:
                    adapter.connect_bluetooth(selected_address)
                results = TestRunner(selected_cases).run()
                self._queue.put(("results", results))
            except Exception as error:
                self._queue.put(("error", str(error)))

        threading.Thread(target=work, daemon=True, name="connectivity-test-run").start()

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.status_var.set(message)
        self.discover_button.configure(state="disabled" if busy or self.adapter_var.get() == "Android phone via ADB" else "normal")
        self._render_catalog()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "devices":
                    self._devices = {f"{device.name} · {device.address}": device.address for device in payload}
                    names = list(self._devices)
                    self.device_combo.configure(values=names, state="readonly" if names and self.adapter_var.get() == "Host BLE device" else "disabled")
                    if names:
                        self.device_var.set(names[0])
                        self.status_var.set(f"Found {len(names)} Bluetooth device(s). Choose one or run selected cases.")
                    else:
                        self.device_var.set("")
                        self.status_var.set("No Bluetooth devices found.")
                    self._set_busy(False, self.status_var.get())
                elif kind == "results":
                    self._show_results(payload)
                    self._set_busy(False, f"Finished {len(payload)} scenarios.")
                elif kind == "error":
                    self._set_busy(False, "Operation failed. See details below.")
                    messagebox.showerror("Connectivity test error", str(payload), parent=self.root)
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self._poll_queue)

    def _show_results(self, results: list[TestCaseResult]) -> None:
        counts = {"passed": 0, "failed": 0, "skipped": 0}
        self._last_results = []
        for result in results:
            status = result.status.value
            counts[status] = counts.get(status, 0) + 1
            case = self._case_by_id.get(result.name)
            title = (case.title or case.name) if case else result.name
            self.results_tree.insert(
                "",
                "end",
                values=(status.upper(), title, f"{result.duration_ms:.1f}", result.message),
                tags=(status,),
            )
            self._last_results.append(
                {
                    "name": result.name,
                    "title": title,
                    "domain": case.domain if case else "",
                    "category": case.category if case else "",
                    "status": status,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                    "details": result.details,
                }
            )
        self.summary_var.set(
            f"{len(results)} total    {counts['passed']} passed    {counts['failed']} failed    {counts['skipped']} skipped"
        )

    def _export_results(self) -> None:
        if not self._last_results:
            messagebox.showinfo("No results", "Run some scenarios before exporting.", parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export connectivity results",
            defaultextension=".json",
            filetypes=(("JSON report", "*.json"), ("All files", "*.*")),
            initialfile="connectivity-test-results.json",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as report:
                json.dump(self._last_results, report, indent=2)
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self.root)
            return
        self.status_var.set(f"Results saved to {path}")

    def _on_close(self) -> None:
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ConnectivityDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
