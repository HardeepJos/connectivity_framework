# Android Bluetooth and Wi-Fi Test Catalog

The dashboard is the executable catalog (`python -m wearables.web`). Its **All tests** filter includes these Android-oriented scenarios plus the Bluetooth Classic/BLE version checks, BLE feature checks, and 802.11 standards matrix.

## Reading results

- **Passed / failed:** the active adapter supplied a positive / negative observation for the check.
- **Skipped:** the adapter cannot observe that signal, a permission is missing, or a peer/AP/instrumentation fixture is required. A skip is not a pass.
- The fake adapter validates framework and UI behavior; it does not prove Android hardware behavior.
- The Android ADB adapter is read-only. It currently reads Wi-Fi and Bluetooth radio status where Android exposes them. Pairing, BLE scans/GATT, Classic profile tests, and RF tests require a native Android instrumentation companion and/or dedicated fixtures.

## Bluetooth

### Android system, discovery, connection, and permissions

| Scenario ID | Test |
|---|---|
| `bluetooth_android_radio_enabled` | Android Bluetooth adapter enabled state (ADB) |
| `bluetooth_android_permissions` | Bluetooth scan/connect runtime permission state |
| `bluetooth_discovery` | BLE device discovery |
| `bluetooth_discovery_filter` | Name/service UUID scan filtering |
| `bluetooth_scan_response` | Scan response and advertising data |
| `bluetooth_scan_duty_cycle` | Scan latency and duty cycle |
| `bluetooth_rssi` | RSSI sampling and threshold |
| `bluetooth_signal_quality` | Connection signal quality |
| `bluetooth_connect` | Connect to a selected BLE peer |
| `bluetooth_reconnect` | Reconnect after link loss |
| `bluetooth_connection_drop` | Unexpected disconnect detection |
| `bluetooth_bond_persistence` | Bond persistence across restart |
| `bluetooth_bond_removal` | Bond removal (destructive; lab device only) |
| `bluetooth_background_scan` | Android background scan/throttling behavior |
| `bluetooth_process_recovery` | Recovery after app process recreation |
| `bluetooth_adapter_recovery` | Recovery after radio state change (disruptive) |

### Pairing, security, GATT, and LE link

| Scenario ID | Test |
|---|---|
| `bluetooth_pairing_auth` | Pairing and user authentication |
| `bluetooth_encryption` | Encrypted link state |
| `bluetooth_secure_connections` | LE Secure Connections pairing |
| `bluetooth_privacy` | Resolvable private address behavior |
| `bluetooth_gatt_service_discovery` | GATT service discovery and UUID validation |
| `bluetooth_gatt_read` | Characteristic read/value validation |
| `bluetooth_gatt_write` | Characteristic write/response validation |
| `bluetooth_gatt_notifications` | Notification/indication subscription and delivery |
| `bluetooth_gatt_reliable_write` | Reliable/queued GATT write |
| `bluetooth_mtu_negotiation` | ATT MTU negotiation/payload boundary |
| `bluetooth_gatt_operation_timeout` | GATT timeout/cancellation behavior |
| `bluetooth_phy_1m` | LE 1M PHY operation |
| `bluetooth_phy_2m` | LE 2M PHY negotiation |
| `bluetooth_phy_coded` | LE Coded PHY / long range |
| `bluetooth_connection_parameters` | Connection interval/latency/supervision parameters |
| `bluetooth_data_length_extension` | Data Length Extension |
| `bluetooth_connection_stability` | Sustained connection stability |
| `bluetooth_concurrent_connections` | Multiple simultaneous BLE connections |

### Bluetooth 5.x/6.x capability scenarios

| Scenario ID | Test |
|---|---|
| `bluetooth_extended_advertising` | Extended advertising |
| `bluetooth_periodic_advertising` | Periodic advertising/synchronization |
| `bluetooth_direction_finding` | Direction finding (AoA/AoD) |
| `bluetooth_periodic_sync_transfer` | Periodic advertising sync transfer |
| `bluetooth_power_control` | LE power control/path-loss monitoring |
| `bluetooth_isochronous_channels` | LE isochronous channels / LE Audio transport |
| `bluetooth_connection_subrating` | LE connection subrating |
| `bluetooth_pawr` | Periodic Advertising with Responses |
| `bluetooth_encrypted_advertising` | Encrypted advertising data |
| `bluetooth_channel_sounding` | Bluetooth 6.0 channel sounding |
| `bluetooth_decision_based_filtering` | Bluetooth 6.0 decision-based advertising filtering |
| `bluetooth_advertiser_monitoring` | Bluetooth 6.0 advertiser monitoring |

The dashboard additionally creates one feature check for every item in `BLE_FEATURES_BY_VERSION` from Bluetooth 4.0 through 6.0, and version checks for Classic and BLE profiles. Controller feature support must be explicitly reported by an adapter; a version number alone does not prove a feature works.

### Bluetooth Classic profiles and interoperability

| Scenario ID | Test |
|---|---|
| `bluetooth_classic_a2dp` | A2DP audio streaming/interoperability |
| `bluetooth_classic_hfp` | Hands-Free Profile call audio |
| `bluetooth_classic_avrcp` | AVRCP media control |
| `bluetooth_classic_hid` | HID input interoperability |
| `bluetooth_classic_spp` | Serial Port Profile data exchange |
| `bluetooth_classic_pan` | PAN networking/tethering profile |
| `bluetooth_profile_interoperability` | Profile interoperability/reconnect |

## Wi-Fi

### Android permissions, association, and IP

| Scenario ID | Test |
|---|---|
| `wifi_android_permissions` | Nearby Wi-Fi/location permission behavior |
| `wifi_radio_enabled` | Wi-Fi radio enabled state |
| `wifi_connected` | Association to expected SSID |
| `wifi_bssid_access` | BSSID access/privacy behavior |
| `wifi_hidden_ssid` | Hidden SSID connection behavior |
| `wifi_saved_network_reconnect` | Saved network auto-reconnect |
| `wifi_reconnect` | Reconnect after link loss |
| `wifi_ip_configured` | IPv4 address assignment |
| `wifi_ipv6_address` | IPv6 address assignment |
| `wifi_gateway_configured` | Default gateway/route |
| `wifi_dhcp_lease` | DHCP lease acquisition/renewal |
| `wifi_dhcp_timeout` | DHCP timeout/failure recovery |
| `wifi_dns_configured` | DNS server configuration |
| `wifi_dns_resolution` | DNS lookup/failure handling |
| `wifi_dns_failure` | DNS outage recovery |

### Internet, RF, and roaming

| Scenario ID | Test |
|---|---|
| `wifi_internet_reachability` | Internet reachability |
| `wifi_network_probe` | TCP endpoint reachability/latency |
| `wifi_captive_portal` | Captive portal detection |
| `wifi_signal_quality` | RSSI sampling/threshold |
| `wifi_frequency_band` | 2.4/5/6 GHz association band |
| `wifi_link_speed` | Negotiated link speed |
| `wifi_channel_width` | Channel width (20–320 MHz where supported) |
| `wifi_standard` | 802.11 mode (a/b/g/n/ac/ax/be) |
| `wifi_throughput` | Upload/download throughput |
| `wifi_packet_loss_latency` | Latency, jitter, and packet loss |
| `wifi_roaming_handoff` | Roaming between coordinated APs |
| `wifi_roaming_authentication` | Roaming authentication continuity |

### Wi-Fi security, sharing, and Android behavior

| Scenario ID | Test |
|---|---|
| `wifi_wpa2` | WPA2-PSK association |
| `wifi_wpa3` | WPA3-SAE association |
| `wifi_transition_mode` | WPA2/WPA3 transition mode |
| `wifi_enterprise_8021x` | Enterprise 802.1X/EAP authentication |
| `wifi_wrong_password` | Invalid credential rejection |
| `wifi_certificate_validation` | Enterprise server certificate validation |
| `wifi_randomized_mac` | Per-network randomized MAC behavior |
| `wifi_metered_network` | Metered network policy behavior |
| `wifi_hotspot_state` | Android hotspot state/client connection |
| `wifi_hotspot_security` | Hotspot security/client isolation |
| `wifi_direct` | Wi-Fi Direct discovery/group formation |
| `wifi_passpoint` | Passpoint/Hotspot 2.0 connection |
| `wifi_airplane_mode_recovery` | Wi-Fi recovery after airplane-mode change |
| `wifi_background_restrictions` | Background scan/power restriction behavior |
| `wifi_process_recovery` | Network callback recovery after process recreation |

These scenarios require dedicated APs, a second device, a controlled DNS/RADIUS/throughput endpoint, or Android instrumentation when stated in the dashboard. Keep credentials and disruptive configuration tests confined to an isolated lab.

## Run the dashboard

```bash
python -m wearables.web
```

Open `http://127.0.0.1:8765`. Choose **Android phone via ADB** for read-only Android status checks; authorize USB debugging first. Choose **Host BLE device (Bleak)** to scan/connect to a BLE peripheral from the computer. The dashboard supports searching, domain/category filters, running selected cases, and exporting results as JSON.
