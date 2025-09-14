import anchorpoint as ap
import apsync as aps

ui = ap.UI()
settings = aps.Settings("maintenance_notice")


def store_settings(dialog: ap.Dialog):
    settings.set("auto_start", dialog.get_value("auto_var"))
    settings.store()
    ui.show_success("Settings saved")
    dialog.close()


def open_settings():
    auto_start = settings.get("auto_start", False)

    dialog = ap.Dialog()
    dialog.title = "Maintenance Notice Settings"
    dialog.add_checkbox(default=auto_start, var="auto_var", text="Show on Startup")

    dialog.add_button("Save", callback=store_settings)
    dialog.show()


open_settings()
