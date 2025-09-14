import anchorpoint as ap
import apsync as aps


class CustomDialogSettings(ap.AnchorpointSettings):
    def __init__(self):
        super().__init__()
        self.name = "Custom Dialog"
        self.icon = "star"
        self.priority = 10

    def get_dialog(self) -> ap.Dialog:
        settings = aps.Settings("custom_dialog")

        title = settings.get("title", "Default Title")
        message = settings.get("message", "Hello from Anchorpoint!")
        auto_start = settings.get("auto_start", False)
        icon = settings.get("icon", "info")

        icon_options = ["info", "star", "check", "warning", "error"]

        dialog = ap.Dialog()
        dialog.title = "Custom Dialog Settings"
        dialog.add_text("Dialog Title\t").add_input(title, var="title_var")
        dialog.add_text("Dialog Message\t").add_input(message, var="msg_var")
        dialog.add_checkbox("Show on Startup", var="auto_var", checked=auto_start)
        dialog.add_text("Sidebar Icon\t").add_dropdown(icon, icon_options, var="icon_var")

        def store_settings(d: ap.Dialog):
            settings.set("title", d.get_value("title_var"))
            settings.set("message", d.get_value("msg_var"))
            settings.set("auto_start", d.get_value("auto_var"))
            settings.set("icon", d.get_value("icon_var"))
            settings.store()
            ap.UI().show_success("Custom Dialog settings saved")
            d.close()

        dialog.add_button("Save", callback=store_settings)
        return dialog
