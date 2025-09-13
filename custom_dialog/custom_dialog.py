import anchorpoint as ap
import apsync as aps

ctx = ap.get_context()
ui = ap.UI()


def show_custom_dialog():
    settings = aps.Settings("custom_dialog")

    title = settings.get("title", "Default Title")
    message = settings.get("message", "Hello from Anchorpoint!")

    dialog = ap.Dialog()
    dialog.title = title
    if ctx.icon:
        dialog.icon = ctx.icon
    dialog.add_info(message)
    dialog.add_button("OK", callback=lambda d: d.close())
    dialog.show()


def on_application_started(ctx: ap.Context):
    """Automatically show dialog if auto_start is enabled in settings"""
    settings = aps.Settings("custom_dialog")
    if settings.get("auto_start", False):
        show_custom_dialog()


# Always show dialog when action is triggered manually
show_custom_dialog()
