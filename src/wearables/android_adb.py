from __future__ import annotations

import re
import shutil
import subprocess

from .adapters import UnsupportedAdapterOperation
from .models import DeviceInfo, WifiInfo


class AndroidAdbAdapter:
    """Read-only Android diagnostics over ADB.

    This adapter reads Android radio and Wi-Fi state without changing device
    settings. Bluetooth scanning/GATT operations require a companion Android
    instrumentation app and are intentionally reported as unsupported.
    """

    def __init__(self, serial: str | None = None, command_timeout_seconds: float = 10) -> None:
        self.serial = serial.strip() if serial and serial.strip() else None
        self.command_timeout_seconds = command_timeout_seconds
        self._resolved_serial: str | None = None
        self._wifi_info_cache: WifiInfo | None = None
        self._bluetooth_capabilities_cache: dict[str, bool | None] | None = None

    def _adb_prefix(self) -> list[str]:
        if shutil.which("adb") is None:
            raise UnsupportedAdapterOperation("ADB is not installed or is not on PATH")
        if self._resolved_serial:
            return ["adb", "-s", self._resolved_serial]

        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=self.command_timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise UnsupportedAdapterOperation(f"Could not query ADB devices: {error}") from error
        if result.returncode:
            raise UnsupportedAdapterOperation(result.stderr.strip() or "adb devices failed")

        connected: list[str] = []
        unauthorized = False
        for line in result.stdout.splitlines()[1:]:
            columns = line.split()
            if len(columns) >= 2 and columns[1] == "device":
                connected.append(columns[0])
            elif len(columns) >= 2 and columns[1] == "unauthorized":
                unauthorized = True
        if self.serial:
            if self.serial not in connected:
                detail = " (authorize USB debugging on the phone)" if unauthorized else ""
                raise UnsupportedAdapterOperation(f"ADB device {self.serial!r} is not connected{detail}")
            self._resolved_serial = self.serial
        elif len(connected) == 1:
            self._resolved_serial = connected[0]
        elif not connected:
            detail = "; authorize USB debugging on the phone" if unauthorized else ""
            raise UnsupportedAdapterOperation(f"No authorized Android device found over ADB{detail}")
        else:
            raise UnsupportedAdapterOperation("Multiple Android devices found; specify an ADB serial in the UI")
        return ["adb", "-s", self._resolved_serial]

    def _shell(self, *args: str) -> str:
        command = [*self._adb_prefix(), "shell", *args]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.command_timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise UnsupportedAdapterOperation(f"Android ADB command failed: {error}") from error
        if result.returncode:
            raise UnsupportedAdapterOperation(result.stderr.strip() or f"ADB command failed: {' '.join(args)}")
        return result.stdout.strip()

    def discover(self, timeout_seconds: float = 5) -> list[DeviceInfo]:
        del timeout_seconds
        raise UnsupportedAdapterOperation(
            "Android ADB does not expose app-level BLE scanning; use an Android instrumentation companion or the host BLE adapter"
        )

    def connect_bluetooth(self, address: str) -> None:
        del address
        raise UnsupportedAdapterOperation("Android ADB cannot initiate app-level Bluetooth pairing; use Android UI/instrumentation")

    def disconnect_bluetooth(self) -> None:
        raise UnsupportedAdapterOperation("Android ADB cannot disconnect a Bluetooth peer safely without app instrumentation")

    def bluetooth_connected(self) -> bool:
        raise UnsupportedAdapterOperation("Android peer connection state requires BluetoothManager instrumentation")

    def bluetooth_info(self) -> DeviceInfo:
        raise UnsupportedAdapterOperation("Android peer details require BluetoothManager instrumentation")

    def capability_info(self, domain: str) -> dict[str, bool | None]:
        if domain.lower() != "bluetooth":
            return {}
        if self._bluetooth_capabilities_cache is not None:
            return self._bluetooth_capabilities_cache
        radio_state = self._shell("settings", "get", "global", "bluetooth_on")
        enabled = radio_state == "1"
        self._bluetooth_capabilities_cache = {"bluetooth_android_radio_enabled": enabled}
        return self._bluetooth_capabilities_cache

    @staticmethod
    def _match(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
        found = re.search(pattern, text, flags)
        return found.group(1).strip().strip('"') if found else None

    def wifi_info(self) -> WifiInfo:
        if self._wifi_info_cache is not None:
            return self._wifi_info_cache
        self._adb_prefix()  # Resolve/check the target before issuing other commands.
        dump = self._shell("dumpsys", "wifi")
        radio_state = self._shell("settings", "get", "global", "wifi_on")
        route = self._shell("ip", "route", "show", "dev", "wlan0")
        interface = self._shell("ip", "-4", "addr", "show", "dev", "wlan0")
        dns_server = self._shell("getprop", "net.dns1")

        state_text = " ".join((dump, self._shell("dumpsys", "connectivity")))
        connected = bool(
            re.search(r"Supplicant state:\s*COMPLETED", dump, re.IGNORECASE)
            or re.search(r"state:\s*CONNECTED", dump, re.IGNORECASE)
            or re.search(r"NetworkAgentInfo.*WIFI.*CONNECTED", state_text, re.IGNORECASE)
        )
        ssid = self._match(r"SSID:\s*(\"[^\"]*\"|[^,;\s]+)", dump) or ""
        if ssid.lower() in {"<unknown ssid>", "unknown", "null"}:
            ssid = ""
        bssid = self._match(r"BSSID:\s*([0-9a-f:]{17})", dump)
        rssi_text = self._match(r"RSSI:\s*(-?\d+)", dump)
        frequency_text = self._match(r"Frequency:\s*(\d+)", dump)
        speed_text = self._match(r"Link speed:\s*(\d+)", dump)
        ip_address = self._match(r"inet\s+(\d{1,3}(?:\.\d{1,3}){3})/", interface)
        if not ip_address:
            ip_address = self._match(r"IP(?: address)?:\s*/?(\d{1,3}(?:\.\d{1,3}){3})", dump)
        gateway = self._match(r"default\s+via\s+(\d{1,3}(?:\.\d{1,3}){3})", route)
        standard_text = self._match(r"Wi-Fi standard:\s*(\S+)", dump)
        standard = None
        if standard_text:
            standard = standard_text if standard_text.startswith("802.11") else f"802.11{standard_text.removeprefix('11')}"
        rssi = int(rssi_text) if rssi_text else None
        frequency = int(frequency_text) if frequency_text else None
        link_speed = int(speed_text) if speed_text else None
        ipv6_text = self._shell("ip", "-6", "addr", "show", "dev", "wlan0")
        ipv6_addresses = tuple(re.findall(r"inet6\s+([0-9a-f:]+)/", ipv6_text, re.IGNORECASE))
        capabilities: dict[str, bool | None] = {
            "wifi_radio_enabled": radio_state == "1" if radio_state in {"0", "1"} else None,
            "wifi_bssid_access": bssid is not None,
            "wifi_frequency_band": frequency is not None,
            "wifi_link_speed": link_speed is not None,
            "wifi_standard": standard is not None,
            "wifi_ipv6_address": bool(ipv6_addresses) if connected else None,
            "wifi_gateway_configured": bool(gateway) if connected else None,
            "wifi_dns_configured": bool(dns_server) if connected else None,
            "wifi_ip_configured": bool(ip_address) if connected else None,
        }
        self._wifi_info_cache = WifiInfo(
            ssid=ssid,
            connected=connected,
            ip_address=ip_address,
            standard=standard,
            band_ghz=round(frequency / 1000, 1) if frequency else None,
            gateway=gateway,
            dns_server=dns_server or None,
            signal_strength_dbm=rssi,
            bssid=bssid,
            frequency_mhz=frequency,
            link_speed_mbps=link_speed,
            ipv6_addresses=ipv6_addresses,
            capabilities=capabilities,
        )
        return self._wifi_info_cache

    def reconnect_wifi(self) -> None:
        raise UnsupportedAdapterOperation("Wi-Fi reconnect changes Android network state; use a dedicated Android instrumentation test")
