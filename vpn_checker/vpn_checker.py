import anchorpoint as ap
import apsync
import time
import requests

SETTINGS_NAME = "vpn_checker"
LOCAL_SETTINGS_NAME = "vpn_checker_local"
STATE_SETTINGS_NAME = "vpn_checker_state"

# on_timeout fires once a minute, which is the finest granularity available.
MIN_INTERVAL_SECS = 60.0
DEFAULT_INTERVAL_SECS = 60
DEFAULT_URL = "https://gitea.playngo.com"

VPN_HELP_URL = (
    "https://playngo.sharepoint.com/:b:/s/OnePlaynGO/"
    "EWoYO4KXq3dCjgAVR3wqu7MBXBiQK_vN6bR6T5c7B-CPCg?e=ESxako"
)


# ── Persisted state ───────────────────────────────────────────────────────────
#
# Module level globals do not survive between on_timeout calls — Anchorpoint
# reloads the script, so the state reset on every tick and the "connected"
# toast fired every minute instead of only on recovery. State therefore lives
# in local Settings, which also means a restart while the VPN is up stays
# silent instead of announcing a connection that never dropped.

def _read_state():
    """Returns (was_disconnected, notified_disconnected, last_check)."""
    s = apsync.Settings(STATE_SETTINGS_NAME)
    try:
        last_check = float(s.get("last_check", 0.0) or 0.0)
    except (TypeError, ValueError):
        last_check = 0.0
    return (
        bool(s.get("was_disconnected", False)),
        bool(s.get("notified_disconnected", False)),
        last_check,
    )


def _write_state(was_disconnected, notified_disconnected, last_check):
    s = apsync.Settings(STATE_SETTINGS_NAME)
    s.set("was_disconnected", bool(was_disconnected))
    s.set("notified_disconnected", bool(notified_disconnected))
    s.set("last_check", float(last_check))
    s.store()


def is_vpn_connected(test_url):
    try:
        response = requests.get(test_url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_vpn(was_disconnected, notified_disconnected, checked_at):
    """Runs on a worker thread via ctx.run_async so the blocking request never
    stalls the UI.

    Notifications only fire on a state change: while the VPN is up the checker
    stays silent, an outage is reported according to the notification mode, and
    the recovery is confirmed once — only if an outage was actually seen.
    """
    test_url = (apsync.Settings(SETTINGS_NAME).get("vpn_url", DEFAULT_URL) or DEFAULT_URL).strip()
    notification_mode = apsync.Settings(LOCAL_SETTINGS_NAME).get(
        "notification_mode", "Turn on notification"
    )

    ui = ap.UI()
    connected = is_vpn_connected(test_url)

    if connected:
        if was_disconnected:
            print("[VPN Checker] Status changed: VPN is CONNECTED")
            if notification_mode != "Turn off notification":
                ui.show_info("VPN is CONNECTED ✅", duration=10000)
        _write_state(False, False, checked_at)
        return

    should_notify = (
        notification_mode == "Turn on notification"
        or (notification_mode == "Show only once" and not notified_disconnected)
    )
    if should_notify:
        description = (
            f"Please reconnect or <a href='{VPN_HELP_URL}'>setup VPN</a>.<br>"
            "Change notification settings in the context menu."
        )
        ui.show_info("VPN is DISCONNECTED ❌", description=description, duration=20000)
        notified_disconnected = True

    if not was_disconnected:
        print("[VPN Checker] Status changed: VPN is DISCONNECTED")

    _write_state(True, notified_disconnected, checked_at)


def on_timeout(ctx: ap.Context):
    """Called once a minute by Anchorpoint. Runs the reachability check whenever
    the configured interval has elapsed."""
    was_disconnected, notified_disconnected, last_check = _read_state()

    try:
        interval = float(apsync.Settings(SETTINGS_NAME).get("interval", DEFAULT_INTERVAL_SECS))
    except (TypeError, ValueError):
        interval = DEFAULT_INTERVAL_SECS
    interval = max(MIN_INTERVAL_SECS, interval)

    now = time.time()
    # A negative delta means the system clock moved backwards — treat as due
    # rather than blocking every check until the clock catches up.
    if last_check and 0 <= (now - last_check) < interval:
        return

    ctx.run_async(check_vpn, was_disconnected, notified_disconnected, now)
