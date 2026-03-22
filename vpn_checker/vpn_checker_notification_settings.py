import anchorpoint as ap
import apsync

ctx = ap.get_context()
ui = ap.UI()

local_settings = apsync.Settings("vpn_checker_local")

NOTIFICATION_OPTIONS = ["Turn on notification", "Show only once", "Turn off notification"]

def store(dialog):
    notification_mode = dialog.get_value("notification_mode")
    local_settings.set("notification_mode", notification_mode)
    local_settings.store()
    ui.show_success("Settings saved")
    dialog.close()

def show_settings():
    notification_mode = local_settings.get("notification_mode", NOTIFICATION_OPTIONS[0])

    dialog = ap.Dialog()
    dialog.title = "VPN Checker Notifications"
    dialog.icon = ctx.icon

    dialog.add_text("Notifications\t").add_dropdown(notification_mode, NOTIFICATION_OPTIONS, var="notification_mode")

    dialog.add_button("Save", callback=store)

    dialog.show()

show_settings()
