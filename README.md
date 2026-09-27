# Android Bluetooth and Wi-Fi Connectivity Lab

Python connectivity test framework for Android-focused Bluetooth and Wi-Fi validation. It includes a deterministic fake adapter, a host BLE adapter backed by Bleak, a read-only Android ADB Wi-Fi/radio adapter, a browsable scenario catalog, and a local web dashboard.

## Setup

```bash
python -m pip install -e ".[test]"
```

Optional host BLE support:

```bash
python -m pip install -e ".[bluetooth]"
```

Run the automated regression tests:

```bash
python -m pytest -q
```

## Start the dashboard

```bash
python -m wearables.web
```

Open `http://127.0.0.1:8765`. On Windows, `launch_ui.bat` starts it. The dashboard supports search, Bluetooth/Wi-Fi filters, category filters, quick smoke/BLE/Wi-Fi presets, selected or full-suite runs, results summaries, remembered selections, and JSON export. Full-catalog runs ask for confirmation because many scenarios require Android instrumentation and lab fixtures.

## Start the Tkinter desktop app

```bash
python -m wearables.tk_ui
```

On Windows, run `launch_desktop.bat`. The desktop app provides adapter selection, device discovery, searchable/filterable scenarios, quick presets, async test execution, and JSON results export. Tkinter is included with most standard Python installers; if your Python installation reports that `tkinter` is missing, install a Python distribution that includes Tcl/Tk.

### Dashboard adapters

- **Demo / fake device** — deterministic framework/UI checks only; it does not exercise physical Android hardware.
- **Host BLE device (Bleak)** — scans and connects to BLE peripherals using the computer's Bluetooth adapter. Wi-Fi and many Android-specific tests are skipped if no adapter evidence exists.
- **Android phone via ADB** — reads Android Wi-Fi status and Bluetooth radio state without changing settings. Enable USB/wireless debugging, authorize this computer, and optionally provide the ADB serial if multiple devices are attached. BLE app-level scanning, pairing, GATT operations, and Classic profiles require an Android instrumentation companion; these are shown as skipped rather than simulated.

## Android test catalog

See [ANDROID_TEST_CATALOG.md](ANDROID_TEST_CATALOG.md) for the full scenario inventory and prerequisites. The dashboard also includes Bluetooth Classic/BLE version checks, BLE feature checks across versions 4.0–6.0, and Wi-Fi 802.11 a/b/g/n/ac/ax/be profile checks.

### Android access considerations

- Android 12+ uses runtime Nearby devices permissions for Bluetooth scanning/connecting; location and background execution behavior varies by Android release and OEM.
- Wi-Fi SSID/BSSID and scan details may be restricted by Android permissions, location settings, and OS/OEM policy.
- GATT, Classic profile, audio, hotspot, roaming, WPA-Enterprise, throughput, packet-loss, and RF-range tests need the corresponding peer/AP fixtures and often a native Android instrumentation app.
- The ADB adapter is intentionally read-only. Scenarios that toggle radios, change credentials, interrupt DHCP/DNS, remove bonds, or disrupt connectivity must be run only in an isolated lab through an explicitly instrumented adapter.

## CLI

```bash
wearable-test
wearable-test --probe-host 192.168.1.1 --probe-port 443 --json
```

The fake adapter is intentionally separate from device adapters so CI does not need Bluetooth hardware or a live Wi-Fi network.
