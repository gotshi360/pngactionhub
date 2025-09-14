import anchorpoint as ap
import apsync as aps

ui = ap.UI()
settings = aps.Settings("maintenance_notice")


def store_settings(dialog: ap.Dialog):
    settings.set("enabled", dialog.get_value("enabled_var"))
    settings.set("auto_start", dialog.get_value("auto_var"))
    settings.store()
    ui.show_success("Settings saved")
    dialog.close()


def open_settings():
    enabled = settings.get("enabled", True)
    auto_start = settings.get("auto_start", False)

    dialog = ap.Dialog()
    dialog.title = "Maintenance Notice Settings"
    dialog.add_checkbox(default=enabled, var="enabled_var", text="Enable Maintenance Notice")
    dialog.add_checkbox(default=auto_start, var="auto_var", text="Show on Startup")

    dialog.add_button("Save", callback=store_settings)
    dialog.show()


open_settings()
