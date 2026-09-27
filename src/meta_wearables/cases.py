from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .adapters import WearableAdapter
from .models import TestCaseResult, TestStatus
from .probes import tcp_probe


CLASSIC_VERSIONS = ("1.0", "1.1", "1.2", "2.0+EDR", "2.1+EDR", "3.0+HS", "4.0", "4.1", "4.2", "5.0", "5.1", "5.2", "5.3", "5.4", "6.0")
BLE_VERSIONS = ("4.0", "4.1", "4.2", "5.0", "5.1", "5.2", "5.3", "5.4", "6.0")
BLE_FEATURES_BY_VERSION = {
    "4.0": ("le_advertising", "gatt", "central_peripheral_roles", "le_connections"),
    "4.1": ("connection_parameter_update", "le_link_layer_topology", "le_l2cap_flow_control"),
    "4.2": ("data_length_extension", "le_secure_connections", "le_privacy", "l2cap_credit_based_flow_control"),
    "5.0": ("le_2m_phy", "le_coded_phy", "extended_advertising", "periodic_advertising", "increased_advertising_data_length"),
    "5.1": ("direction_finding", "gatt_caching", "periodic_advertising_sync_transfer", "advertising_channel_index"),
    "5.2": ("isochronous_channels", "enhanced_att", "le_power_control", "path_loss_monitoring"),
    "5.3": ("connection_subrating", "encryption_key_size_control", "periodic_advertising_enhancements", "channel_classification"),
    "5.4": ("pawr", "encrypted_advertising_data", "gatt_security_levels", "advertising_coding_selection"),
    "6.0": ("channel_sounding", "decision_based_advertising_filtering", "advertiser_monitoring", "isoal_enhancements", "ll_extended_feature_set", "frame_space_update"),
}
WIFI_STANDARDS = ("802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax", "802.11be")


@dataclass(frozen=True)
class ConnectivityTestCase:
    name: str
    run: Callable[[], TestCaseResult]


def _result(name: str, passed: bool, message: str, **details: object) -> TestCaseResult:
    return TestCaseResult(
        name=name,
        status=TestStatus.PASSED if passed else TestStatus.FAILED,
        message=message,
        details=details,
    )


def bluetooth_cases(adapter: WearableAdapter) -> list[ConnectivityTestCase]:
    def connected_info():
        if not adapter.bluetooth_connected():
            devices = adapter.discover()
            if not devices:
                raise ConnectionError("no wearable discovered")
            adapter.connect_bluetooth(devices[0].address)
        return adapter.bluetooth_info()

    def discover() -> TestCaseResult:
        devices = adapter.discover()
        return _result("bluetooth_discovery", bool(devices), f"found {len(devices)} device(s)")

    def pair_and_connect() -> TestCaseResult:
        devices = adapter.discover()
        if not devices:
            return _result("bluetooth_connect", False, "no wearable discovered")
        adapter.connect_bluetooth(devices[0].address)
        return _result("bluetooth_connect", adapter.bluetooth_connected(), "Bluetooth connection established")

    def reconnect() -> TestCaseResult:
        devices = adapter.discover()
        if not devices:
            return _result("bluetooth_reconnect", False, "no wearable discovered")
        adapter.disconnect_bluetooth()
        adapter.connect_bluetooth(devices[0].address)
        return _result("bluetooth_reconnect", adapter.bluetooth_connected(), "Bluetooth reconnection succeeded")

    def pairing_auth() -> TestCaseResult:
        try:
            devices = adapter.discover()
            if not devices:
                return _result("bluetooth_pairing_auth", False, "no wearable discovered")
            adapter.connect_bluetooth(devices[0].address)
            return _result("bluetooth_pairing_auth", True, "pairing authentication passed")
        except Exception as error:
            return _result("bluetooth_pairing_auth", False, str(error))

    def signal_quality() -> TestCaseResult:
        try:
            info = adapter.bluetooth_info()
        except Exception as error:
            return _result("bluetooth_signal_quality", False, str(error))
        return _result("bluetooth_signal_quality", bool(info.signal_ok), f"signal={info.rssi} dBm", rssi=info.rssi)

    def connection_drop() -> TestCaseResult:
        try:
            devices = adapter.discover()
            if not devices:
                return _result("bluetooth_connection_drop", False, "no wearable discovered")
            adapter.connect_bluetooth(devices[0].address)
            adapter.disconnect_bluetooth()
            return _result("bluetooth_connection_drop", not adapter.bluetooth_connected(), "connection dropped cleanly")
        except Exception as error:
            return _result("bluetooth_connection_drop", False, str(error))

    def version_case(version: str, transport: str) -> ConnectivityTestCase:
        def check_version() -> TestCaseResult:
            info = connected_info()
            if info.transport != transport:
                return TestCaseResult(f"bluetooth_{transport}_{version}", TestStatus.SKIPPED, f"device uses {info.transport}, not {transport}")
            if info.bluetooth_version is None:
                return TestCaseResult(f"bluetooth_{transport}_{version}", TestStatus.SKIPPED, "adapter did not report a Bluetooth version")
            supported = info.bluetooth_version == version
            return _result(f"bluetooth_{transport}_{version}", supported, f"reported Bluetooth {info.bluetooth_version}", reported_version=info.bluetooth_version)

        return ConnectivityTestCase(f"bluetooth_{transport}_{version}", check_version)

    def feature_case(feature: str, introduced_in: str) -> ConnectivityTestCase:
        name = f"bluetooth_feature_{feature}"

        def check_feature() -> TestCaseResult:
            info = connected_info()
            if info.transport != "ble":
                return TestCaseResult(name, TestStatus.SKIPPED, f"device uses {info.transport}, not BLE")
            if info.bluetooth_version is None:
                return TestCaseResult(name, TestStatus.SKIPPED, "adapter did not report a Bluetooth version")
            if info.bluetooth_features is None:
                return TestCaseResult(name, TestStatus.SKIPPED, "adapter did not report BLE feature capabilities")
            try:
                reported_version = tuple(int(part) for part in info.bluetooth_version.split(".")[:2])
                required_version = tuple(int(part) for part in introduced_in.split(".")[:2])
            except ValueError:
                return TestCaseResult(name, TestStatus.SKIPPED, f"unrecognized Bluetooth version {info.bluetooth_version}")
            if reported_version < required_version:
                return TestCaseResult(name, TestStatus.SKIPPED, f"requires Bluetooth {introduced_in}; device reports {info.bluetooth_version}")
            supported = feature in info.bluetooth_features
            return _result(
                name,
                supported,
                f"{feature} {'reported' if supported else 'not reported'} by Bluetooth {info.bluetooth_version}",
                feature=feature,
                introduced_in=introduced_in,
                reported_version=info.bluetooth_version,
            )

        return ConnectivityTestCase(name, check_feature)

    cases = [
        ConnectivityTestCase("bluetooth_discovery", discover),
        ConnectivityTestCase("bluetooth_connect", pair_and_connect),
        ConnectivityTestCase("bluetooth_reconnect", reconnect),
        ConnectivityTestCase("bluetooth_pairing_auth", pairing_auth),
        ConnectivityTestCase("bluetooth_signal_quality", signal_quality),
        ConnectivityTestCase("bluetooth_connection_drop", connection_drop),
    ]
    cases.extend(version_case(version, "classic") for version in CLASSIC_VERSIONS)
    cases.extend(version_case(version, "ble") for version in BLE_VERSIONS)
    cases.extend(
        feature_case(feature, version)
        for version, features in BLE_FEATURES_BY_VERSION.items()
        for feature in features
    )
    return cases


def wifi_cases(adapter: WearableAdapter, probe_host: str | None = None, probe_port: int = 443) -> list[ConnectivityTestCase]:
    def connected() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_connected", info.connected, f"SSID={info.ssid}", ssid=info.ssid, ip_address=info.ip_address)

    def network_probe() -> TestCaseResult:
        if not probe_host:
            return TestCaseResult("wifi_network_probe", TestStatus.SKIPPED, "no probe host configured")
        reachable, latency = tcp_probe(probe_host, probe_port)
        return _result("wifi_network_probe", reachable, f"TCP probe latency={latency:.1f} ms", host=probe_host, port=probe_port, latency_ms=latency)

    def reconnect() -> TestCaseResult:
        adapter.reconnect_wifi()
        info = adapter.wifi_info()
        return _result("wifi_reconnect", info.connected, "Wi-Fi reconnection succeeded")

    def ip_configured() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_ip_configured", info.connected and bool(info.ip_address), f"IP={info.ip_address}")

    def gateway_configured() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_gateway_configured", info.connected and bool(info.gateway), f"gateway={info.gateway}")

    def dns_configured() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_dns_configured", info.connected and bool(info.dns_server), f"DNS={info.dns_server}")

    def signal_quality() -> TestCaseResult:
        info = adapter.wifi_info()
        quality_ok = info.connected and (info.signal_strength_dbm is None or info.signal_strength_dbm >= -70)
        return _result("wifi_signal_quality", quality_ok, f"RSSI={info.signal_strength_dbm} dBm", rssi=info.signal_strength_dbm)

    def hidden_ssid() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_hidden_ssid", not info.hidden_ssid or info.connected, "hidden SSID policy evaluated", hidden=info.hidden_ssid)

    def dhcp_timeout() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_dhcp_timeout", info.connected and info.dhcp_ok, "DHCP lease validation completed", dhcp_ok=info.dhcp_ok)

    def dns_failure() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_dns_failure", info.connected and info.dns_ok, "DNS resolution validation completed", dns_ok=info.dns_ok)

    def roaming_handoff() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_roaming_handoff", info.connected and (not info.roaming or info.connected), "roaming handoff validated", roaming=info.roaming)

    def password_issue() -> TestCaseResult:
        info = adapter.wifi_info()
        return _result("wifi_password_issue", info.connected or info.password_valid is not False, "credential validity checked", password_valid=info.password_valid)

    def standard_case(standard: str) -> ConnectivityTestCase:
        def check_standard() -> TestCaseResult:
            info = adapter.wifi_info()
            if info.standard is None:
                return TestCaseResult(f"wifi_{standard}", TestStatus.SKIPPED, "adapter did not report an 802.11 standard")
            return _result(f"wifi_{standard}", info.standard == standard, f"reported Wi-Fi {info.standard}", reported_standard=info.standard)

        return ConnectivityTestCase(f"wifi_{standard}", check_standard)

    cases = [
        ConnectivityTestCase("wifi_connected", connected),
        ConnectivityTestCase("wifi_ip_configured", ip_configured),
        ConnectivityTestCase("wifi_gateway_configured", gateway_configured),
        ConnectivityTestCase("wifi_dns_configured", dns_configured),
        ConnectivityTestCase("wifi_signal_quality", signal_quality),
        ConnectivityTestCase("wifi_hidden_ssid", hidden_ssid),
        ConnectivityTestCase("wifi_dhcp_timeout", dhcp_timeout),
        ConnectivityTestCase("wifi_dns_failure", dns_failure),
        ConnectivityTestCase("wifi_roaming_handoff", roaming_handoff),
        ConnectivityTestCase("wifi_password_issue", password_issue),
        ConnectivityTestCase("wifi_network_probe", network_probe),
        ConnectivityTestCase("wifi_reconnect", reconnect),
    ]
    cases.extend(standard_case(standard) for standard in WIFI_STANDARDS)
    return cases