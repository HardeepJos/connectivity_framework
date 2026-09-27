# Meta Wearables Connectivity Test Run Guide

## 1. Open project folder

```bash
cd "/d/128 GB/hardeep/delete/Connectivity"
```

## 2. Activate virtual environment

```bash
source .venv/Scripts/activate
```

## 3. Run a single test case

```bash
pytest tests/test_framework.py::test_all_fake_connectivity_cases_pass_except_unconfigured_probe -q
```

Other single-test commands:

```bash
pytest tests/test_framework.py::test_version_matrix_contains_classic_ble_and_wifi_profiles -q
pytest tests/test_framework.py::test_bluetooth_failure_is_reported -q
pytest tests/test_framework.py::test_wifi_failure_is_reported -q
pytest tests/test_framework.py::test_unsupported_hardware_operation_is_skipped -q
```

## 4. Run all tests in the file

```bash
pytest tests/test_framework.py -q
```

## 5. Run the complete project test suite

```bash
pytest -q
```

## 6. Run the UI

```bash
python -m meta_wearables.web
```

Then open:

```text
http://127.0.0.1:8765
```

## 7. Useful notes

- This project uses pytest function names as test selectors.
- If a dependency is missing, install with:

```bash
python -m pip install -e ".[test]"
```

- For real Bluetooth support, install the optional Bluetooth package:

```bash
python -m pip install -e ".[bluetooth]"
```

## 8. Quick summary

Use single-test commands when debugging one scenario. Use the full file or full project command when validating the whole framework.
