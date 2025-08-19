import anchorpoint as ap
import apsync

SETTINGS_KEYS = {
    "enabled": "startup_enabled",
    "title": "startup_title",
    "message": "startup_message",
    "type": "startup_type",
    "duration": "startup_duration",
    "skip_today": "startup_skip_today"
}

DEFAULTS = {
    SETTINGS_KEYS["enabled"]: True,
    SETTINGS_KEYS["title"]: "Welcome",
    SETTINGS_KEYS["message"]: "Have a great session 👋",
    SETTINGS_KEYS["type"]: "info",
    SETTINGS_KEYS["duration"]: 4000,
    SETTINGS_KEYS["skip_today"]: False
}

TYPE_OPTIONS = ["info", "success", "error"]


def open_dialog():
    ui = ap.UI()
    s = apsync.Settings()

    enabled = bool(s.get(SETTINGS_KEYS["enabled"]) or DEFAULTS[SETTINGS_KEYS["enabled"]])
    title = s.get(SETTINGS_KEYS["title"]) or DEFAULTS[SETTINGS_KEYS["title"]]
    message = s.get(SETTINGS_KEYS["message"]) or DEFAULTS[SETTINGS_KEYS["message"]]
    ntype = s.get(SETTINGS_KEYS["type"]) or DEFAULTS[SETTINGS_KEYS["type"]]
    duration = str(s.get(SETTINGS_KEYS["duration"]) or DEFAULTS[SETTINGS_KEYS["duration"]])
    skip_today = bool(s.get(SETTINGS_KEYS["skip_today"]) or DEFAULTS[SETTINGS_KEYS["skip_today"]])

    def on_save(dialog: ap.Dialog):
        s.set(SETTINGS_KEYS["enabled"], bool(dialog.get_value("enabled")))
        s.set(SETTINGS_KEYS["title"], dialog.get_value("title"))
        s.set(SETTINGS_KEYS["message"], dialog.get_value("message"))
        s.set(SETTINGS_KEYS["type"], dialog.get_value("type"))
        s.set(SETTINGS_KEYS["duration"], int(dialog.get_value("duration")))
        s.set(SETTINGS_KEYS["skip_today"], bool(dialog.get_value("skip_today")))
        s.store()
        ui.show_success("Startup Notification", "Settings saved.")

    dialog = ap.Dialog()
    dialog.title = "Startup Notification Settings"

    dialog.add_switch(enabled, text="Enable on startup", var="enabled")
    dialog.add_separator()

    dialog.add_text("Title\t").add_input(default=title, var="title", width=300)
    dialog.add_text("Message\t").add_input(default=message, var="message", width=300)
    dialog.add_text("Type\t").add_dropdown(ntype, TYPE_OPTIONS, var="type")
    dialog.add_text("Duration (ms)\t").add_input(default=duration, var="duration", width=120)

    dialog.add_checkbox(skip_today, text="Don't show again today", var="skip_today")

    dialog.add_button("Save", callback=on_save)
    dialog.add_button("Close", callback=lambda d: None, primary=False)

    dialog.show()


if __name__ == "__main__":
    open_dialog()
