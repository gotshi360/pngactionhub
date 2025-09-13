import anchorpoint as ap
import apsync as aps

ui = ap.UI()
settings = aps.Settings("custom_dialog")


def store_settings(dialog: ap.Dialog):
    settings.set("title", dialog.get_value("title_var"))
    settings.set("message", dialog.get_value("msg_var"))
    settings.set("auto_start", dialog.get_value("auto_var"))
    settings.set("icon", dialog.get_value("icon_var"))
    settings.store()
    ui.show_success("Custom Dialog settings saved")
    dialog.close()


def open_settings():
    dialog = ap.Dialog()
    dialog.title = "Custom Dialog Settings"

    title = settings.get("title", "Default Title")
    message = settings.get("message", "Hello from Anchorpoint!")
    auto_start = settings.get("auto_start", False)
    icon = settings.get("icon", "info")

    icon_options = ["info", "star", "check", "warning", "error"]

    dialog.add_text("Dialog Title	").add_input(title, var="title_var")
    dialog.add_text("Dialog Message	").add_input(message, var="msg_var")
    dialog.add_checkbox("Show on Startup", var="auto_var", checked=auto_start)
    dialog.add_text("Sidebar Icon	").add_dropdown(icon, icon_options, var="icon_var")

    dialog.add_button("Save", callback=store_settings)
    dialog.show()


open_settings()
