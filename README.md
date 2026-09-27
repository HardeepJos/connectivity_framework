# Meta Wearables Connectivity Framework

Small Python/pytest framework for exercising Bluetooth and Wi-Fi connectivity around a Meta wearable. The test logic is hardware-neutral; a device integration implements `WearableAdapter`, while the included fake adapter makes the suite deterministic in CI.

## Quick start

```powershell
py -m pip install -e ".[test]"
py -m pytest
py -m meta_wearables.cli
py -m meta_wearables.cli --probe-host 192.168.1.1 --probe-port 443 --json
py -m meta_wearables.web
```

On Windows, you can also double-click `launch_ui.bat`. Keep that terminal window open while using the UI, then open `http://127.0.0.1:8765`.

Then open `http://127.0.0.1:8765`. Select **Real Bluetooth device** to scan using `bleak`; install it with `py -m pip install -e ".[bluetooth]"`. The UI can discover and connect to a BLE-visible wearable. Wi-Fi checks are shown as skipped when the selected adapter cannot expose that signal.

The suite currently covers:

- Bluetooth discovery
- Bluetooth connect and reconnect
- Bluetooth Classic profiles: 1.0, 1.1, 1.2, 2.0+EDR, 2.1+EDR, 3.0+HS, 4.0, 4.1, 4.2, 5.0, 5.1, 5.2, 5.3, and 5.4
- Bluetooth Low Energy profiles: 4.0, 4.1, 4.2, 5.0, 5.1, 5.2, 5.3, and 5.4
- Wi-Fi association state and IP address
- Wi-Fi 802.11a/b/g/n/ac/ax/be profiles
- Wi-Fi gateway and DNS configuration
- Optional TCP reachability probe from the connected network
- Wi-Fi reconnect
- Structured results with pass/fail/skip status, timing, and details

## Adding real hardware

Implement `WearableAdapter` in `src/meta_wearables/adapters.py` using the transport APIs available in the lab. The optional `bleak` dependency can support BLE discovery, but Meta wearable pairing, media commands, and Wi-Fi provisioning may require the Meta companion app or an approved device-facing API. Those operations should be implemented in the adapter rather than guessed by the test cases.

The fake adapter is intentionally separate from the real adapter so CI tests do not need Bluetooth hardware or a live Wi-Fi network.