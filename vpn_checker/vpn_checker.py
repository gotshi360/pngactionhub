import anchorpoint as ap
import apsync
import time
import threading
import requests

ui = ap.UI()

def is_vpn_connected(test_url):
    try:
        response = requests.get(test_url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def run_vpn_checker(interval, test_url):
    print(f"[VPN Checker] Started with interval: {interval} seconds")
    was_connected_once = False
    printed_disconnected = False
    notified_disconnected = False

    while True:
        local_settings = apsync.Settings("vpn_checker_local")
        notification_mode = local_settings.get("notification_mode", "Turn on notification")

        connected = is_vpn_connected(test_url)

        if connected and not was_connected_once:
            msg = "VPN is CONNECTED ✅"
            if notification_mode != "Turn off notification":
                ui.show_info(msg, duration=10000)
            print(f"[VPN Checker] Status changed: {msg}")
            was_connected_once = True
            printed_disconnected = False
            notified_disconnected = False

        elif not connected:
            msg = "VPN is DISCONNECTED ❌"
            description = (
                "Please reconnect or <a href='https://playngo.sharepoint.com/:b:/s/OnePlaynGO/EWoYO4KXq3dCjgAVR3wqu7MBXBiQK_vN6bR6T5c7B-CPCg?e=ESxako'>setup VPN</a>.<br>"
                "Change notification settings in the context menu."
            )

            should_notify = (
                notification_mode == "Turn on notification"
                or (notification_mode == "Show only once" and not notified_disconnected)
            )

            if should_notify:
                ui.show_info(msg, description=description, duration=20000)
                notified_disconnected = True

            if not printed_disconnected:
                print(f"[VPN Checker] Status changed: {msg}")
                printed_disconnected = True

            was_connected_once = False

        time.sleep(interval)

def start_checker():
    settings = apsync.Settings("vpn_checker")
    interval = int(settings.get("interval", 15))
    test_url = settings.get("vpn_url", "https://gitea.playngo.com").strip()

    print(f"[VPN Checker] Using interval: {interval} seconds")
    print(f"[VPN Checker] Testing access to: {test_url}")

    thread = threading.Thread(target=run_vpn_checker, args=(interval, test_url), daemon=True)
    thread.start()

def on_application_started(ctx: ap.Context):
    print("[VPN Checker] Triggered on application start")
    start_checker()
