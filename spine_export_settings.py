import anchorpoint as ap
import apsync as aps
import platform

ctx = ap.get_context()
ui = ap.UI()
settings = aps.Settings("spine_export")

def store_settings(dialog: ap.Dialog):
    settings.set("spine_path_win", dialog.get_value("spine_path_win"))
    settings.set("spine_path_mac", dialog.get_value("spine_path_mac"))
    settings.store()
    ui.show_success("Spine path saved")
    dialog.close()

default_win = settings.get("spine_path_win", "C:/Program Files/Spine/Spine.com")
default_mac = settings.get("spine_path_mac", "/Applications/Spine.app/Contents/MacOS/Spine")

dialog = ap.Dialog()
dialog.icon = ctx.icon
dialog.title = "Spine Export Settings"
dialog.add_info("Spine CLI executable path")

dialog.add_text("Windows path").add_input(default_win, browse=ap.BrowseType.File, var="spine_path_win")
dialog.add_text("macOS path").add_input(default_mac, browse=ap.BrowseType.File, var="spine_path_mac")

dialog.add_button("Save", callback=store_settings)
dialog.show()