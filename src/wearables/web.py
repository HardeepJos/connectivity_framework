from __future__ import annotations

import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .adapters import BleakWearableAdapter, FakeWearableAdapter
from .android_adb import AndroidAdbAdapter
from .cases import ConnectivityTestCase, bluetooth_cases, wifi_cases
from .runner import TestRunner
from .ui import PAGE


def _adapter(kind: str, name_filter: str | None, serial: str | None = None):
    if kind == "fake":
        return FakeWearableAdapter()
    if kind == "real":
        return BleakWearableAdapter(name_filter)
    if kind == "android":
        return AndroidAdbAdapter(serial)
    raise ValueError(f"Unknown adapter {kind!r}")


def _cases(adapter, probe_host: str | None = None, probe_port: int = 443) -> list[ConnectivityTestCase]:
    return bluetooth_cases(adapter) + wifi_cases(adapter, probe_host, probe_port)


def _case_payload(case: ConnectivityTestCase) -> dict[str, str]:
    return {
        "id": case.name,
        "name": case.name,
        "domain": case.domain,
        "category": case.category,
        "title": case.title or case.name.replace("_", " ").title(),
        "description": case.description or "Adapter-based connectivity validation.",
        "requirement": case.requirement or "Adapter-reported device evidence",
        "mode": case.mode,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ConnectivityLab/1.0"

    def _send(self, body: str, content_type: str = "text/html", status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def _json(self, payload: object, status: int = 200) -> None:
        self._send(json.dumps(payload, default=str), "application/json", status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(PAGE)
            return
        if parsed.path == "/api/catalog":
            adapter = FakeWearableAdapter()
            cases = _cases(adapter)
            scenarios = [_case_payload(case) for case in cases]
            self._json(
                {
                    "scenarios": scenarios,
                    "counts": {
                        "total": len(scenarios),
                        "bluetooth": sum(item["domain"] == "Bluetooth" for item in scenarios),
                        "wifi": sum(item["domain"] == "Wi-Fi" for item in scenarios),
                    },
                }
            )
            return
        if parsed.path == "/api/discover":
            values = parse_qs(parsed.query)
            kind = values.get("adapter", ["fake"])[0]
            try:
                adapter = _adapter(kind, values.get("filter", [None])[0], values.get("serial", [None])[0])
                devices = adapter.discover()
                self._json({"devices": [device.__dict__ for device in devices]})
            except Exception as error:
                self._json({"devices": [], "error": str(error)})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0 or content_length > 65536:
                self._json({"error": "Request body must be under 64 KB"}, 413)
                return
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")
            adapter = _adapter(payload.get("adapter", "fake"), payload.get("filter"), payload.get("serial"))
            if payload.get("address") and payload.get("adapter") == "real":
                adapter.connect_bluetooth(payload["address"])
            cases = _cases(adapter, payload.get("probe_host"), int(payload.get("probe_port", 443)))
            requested = payload.get("case_ids")
            if requested is not None:
                if not isinstance(requested, list) or any(not isinstance(name, str) for name in requested):
                    raise ValueError("case_ids must be a list of scenario IDs")
                requested_set = set(requested)
                cases = [case for case in cases if case.name in requested_set]
                unknown = requested_set - {case.name for case in cases}
                if unknown:
                    raise ValueError(f"Unknown scenario IDs: {', '.join(sorted(unknown))}")
            results = TestRunner(cases).run()
            metadata = {case.name: _case_payload(case) for case in cases}
            self._json(
                {
                    "results": [
                        {
                            **metadata[result.name],
                            "status": result.status.value,
                            "message": result.message,
                            "duration_ms": result.duration_ms,
                            "details": result.details,
                        }
                        for result in results
                    ]
                }
            )
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            self._json({"error": str(error)}, 400)
        except Exception as error:
            self._json({"error": str(error)}, 500)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Android Bluetooth/Wi-Fi connectivity test dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as error:
        raise SystemExit(f"Cannot start UI on {args.host}:{args.port}: {error}. Try --port 8766") from error
    url = f"http://{args.host}:{args.port}"
    print(f"Open {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping connectivity dashboard")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
