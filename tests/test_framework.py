from meta_wearables.adapters import FakeWearableAdapter, UnsupportedAdapterOperation
from meta_wearables.cases import BLE_FEATURES_BY_VERSION, BLE_VERSIONS, CLASSIC_VERSIONS, WIFI_STANDARDS, bluetooth_cases, wifi_cases
from meta_wearables.models import TestStatus as CaseStatus
from meta_wearables.runner import TestRunner as CaseRunner


def test_all_fake_connectivity_cases_pass_except_unconfigured_probe() -> None:
    adapter = FakeWearableAdapter()
    results = CaseRunner(bluetooth_cases(adapter) + wifi_cases(adapter)).run()
    by_name = {result.name: result for result in results}

    assert by_name["bluetooth_discovery"].status is CaseStatus.PASSED
    assert by_name["bluetooth_connect"].status is CaseStatus.PASSED
    assert by_name["bluetooth_reconnect"].status is CaseStatus.PASSED
    assert by_name["bluetooth_pairing_auth"].status is CaseStatus.PASSED
    assert by_name["bluetooth_signal_quality"].status is CaseStatus.PASSED
    assert by_name["bluetooth_connection_drop"].status is CaseStatus.PASSED
    assert by_name["bluetooth_ble_5.0"].status is CaseStatus.PASSED
    assert by_name["wifi_connected"].status is CaseStatus.PASSED
    assert by_name["wifi_ip_configured"].status is CaseStatus.PASSED
    assert by_name["wifi_gateway_configured"].status is CaseStatus.PASSED
    assert by_name["wifi_dns_configured"].status is CaseStatus.PASSED
    assert by_name["wifi_signal_quality"].status is CaseStatus.PASSED
    assert by_name["wifi_hidden_ssid"].status is CaseStatus.PASSED
    assert by_name["wifi_dhcp_timeout"].status is CaseStatus.PASSED
    assert by_name["wifi_dns_failure"].status is CaseStatus.PASSED
    assert by_name["wifi_roaming_handoff"].status is CaseStatus.PASSED
    assert by_name["wifi_password_issue"].status is CaseStatus.PASSED
    assert by_name["wifi_802.11ac"].status is CaseStatus.PASSED
    assert by_name["wifi_network_probe"].status is CaseStatus.SKIPPED


def test_version_matrix_contains_classic_ble_and_wifi_profiles() -> None:
    results = CaseRunner(bluetooth_cases(FakeWearableAdapter()) + wifi_cases(FakeWearableAdapter())).run()
    names = {result.name for result in results}

    assert {f"bluetooth_classic_{version}" for version in CLASSIC_VERSIONS} <= names
    assert {f"bluetooth_ble_{version}" for version in BLE_VERSIONS} <= names
    assert "6.0" in BLE_VERSIONS
    assert {f"wifi_{standard}" for standard in WIFI_STANDARDS} <= names


def test_ble_feature_matrix_covers_bluetooth_4_0_through_6_0() -> None:
    names = {case.name for case in bluetooth_cases(FakeWearableAdapter())}
    expected_features = {
        f"bluetooth_feature_{feature}"
        for features in BLE_FEATURES_BY_VERSION.values()
        for feature in features
    }

    assert set(BLE_FEATURES_BY_VERSION) == set(BLE_VERSIONS)
    assert expected_features <= names


def test_ble_feature_check_passes_and_fails_from_reported_capabilities() -> None:
    adapter = FakeWearableAdapter(
        bluetooth_version="5.0",
        bluetooth_features=("le_advertising", "gatt", "central_peripheral_roles", "le_connections", "le_2m_phy"),
    )
    results = CaseRunner(bluetooth_cases(adapter)).run()
    by_name = {result.name: result for result in results}

    assert by_name["bluetooth_feature_le_2m_phy"].status is CaseStatus.PASSED
    assert by_name["bluetooth_feature_extended_advertising"].status is CaseStatus.FAILED
    assert by_name["bluetooth_feature_channel_sounding"].status is CaseStatus.SKIPPED


def test_ble_feature_check_skips_when_adapter_does_not_report_capabilities() -> None:
    results = CaseRunner(bluetooth_cases(FakeWearableAdapter())).run()
    by_name = {result.name: result for result in results}

    assert by_name["bluetooth_feature_le_advertising"].status is CaseStatus.SKIPPED


def test_bluetooth_failure_is_reported() -> None:
    results = CaseRunner(bluetooth_cases(FakeWearableAdapter(bluetooth_available=False))).run()

    assert results[0].status is CaseStatus.FAILED
    assert results[1].status is CaseStatus.FAILED


def test_wifi_failure_is_reported() -> None:
    results = CaseRunner(wifi_cases(FakeWearableAdapter(wifi_available=False))).run()

    assert all(result.status is CaseStatus.FAILED for result in (results[0], results[2]))


def test_unsupported_hardware_operation_is_skipped() -> None:
    class Adapter(FakeWearableAdapter):
        def wifi_info(self):
            raise UnsupportedAdapterOperation("not exposed")

    results = CaseRunner(wifi_cases(Adapter())).run()

    assert results[0].status is CaseStatus.SKIPPED