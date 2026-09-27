from __future__ import annotations

import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .adapters import BleakWearableAdapter, FakeWearableAdapter
from .cases import bluetooth_cases, wifi_cases
from .runner import TestRunner


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meta Wearables Connectivity</title><style>
:root{font-family:Segoe UI,sans-serif;color:#17212b;background:#eef2f1}body{max-width:920px;margin:0 auto;padding:40px 20px}
h1{font-size:clamp(28px,5vw,48px);margin:0 0 8px}p{color:#5b6870}.panel{background:#fff;border:1px solid #d5dedb;border-radius:8px;padding:20px;margin-top:24px;box-shadow:0 8px 24px #20352a12}
label{display:block;font-size:13px;font-weight:700;margin-bottom:6px}select,input,button{font:inherit;padding:10px 12px;border:1px solid #bcc9c5;border-radius:6px}button{cursor:pointer;background:#1c6b59;color:#fff;border-color:#1c6b59;font-weight:700;margin-right:8px}button.secondary{background:#fff;color:#1c6b59}.actions{display:flex;gap:8px;flex-wrap:wrap}.device{padding:12px 0;border-bottom:1px solid #e5ebe8}.device:last-child{border-bottom:0}.status{font-weight:700}.passed{color:#18734b}.failed{color:#b3362d}.skipped{color:#8a641a}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style></head><body><h1>Meta wearable lab</h1><p>Discover a device, connect over Bluetooth, and run the available connectivity checks.</p>
<section class="panel"><div class="grid"><div><label for="adapter">Adapter</label><select id="adapter"><option value="fake">Fake device</option><option value="real">Real Bluetooth device</option></select></div><div><label for="filter">Name filter (optional)</label><input id="filter" placeholder="Ray-Ban Meta"></div></div><div class="actions" style="margin-top:18px"><button onclick="discover()">Discover devices</button><button class="secondary" onclick="runTests()">Run checks</button></div><div id="devices"><p>No scan performed.</p></div></section>
<section class="panel"><h2>Results</h2><div id="results"><p>Results will appear here.</p></div></section>
<script>
let selected=null;const el=id=>document.getElementById(id);
async function discover(){const q=new URLSearchParams({adapter:el('adapter').value,filter:el('filter').value});const r=await fetch('/api/discover?'+q);const d=await r.json();selected=d.devices[0]?.address||null;el('devices').innerHTML=d.devices.length?d.devices.map(x=>`<div class="device"><b>${x.name}</b><br>${x.address} ${x.rssi??''} dBm</div>`).join(''):`<p>${d.error||'No devices found.'}</p>`;}
async function runTests(){const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({adapter:el('adapter').value,filter:el('filter').value,address:selected})});const d=await r.json();el('results').innerHTML=d.results?d.results.map(x=>`<div class="device"><span class="status ${x.status}">${x.status.toUpperCase()}</span> &nbsp; ${x.name}<br><small>${x.message}</small></div>`).join(''):`<p>${d.error}</p>`;}
</script></body></html>"""


def _adapter(kind: str, name_filter: str | None):
    return FakeWearableAdapter() if kind == "fake" else BleakWearableAdapter(name_filter)


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, content_type: str = "text/html") -> None:
        encoded = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(PAGE)
            return
        if parsed.path == "/api/discover":
            values = parse_qs(parsed.query)
            try:
                devices = _adapter(values.get("adapter", ["fake"])[0], values.get("filter", [None])[0]).discover()
                self._send(json.dumps({"devices": [device.__dict__ for device in devices]}), "application/json")
            except Exception as error:
                self._send(json.dumps({"devices": [], "error": str(error)}), "application/json")
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self.send_error(404)
            return
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        adapter = _adapter(payload.get("adapter", "fake"), payload.get("filter"))
        try:
            if payload.get("address"):
                adapter.connect_bluetooth(payload["address"])
            results = TestRunner(bluetooth_cases(adapter) + wifi_cases(adapter)).run()
            self._send(json.dumps({"results": [result.__dict__ for result in results]}, default=str), "application/json")
        except Exception as error:
            self._send(json.dumps({"error": str(error)}), "application/json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Meta wearable connectivity UI")
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
    server.serve_forever()


if __name__ == "__main__":
    main()