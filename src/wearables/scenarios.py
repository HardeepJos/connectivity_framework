"""Android-oriented Bluetooth and Wi-Fi scenario catalog.

A scenario is only marked passed/failed when the selected adapter supplies evidence.
The generic BLE adapter and Android public APIs cannot inspect every controller,
security, or RF capability; those scenarios are reported as skipped until a native
Android instrumentation adapter or suitable peer/test fixture is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    domain: str
    category: str
    title: str
    description: str
    requirement: str
    mode: str = "adapter"


_BLUETOOTH_SCENARIOS = [
    ("bluetooth_android_radio_enabled", "Android radio", "Bluetooth adapter is enabled", "ADB read-only status; Android device connected with USB debugging"),
    ("bluetooth_android_permissions", "Android permissions", "Bluetooth scan/connect permissions", "Android app instrumentation; Android 12+ Nearby devices permissions"),
    ("bluetooth_discovery", "Discovery", "BLE device discovery", "Bluetooth enabled; scan permission; advertiser in range"),
    ("bluetooth_discovery_filter", "Discovery", "Name/service UUID scan filtering", "Android BLE scanner instrumentation and advertising peer"),
    ("bluetooth_scan_response", "Discovery", "Scan response and advertising data", "Android BLE scanner instrumentation and advertising peer"),
    ("bluetooth_scan_duty_cycle", "Discovery", "Scan latency and duty-cycle behavior", "Timed Android instrumentation; controlled advertiser"),
    ("bluetooth_rssi", "Link quality", "RSSI sampling and threshold", "Connected/discoverable peer; calibrated range fixture for RF conclusions"),
    ("bluetooth_signal_quality", "Link quality", "Connection signal quality", "Connected BLE peer; RSSI available from adapter"),
    ("bluetooth_connect", "Connection", "Connect to selected BLE peer", "Advertiser/peripheral in range; user-approved pairing where required"),
    ("bluetooth_reconnect", "Connection", "Reconnect after link loss", "Paired BLE peripheral and controlled disconnect"),
    ("bluetooth_connection_drop", "Connection", "Unexpected disconnect detection", "Connected peer; Android connection callbacks/instrumentation"),
    ("bluetooth_pairing_auth", "Security", "Pairing and user authentication", "Pairing fixture; Android UI automation for confirmation prompts"),
    ("bluetooth_bond_persistence", "Security", "Bond persists across restart", "Paired fixture; reboot/relaunch automation"),
    ("bluetooth_bond_removal", "Security", "Unpair/bond removal behavior", "Dedicated test peer; destructive state change, run only on lab devices"),
    ("bluetooth_encryption", "Security", "Encrypted link and encryption state", "Android Bluetooth instrumentation or controller diagnostics"),
    ("bluetooth_secure_connections", "Security", "LE Secure Connections pairing", "LE Secure Connections peer; pairing instrumentation"),
    ("bluetooth_privacy", "Security", "Resolvable private address behavior", "Android controller instrumentation; privacy-enabled BLE peer"),
    ("bluetooth_gatt_service_discovery", "GATT", "GATT service discovery and UUID validation", "Connected GATT peripheral with known service database"),
    ("bluetooth_gatt_read", "GATT", "Characteristic read and value validation", "GATT test peripheral; readable characteristic"),
    ("bluetooth_gatt_write", "GATT", "Characteristic write and response validation", "GATT test peripheral; writable test characteristic"),
    ("bluetooth_gatt_notifications", "GATT", "Notification/indication subscription and delivery", "GATT test peripheral that emits known values"),
    ("bluetooth_gatt_reliable_write", "GATT", "Reliable/queued GATT write", "Peripheral supports reliable writes; instrumented GATT client"),
    ("bluetooth_mtu_negotiation", "GATT", "ATT MTU negotiation and payload boundary", "Android GATT instrumentation; peer supports MTU exchange"),
    ("bluetooth_gatt_operation_timeout", "GATT", "GATT timeout and cancellation behavior", "Instrumented GATT peer with controlled delayed response"),
    ("bluetooth_phy_1m", "LE PHY", "LE 1M PHY operation", "Android PHY callback and connected BLE peer"),
    ("bluetooth_phy_2m", "LE PHY", "LE 2M PHY negotiation", "Bluetooth 5+ controller and peer; Android PHY callback"),
    ("bluetooth_phy_coded", "LE PHY", "LE Coded PHY / long range", "Bluetooth 5+ coded-PHY hardware at controlled RF range"),
    ("bluetooth_connection_parameters", "LE link", "Connection interval/latency/supervision parameters", "Android controller diagnostics or instrumented peer"),
    ("bluetooth_data_length_extension", "LE link", "Data Length Extension", "Bluetooth 4.2+ peer and controller-level feature reporting"),
    ("bluetooth_connection_stability", "Reliability", "Sustained connection stability", "Timed run with connected peer; repeatable RF environment"),
    ("bluetooth_concurrent_connections", "Reliability", "Multiple simultaneous BLE connections", "Multiple peripherals; Android concurrency instrumentation"),
    ("bluetooth_background_scan", "Android behavior", "Background scan behavior and throttling", "Android app instrumentation; background execution and location/scan permissions"),
    ("bluetooth_process_recovery", "Android behavior", "Recovery after app/process recreation", "Android instrumentation; peer and process lifecycle control"),
    ("bluetooth_adapter_recovery", "Android behavior", "Recovery after adapter/radio state change", "Android instrumentation; toggles radio, disruptive to device"),
    ("bluetooth_extended_advertising", "Bluetooth 5.x/6.x", "Extended advertising", "Bluetooth 5+ controller and advertising peer"),
    ("bluetooth_periodic_advertising", "Bluetooth 5.x/6.x", "Periodic advertising and synchronization", "Bluetooth 5+ advertiser; Android periodic sync support"),
    ("bluetooth_direction_finding", "Bluetooth 5.x/6.x", "Direction finding (AoA/AoD) capability", "Bluetooth 5.1+ direction-finding hardware and antenna array"),
    ("bluetooth_periodic_sync_transfer", "Bluetooth 5.x/6.x", "Periodic advertising sync transfer", "Bluetooth 5.1+ controller and cooperating peer"),
    ("bluetooth_power_control", "Bluetooth 5.x/6.x", "LE power control and path-loss monitoring", "Bluetooth 5.2+ controllers at both ends"),
    ("bluetooth_isochronous_channels", "Bluetooth 5.x/6.x", "LE isochronous channels / LE Audio transport", "Bluetooth 5.2+ LE Audio controllers; compatible audio peers"),
    ("bluetooth_connection_subrating", "Bluetooth 5.x/6.x", "LE connection subrating", "Bluetooth 5.3+ controller and link-layer diagnostics"),
    ("bluetooth_pawr", "Bluetooth 5.x/6.x", "Periodic Advertising with Responses", "Bluetooth 5.4+ controller and PAwR test advertiser"),
    ("bluetooth_encrypted_advertising", "Bluetooth 5.x/6.x", "Encrypted advertising data handling", "Bluetooth 5.4+ controller and provisioned advertising keys"),
    ("bluetooth_channel_sounding", "Bluetooth 5.x/6.x", "Bluetooth 6.0 channel sounding", "Bluetooth 6.0-capable controller and sounding peer"),
    ("bluetooth_decision_based_filtering", "Bluetooth 5.x/6.x", "Bluetooth 6.0 decision-based advertising filtering", "Bluetooth 6.0 controller diagnostics and advertising fixture"),
    ("bluetooth_advertiser_monitoring", "Bluetooth 5.x/6.x", "Bluetooth 6.0 advertiser monitoring", "Bluetooth 6.0 controller diagnostics and advertiser fixture"),
    ("bluetooth_classic_a2dp", "Classic profiles", "A2DP audio streaming/interoperability", "Classic Bluetooth audio source/sink and Android profile instrumentation"),
    ("bluetooth_classic_hfp", "Classic profiles", "Hands-Free Profile call audio", "HFP peer; telephony/audio permissions and call fixture"),
    ("bluetooth_classic_avrcp", "Classic profiles", "AVRCP playback/control interoperability", "AVRCP controller/target peer and media session"),
    ("bluetooth_classic_hid", "Classic profiles", "HID input interoperability", "HID peer and Android input event verification"),
    ("bluetooth_classic_spp", "Classic profiles", "Serial Port Profile data exchange", "SPP peer; profile support (not available to every Android app)"),
    ("bluetooth_classic_pan", "Classic profiles", "PAN networking/tethering profile", "PAN-capable peer; privileged Android/system configuration"),
    ("bluetooth_profile_interoperability", "Classic profiles", "Profile interoperability and reconnect", "Each target profile plus known-good peer/test fixture"),
]

_WIFI_SCENARIOS = [
    ("wifi_android_permissions", "Android permissions", "Nearby Wi-Fi/location permissions", "Android app instrumentation; Android 13+ Nearby Wi-Fi and applicable location rules"),
    ("wifi_radio_enabled", "Radio and association", "Wi-Fi radio enabled state", "Android API/ADB status access"),
    ("wifi_connected", "Radio and association", "Association to expected SSID", "Connected Android device; SSID visibility permission where required"),
    ("wifi_bssid_access", "Radio and association", "BSSID access and privacy behavior", "Android location/nearby permissions; Android version/OEM policy varies"),
    ("wifi_hidden_ssid", "Radio and association", "Hidden SSID connection behavior", "Dedicated hidden-SSID AP and saved-network configuration"),
    ("wifi_saved_network_reconnect", "Radio and association", "Saved network auto-reconnect", "Previously provisioned test AP; controlled disconnect/reconnect"),
    ("wifi_reconnect", "Radio and association", "Reconnect after link loss", "Test AP; Android instrumentation; link interruption"),
    ("wifi_ip_configured", "IP and routing", "IPv4 address assignment", "Connected network; Android connectivity diagnostics"),
    ("wifi_ipv6_address", "IP and routing", "IPv6 address assignment", "IPv6-enabled test network"),
    ("wifi_gateway_configured", "IP and routing", "Default gateway and route", "Connected network; system diagnostics or privileged test app"),
    ("wifi_dhcp_lease", "IP and routing", "DHCP lease acquisition/renewal", "Controlled DHCP server; renewal requires instrumentation"),
    ("wifi_dhcp_timeout", "IP and routing", "DHCP timeout/failure recovery", "Isolated lab AP/DHCP server; disruptive network test"),
    ("wifi_dns_configured", "Name resolution", "DNS server configuration", "Connected network; Android system diagnostics"),
    ("wifi_dns_resolution", "Name resolution", "DNS lookup and failure handling", "Controlled DNS resolver/domain; network connectivity"),
    ("wifi_dns_failure", "Name resolution", "DNS outage recovery", "Isolated test resolver; do not run on production networks"),
    ("wifi_internet_reachability", "Internet and captive portal", "Internet reachability", "Internet access or approved probe endpoint"),
    ("wifi_network_probe", "Internet and captive portal", "TCP endpoint reachability and latency", "Configured allowed host/port; network egress permission"),
    ("wifi_captive_portal", "Internet and captive portal", "Captive portal detection/validation", "Captive portal test AP and Android connectivity callbacks"),
    ("wifi_signal_quality", "Radio performance", "RSSI threshold and signal sampling", "Connected AP; calibrated test positions for RF claims"),
    ("wifi_frequency_band", "Radio performance", "2.4/5/6 GHz association band", "AP with each band; Android frequency information access"),
    ("wifi_link_speed", "Radio performance", "Negotiated link speed", "AP/Android link-layer telemetry; traffic fixture for throughput"),
    ("wifi_channel_width", "Radio performance", "20/40/80/160/320 MHz channel width", "Configurable AP and Android chipset/driver reporting"),
    ("wifi_standard", "Radio performance", "802.11 mode (a/b/g/n/ac/ax/be)", "AP and handset support; mode telemetry (not inferred from band alone)"),
    ("wifi_throughput", "Radio performance", "Upload/download throughput", "Controlled local iperf endpoint; consented traffic generation"),
    ("wifi_packet_loss_latency", "Radio performance", "Latency, jitter, and packet loss", "Controlled local endpoint and repeatable RF conditions"),
    ("wifi_roaming_handoff", "Roaming", "Roaming between APs with same SSID", "Two or more coordinated APs; Android instrumentation and handoff logs"),
    ("wifi_roaming_authentication", "Roaming", "Roaming authentication continuity", "Enterprise/multi-AP lab (e.g. 802.1X) and test credentials"),
    ("wifi_wpa2", "Security", "WPA2-PSK association", "Dedicated WPA2 test AP and test credentials"),
    ("wifi_wpa3", "Security", "WPA3-SAE association", "WPA3-capable AP; compatible Android hardware/OS"),
    ("wifi_transition_mode", "Security", "WPA2/WPA3 transition-mode behavior", "Transition-mode test AP and Android compatibility matrix"),
    ("wifi_enterprise_8021x", "Security", "802.1X/EAP authentication", "Enterprise test RADIUS/AP and non-production credentials"),
    ("wifi_wrong_password", "Security", "Invalid credential rejection", "Isolated test AP; test-only credentials"),
    ("wifi_certificate_validation", "Security", "Enterprise server certificate validation", "Controlled RADIUS certificates; Android test profile"),
    ("wifi_randomized_mac", "Privacy and sharing", "Per-network randomized MAC behavior", "Android network details/system API; test AP association logs"),
    ("wifi_metered_network", "Privacy and sharing", "Metered network handling", "Android API and network policy instrumentation"),
    ("wifi_hotspot_state", "Hotspot and peer", "Soft AP/hotspot state and client connection", "Android tethering permission/system APIs; secondary client"),
    ("wifi_hotspot_security", "Hotspot and peer", "Hotspot security and client isolation", "Dedicated Android hotspot test; second client; avoid production networks"),
    ("wifi_direct", "Hotspot and peer", "Wi-Fi Direct discovery/group formation", "Android Wi-Fi P2P APIs and second Android device"),
    ("wifi_passpoint", "Hotspot and peer", "Passpoint/Hotspot 2.0 connection", "Passpoint provider/AP and provisioned test profile"),
    ("wifi_airplane_mode_recovery", "Android behavior", "Wi-Fi recovery after airplane-mode change", "Android instrumentation; disruptive radio state change"),
    ("wifi_background_restrictions", "Android behavior", "Background scan/restriction behavior", "Android app instrumentation; OS-version and battery-policy matrix"),
    ("wifi_process_recovery", "Android behavior", "Network callback recovery after process recreation", "Android instrumentation and controlled process lifecycle"),
]


def _build_specs() -> tuple[ScenarioSpec, ...]:
    specs: list[ScenarioSpec] = []
    for domain, rows in (("Bluetooth", _BLUETOOTH_SCENARIOS), ("Wi-Fi", _WIFI_SCENARIOS)):
        for scenario_id, category, title, requirement in rows:
            specs.append(
                ScenarioSpec(
                    id=scenario_id,
                    domain=domain,
                    category=category,
                    title=title,
                    description=f"Android {domain} validation: {title.lower()}.",
                    requirement=requirement,
                    mode="adapter" if "ADB" in requirement or "API access" in requirement else "instrumentation/fixture",
                )
            )
    return tuple(specs)


ANDROID_SCENARIOS = _build_specs()
SCENARIO_BY_ID = {scenario.id: scenario for scenario in ANDROID_SCENARIOS}
