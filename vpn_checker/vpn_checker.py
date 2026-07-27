import anchorpoint as ap
import apsync
import time
import requests

SETTINGS_NAME = "vpn_checker"
LOCAL_SETTINGS_NAME = "vpn_checker_local"

# on_timeout fires once a minute, which is the finest granularity available.
MIN_INTERVAL_SECS = 60.0
DEFAULT_INTERVAL_SECS = 60
DEFAULT_URL = "https://gitea.playngo.com"

VPN_HELP_URL = (
    "https://playngo.sharepoint.com/:b:/s/OnePlaynGO/"
    "EWoYO4KXq3dCjgAVR3wqu7MBXBiQK_vN6bR6T5c7B-CPCg?e=ESxako"
)

# Module level state, so it survives between on_timeout calls and is shared
# across workspaces. That keeps the check running once per interval no matter
# how many workspaces are open — the previous version started one endless
# thread per workspace in on_application_started.
_last_check_t = 0.0
_was_connected = False
_notified_disconnected = False
_logged_disconnected = False


def is_vpn_connected(test_url):
    try:
        response = requests.get(test_url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_vpn():
    """Runs on a worker thread via ctx.run_async so the blocking request never
    stalls the UI."""
    global _was_connected, _notified_disconnected, _logged_disconnected

    test_url = (apsync.Settings(SETTINGS_NAME).get("vpn_url", DEFAULT_URL) or DEFAULT_URL).strip()
    notification_mode = apsync.Settings(LOCAL_SETTINGS_NAME).get(
        "notification_mode", "Turn on notification"
    )

    ui = ap.UI()
    connected = is_vpn_connected(test_url)

    if connected:
        if not _was_connected:
            print("[VPN Checker] Status changed: VPN is CONNECTED")
            if notification_mode != "Turn off notification":
                ui.show_info("VPN is CONNECTED ✅", duration=10000)
        _was_connected = True
        _notified_disconnected = False
        _logged_disconnected = False
        return

    should_notify = (
        notification_mode == "Turn on notification"
        or (notification_mode == "Show only once" and not _notified_disconnected)
    )
    if should_notify:
        description = (
            f"Please reconnect or <a href='{VPN_HELP_URL}'>setup VPN</a>.<br>"
            "Change notification settings in the context menu."
        )
        ui.show_info("VPN is DISCONNECTED ❌", description=description, duration=20000)
        _notified_disconnected = True

    if not _logged_disconnected:
        print("[VPN Checker] Status changed: VPN is DISCONNECTED")
        _logged_disconnected = True

    _was_connected = False


def on_timeout(ctx: ap.Context):
    """Called once a minute by Anchorpoint. Runs the reachability check whenever
    the configured interval has elapsed."""
    global _last_check_t

    try:
        interval = float(apsync.Settings(SETTINGS_NAME).get("interval", DEFAULT_INTERVAL_SECS))
    except (TypeError, ValueError):
        interval = DEFAULT_INTERVAL_SECS
    interval = max(MIN_INTERVAL_SECS, interval)

    now = time.monotonic()
    if _last_check_t and (now - _last_check_t) < interval:
        return
    _last_check_t = now

    ctx.run_async(check_vpn)
