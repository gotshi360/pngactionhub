import anchorpoint as ap
import apsync as aps

ctx = ap.get_context()
ui = ap.UI()
settings = aps.Settings()

def store_settings(dialog: ap.Dialog):
    settings.set("show_dimensions", dialog.get_value("show_dimensions"))
    settings.set("show_resolution", dialog.get_value("show_resolution"))
    settings.set("show_bit_depth", dialog.get_value("show_bit_depth"))
    settings.store()
    dialog.close()
    ui.show_success("Settings saved")

dialog = ap.Dialog()
dialog.title = "Get Image Info Settings"

dialog.add_text("Show Dimensions").add_checkbox(default=settings.get("show_dimensions", True), var="show_dimensions")
dialog.add_text("Show Resolution").add_checkbox(default=settings.get("show_resolution", True), var="show_resolution")
dialog.add_text("Show Bit Depth").add_checkbox(default=settings.get("show_bit_depth", True), var="show_bit_depth")

dialog.add_button("Save", callback=store_settings)

dialog.show()
