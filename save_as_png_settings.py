import anchorpoint as ap
import apsync as aps

settings = aps.Settings()
ui = ap.UI()

def save_settings(dialog: ap.Dialog):
    settings.set("save_to_subfolder", dialog.get_value("save_to_subfolder"))
    settings.store()
    dialog.close()
    ui.show_success("Settings saved")

dialog = ap.Dialog()
dialog.title = "Save as PNG Settings"
dialog.add_text("Save to subfolder '_png'").add_checkbox(default=settings.get("save_to_subfolder", False), var="save_to_subfolder")
dialog.add_button("Save", callback=save_settings)
dialog.show()
