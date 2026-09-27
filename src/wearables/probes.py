from __future__ import annotations

import socket
import time


def tcp_probe(host: str, port: int, timeout_seconds: float = 3) -> tuple[bool, float]:
    """Return reachability and elapsed milliseconds for a TCP endpoint."""
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, (time.perf_counter() - started) * 1000
    except OSError:
        return False, (time.perf_counter() - started) * 1000