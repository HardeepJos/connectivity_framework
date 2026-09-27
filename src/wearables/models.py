from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DeviceInfo:
    name: str
    address: str
    rssi: int | None = None
    transport: str = "bluetooth"
    bluetooth_version: str | None = None
    paired: bool = False
    profile: str | None = None
    signal_ok: bool | None = None
    bluetooth_features: tuple[str, ...] | None = None
    capabilities: dict[str, bool | None] | None = None


@dataclass(frozen=True)
class TestCaseResult:
    name: str
    status: TestStatus
    message: str = ""
    duration_ms: float = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WifiInfo:
    ssid: str
    connected: bool
    ip_address: str | None = None
    standard: str | None = None
    band_ghz: float | None = None
    security: str | None = None
    gateway: str | None = None
    dns_server: str | None = None
    hidden_ssid: bool = False
    signal_strength_dbm: int | None = None
    dhcp_ok: bool = True
    dns_ok: bool = True
    roaming: bool = False
    internet_reachable: bool | None = None
    password_valid: bool | None = None
    bssid: str | None = None
    frequency_mhz: int | None = None
    link_speed_mbps: int | None = None
    ipv6_addresses: tuple[str, ...] = ()
    capabilities: dict[str, bool | None] | None = None