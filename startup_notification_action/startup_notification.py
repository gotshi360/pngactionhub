import anchorpoint as ap
import apsync
import datetime

SETTINGS_KEYS = {
    "enabled": "startup_enabled",
    "title": "startup_title",
    "message": "startup_message",
    "type": "startup_type",
    "duration": "startup_duration",
    "skip_today": "startup_skip_today",
    "last_shown_date": "startup_last_shown"
}

DEFAULTS = {
    SETTINGS_KEYS["enabled"]: True,
    SETTINGS_KEYS["title"]: "Welcome",
    SETTINGS_KEYS["message"]: "Have a great session 👋",
    SETTINGS_KEYS["type"]: "info",
    SETTINGS_KEYS["duration"]: 4000,
    SETTINGS_KEYS["skip_today"]: False,
    SETTINGS_KEYS["last_shown_date"]: ""
}


def get_settings() -> dict:
    print("[StartupNotification] Loading settings...")
    s = apsync.Settings()
    values = {}
    for k, default in DEFAULTS.items():
        try:
            v = s.get(k)
            values[k] = v if v is not None else default
        except:
            values[k] = default

    values[SETTINGS_KEYS["enabled"]] = bool(values[SETTINGS_KEYS["enabled"]])
    values[SETTINGS_KEYS["skip_today"]] = bool(values[SETTINGS_KEYS["skip_today"]])
    try:
        values[SETTINGS_KEYS["duration"]] = int(values[SETTINGS_KEYS["duration"]])
    except:
        values[SETTINGS_KEYS["duration"]] = DEFAULTS[SETTINGS_KEYS["duration"]]

    return values


def show_notification(title, message, ntype="info", duration=4000):
    ui = ap.UI()
    if ntype == "success":
        ui.show_success(title, message, duration=duration)
    elif ntype == "error":
        ui.show_error(title, message, duration=duration)
    else:
        ui.show_info(title, message, duration=duration)


def on_application_started(ctx: ap.Context):
    cfg = get_settings()
    if not cfg[SETTINGS_KEYS["enabled"]]:
        return

    today = datetime.date.today().isoformat()
    if cfg[SETTINGS_KEYS["skip_today"]]:
        if cfg[SETTINGS_KEYS["last_shown_date"]] == today:
            print("[StartupNotification] Already shown today, skipping.")
            return

    show_notification(cfg[SETTINGS_KEYS["title"]],
                      cfg[SETTINGS_KEYS["message"]],
                      cfg[SETTINGS_KEYS["type"]],
                      cfg[SETTINGS_KEYS["duration"]])

    if cfg[SETTINGS_KEYS["skip_today"]]:
        s = apsync.Settings()
        s.set(SETTINGS_KEYS["last_shown_date"], today)
        s.store()


def main():
    cfg = get_settings()
    show_notification(cfg[SETTINGS_KEYS["title"]],
                      cfg[SETTINGS_KEYS["message"]],
                      cfg[SETTINGS_KEYS["type"]],
                      cfg[SETTINGS_KEYS["duration"]])


if __name__ == "__main__":
    main()
