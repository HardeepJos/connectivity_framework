from __future__ import annotations

import argparse
import json

from .adapters import FakeWearableAdapter
from .cases import bluetooth_cases, wifi_cases
from .runner import TestRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Meta wearable connectivity checks")
    parser.add_argument("--probe-host", help="Optional host to test from the Wi-Fi network")
    parser.add_argument("--probe-port", type=int, default=443)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    results = TestRunner(bluetooth_cases(FakeWearableAdapter()) + wifi_cases(FakeWearableAdapter(), args.probe_host, args.probe_port)).run()
    if args.as_json:
        print(json.dumps([result.__dict__ for result in results], default=str, indent=2))
    else:
        for result in results:
            print(f"{result.status.value.upper():7} {result.name}: {result.message}")
    return int(any(result.status.value == "failed" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())