import anchorpoint as ap
import apsync as aps

ctx = ap.get_context()
ui = ap.UI()


def show_dialog():
    settings = aps.Settings("maintenance_notice")
    if not settings.get("enabled", True):
        return  # ha nincs engedélyezve, semmit se csináljon

    dialog = ap.Dialog()
    dialog.title = "Maintenance Notice"
    if ctx.icon:
        dialog.icon = ctx.icon
    dialog.add_text("GITEA is currently unavailable due to ongoing maintenance, which temporarily disables file access via Anchorpoint.")
    dialog.add_text("Please refrain from syncing in Anchorpoint until the maintenance is complete.")
    dialog.add_info("You may continue working on your local files, but avoid pushing any changes to the server during this period.")
    dialog.add_text(" ")
    dialog.add_text("Thank you for your patience.")
    dialog.add_info("Play'n GO Anchorpoint Support")
    dialog.show()


def on_application_started(ctx: ap.Context):
    settings = aps.Settings("maintenance_notice")
    if settings.get("enabled", True) and settings.get("auto_start", False):
        show_dialog()


def on_project_opened(ctx: ap.Context):
    settings = aps.Settings("maintenance_notice")
    if settings.get("enabled", True) and settings.get("auto_start", False):
        show_dialog()


# Always show when triggered manually (but only if enabled)
show_dialog()
