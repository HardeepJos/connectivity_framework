from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from .models import DeviceInfo, WifiInfo


class UnsupportedAdapterOperation(RuntimeError):
    """Raised when a transport API cannot expose a requested device signal."""


class WearableAdapter(Protocol):
    """Hardware boundary implemented by a real Meta device integration."""

    def discover(self, timeout_seconds: float = 5) -> list[DeviceInfo]: ...

    def connect_bluetooth(self, address: str) -> None: ...

    def disconnect_bluetooth(self) -> None: ...

    def bluetooth_connected(self) -> bool: ...

    def bluetooth_info(self) -> DeviceInfo: ...

    def wifi_info(self) -> WifiInfo: ...

    def reconnect_wifi(self) -> None: ...


@dataclass
class FakeWearableAdapter:
    """Deterministic adapter used by tests and local framework development."""

    device_name: str = "Ray-Ban Meta (fake)"
    address: str = "FA:KE:00:00:00:01"
    bluetooth_available: bool = True
    wifi_available: bool = True
    wifi_ssid: str = "Meta-Test-Lab"
    wifi_ip: str = "192.168.1.50"
    wifi_standard: str = "802.11ac"
    wifi_band_ghz: float = 5.0
    wifi_security: str = "WPA2"
    wifi_gateway: str = "192.168.1.1"
    wifi_dns: str = "1.1.1.1"
    signal_strength_dbm: int = -42
    hidden_ssid: bool = False
    dhcp_ok: bool = True
    dns_ok: bool = True
    roaming: bool = False
    internet_reachable: bool | None = None
    password_valid: bool | None = True
    paired: bool = False
    device_transport: str = "ble"
    bluetooth_version: str = "5.0"
    bluetooth_features: tuple[str, ...] | None = None
    bluetooth_capabilities: dict[str, bool | None] | None = None
    wifi_capabilities: dict[str, bool | None] | None = None
    classic_supported: bool = False
    ble_supported: bool = True
    _bluetooth_connected: bool = False

    def discover(self, timeout_seconds: float = 5) -> list[DeviceInfo]:
        del timeout_seconds
        if not self.bluetooth_available:
            return []
        return [
            DeviceInfo(
                self.device_name,
                self.address,
                rssi=self.signal_strength_dbm,
                transport=self.device_transport,
                bluetooth_version=self.bluetooth_version,
                paired=self.paired,
                profile="classic" if self.device_transport == "classic" else "ble",
                signal_ok=self.signal_strength_dbm >= -70,
                bluetooth_features=self.bluetooth_features,
                capabilities=self.bluetooth_capabilities,
            )
        ]

    def connect_bluetooth(self, address: str) -> None:
        if address != self.address or not self.bluetooth_available:
            raise ConnectionError("wearable was not available over Bluetooth")
        if self.password_valid is False:
            raise ConnectionError("Bluetooth pairing authentication failed")
        self._bluetooth_connected = True
        self.paired = True

    def disconnect_bluetooth(self) -> None:
        self._bluetooth_connected = False

    def bluetooth_connected(self) -> bool:
        return self._bluetooth_connected

    def bluetooth_info(self) -> DeviceInfo:
        if not self._bluetooth_connected:
            raise ConnectionError("Bluetooth device is not connected")
        return DeviceInfo(
            self.device_name,
            self.address,
            rssi=self.signal_strength_dbm,
            transport=self.device_transport,
            bluetooth_version=self.bluetooth_version,
            paired=self.paired,
            profile="classic" if self.device_transport == "classic" else "ble",
            signal_ok=self.signal_strength_dbm >= -70,
            bluetooth_features=self.bluetooth_features,
            capabilities=self.bluetooth_capabilities,
        )

    def wifi_info(self) -> WifiInfo:
        return WifiInfo(
            self.wifi_ssid,
            self.wifi_available,
            self.wifi_ip if self.wifi_available else None,
            self.wifi_standard,
            self.wifi_band_ghz,
            self.wifi_security,
            self.wifi_gateway,
            self.wifi_dns,
            hidden_ssid=self.hidden_ssid,
            signal_strength_dbm=self.signal_strength_dbm,
            dhcp_ok=self.dhcp_ok,
            dns_ok=self.dns_ok,
            roaming=self.roaming,
            internet_reachable=self.internet_reachable,
            password_valid=self.password_valid,
            capabilities=self.wifi_capabilities,
        )

    def reconnect_wifi(self) -> None:
        if not self.wifi_available:
            raise ConnectionError("wearable Wi-Fi is unavailable")

    def capability_info(self, domain: str) -> dict[str, bool | None]:
        if domain.lower() == "bluetooth":
            return self.bluetooth_capabilities or {}
        if domain.lower() in {"wi-fi", "wifi"}:
            return self.wifi_capabilities or {}
        return {}


class BleakWearableAdapter:
    """Bluetooth adapter backed by the optional bleak package."""

    def __init__(self, name_filter: str | None = None) -> None:
        self.name_filter = name_filter.lower() if name_filter else None
        self._loop = asyncio.new_event_loop()
        self._client = None
        self._device: DeviceInfo | None = None

    def _run(self, coroutine):
        return self._loop.run_until_complete(coroutine)

    async def _discover(self, timeout_seconds: float) -> list[DeviceInfo]:
        try:
            from bleak import BleakScanner
        except ImportError as error:
            raise RuntimeError("Install Bluetooth support with: pip install -e \".[bluetooth]\"") from error
        discovered = await BleakScanner.discover(timeout=timeout_seconds)
        return [
            DeviceInfo(device.name or "Unknown BLE device", device.address, device.rssi)
            for device in discovered
            if not self.name_filter or self.name_filter in (device.name or "").lower()
        ]

    def discover(self, timeout_seconds: float = 5) -> list[DeviceInfo]:
        return self._run(self._discover(timeout_seconds))

    async def _connect(self, address: str) -> None:
        try:
            from bleak import BleakClient
        except ImportError as error:
            raise RuntimeError("Install Bluetooth support with: pip install -e \".[bluetooth]\"") from error
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = BleakClient(address)
        await self._client.connect()

    def connect_bluetooth(self, address: str) -> None:
        self._run(self._connect(address))
        self._device = DeviceInfo(self._device.name if self._device else "Meta wearable", address)

    def disconnect_bluetooth(self) -> None:
        if self._client:
            self._run(self._client.disconnect())

    def bluetooth_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    def bluetooth_info(self) -> DeviceInfo:
        if not self.bluetooth_connected():
            raise ConnectionError("Bluetooth device is not connected")
        return DeviceInfo(self._device.name if self._device else "Meta wearable", self._device.address if self._device else "unknown", transport="ble")

    def wifi_info(self) -> WifiInfo:
        raise UnsupportedAdapterOperation("Wi-Fi association state is not exposed by the generic BLE API")

    def reconnect_wifi(self) -> None:
        raise UnsupportedAdapterOperation("Wi-Fi reconnect requires a Meta-approved device API")