# CHAT GPT PROMPT:
# Ez a settings script egy dialogot jelenít meg, ahol a user kiválaszthatja, mely kép metaadatokat szeretné beállítani attribútumként.

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

dialog.add_checkbox("Show Dimensions", var="show_dimensions", checked=settings.get("show_dimensions", True))
dialog.add_checkbox("Show Resolution", var="show_resolution", checked=settings.get("show_resolution", True))
dialog.add_checkbox("Show Bit Depth", var="show_bit_depth", checked=settings.get("show_bit_depth", True))

dialog.add_button("Save", callback=store_settings)

dialog.show()
