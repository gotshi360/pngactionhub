import anchorpoint as ap
import apsync as aps

ctx = ap.get_context()
ui = ap.UI()
settings = aps.Settings()

def store_settings(dialog: ap.Dialog):
    settings.set("show_dimensions", dialog.get_value("show_dimensions"))
    settings.set("show_video_dimensions", dialog.get_value("show_video_dimensions"))
    settings.set("show_frame_rate", dialog.get_value("show_frame_rate"))
    settings.set("show_bitrate", dialog.get_value("show_bitrate"))
    settings.set("show_duration", dialog.get_value("show_duration"))
    settings.store()
    dialog.close()
    ui.show_success("Settings saved")

dialog = ap.Dialog()
dialog.title = "Get Image Info Settings"

dialog.add_info("🖼️ Image Attributes")
dialog.add_text("Show Dimensions").add_checkbox(default=settings.get("show_dimensions", True), var="show_dimensions")

dialog.add_info("🎬 Video Attributes")
dialog.add_text("Show Dimensions").add_checkbox(default=settings.get("show_video_dimensions", True), var="show_video_dimensions")
dialog.add_text("Show Frame Rate").add_checkbox(default=settings.get("show_frame_rate", True), var="show_frame_rate")
dialog.add_text("Show Bitrate").add_checkbox(default=settings.get("show_bitrate", True), var="show_bitrate")
dialog.add_text("Show Duration").add_checkbox(default=settings.get("show_duration", True), var="show_duration")

dialog.add_button("Save", callback=store_settings)

dialog.show()
